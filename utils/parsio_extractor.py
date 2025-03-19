import os
import requests
import time
import json
import logging
import re
from dotenv import load_dotenv
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/parsio_extractor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# טעינת משתני סביבה
load_dotenv()
PARSIO_API_KEY = os.getenv("PARSIO_API_KEY")
logger.debug(f"PARSIO_API_KEY exists: {bool(PARSIO_API_KEY)}")

class ParsioExtractor:
    """
    מחלץ תוכן מקבצי PDF באמצעות Parsio.io API.
    """
    
    def __init__(self):
        """Initialize the ParsioExtractor with API key."""
        self.api_key = PARSIO_API_KEY
        if not self.api_key:
            raise ValueError("PARSIO_API_KEY environment variable is not set")
        logger.debug(f"PARSIO_API_KEY exists: {bool(self.api_key)}")
        self.base_url = "https://api.parsio.io/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

    def upload_and_extract(self, file_path):
        """
        Upload a PDF file to Parsio and extract its content.
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            dict: Extracted content
        """
        try:
            logger.info(f"Starting extraction from {file_path} with Parsio")
            
            # 1. Upload the file
            upload_url = f"{self.base_url}/documents/upload"
            
            with open(file_path, "rb") as file:
                files = {"file": (os.path.basename(file_path), file, "application/pdf")}
                response = requests.post(upload_url, headers=self.headers, files=files)
            
            if response.status_code != 200:
                logger.error(f"Error uploading file: {response.text}")
                raise Exception(f"Failed to upload file: {response.status_code} - {response.text}")
            
            document_id = response.json().get("documentId")
            logger.info(f"File uploaded successfully. Document ID: {document_id}")
            
            # 2. Wait for processing to complete
            status_url = f"{self.base_url}/documents/{document_id}"
            max_attempts = 30
            attempts = 0
            
            while attempts < max_attempts:
                attempts += 1
                status_response = requests.get(status_url, headers=self.headers)
                
                if status_response.status_code != 200:
                    logger.error(f"Error checking status: {status_response.text}")
                    raise Exception(f"Failed to check status: {status_response.status_code} - {status_response.text}")
                
                status_data = status_response.json()
                processing_status = status_data.get("status")
                
                logger.info(f"Processing status: {processing_status} (Attempt {attempts}/{max_attempts})")
                
                if processing_status == "processed":
                    break
                
                if processing_status == "failed":
                    logger.error(f"Processing failed: {status_data.get('message')}")
                    raise Exception(f"Processing failed: {status_data.get('message')}")
                
                # Wait before checking again
                time.sleep(5)
            
            if attempts >= max_attempts:
                logger.error("Timeout waiting for processing to complete")
                raise Exception("Timeout waiting for processing to complete")
            
            # 3. Get the extracted data
            data_url = f"{self.base_url}/documents/{document_id}/data"
            data_response = requests.get(data_url, headers=self.headers)
            
            if data_response.status_code != 200:
                logger.error(f"Error getting extracted data: {data_response.text}")
                raise Exception(f"Failed to get extracted data: {data_response.status_code} - {data_response.text}")
            
            extracted_data = data_response.json()
            logger.info(f"Successfully extracted data from {file_path}")
            
            return self._process_extracted_data(extracted_data, file_path)
            
        except Exception as e:
            logger.error(f"Error in extract_content: {str(e)}", exc_info=True)
            raise
    
    def _process_extracted_data(self, extracted_data, file_path):
        """
        Process the extracted data into a standardized format.
        
        Args:
            extracted_data (dict): The raw data extracted by Parsio
            file_path (str): Path to the original file
            
        Returns:
            dict: Processed extracted content
        """
        try:
            # Initialize result structure
            result = {
                "metadata": {
                    "filename": os.path.basename(file_path),
                    "processed_date": datetime.now().isoformat(),
                    "processor": "parsio"
                },
                "text": "",
                "tables": [],
                "financial_data": {
                    "holdings": [],
                    "transactions": [],
                    "summary": {
                        "total_value": 0,
                        "total_holdings": 0
                    }
                }
            }
            
            # Process pages and extract text
            if "pages" in extracted_data:
                for page_data in extracted_data["pages"]:
                    if "text" in page_data:
                        result["text"] += page_data["text"] + "\n\n"
                    
                    # Extract tables if available
                    if "tables" in page_data and page_data["tables"]:
                        for table in page_data["tables"]:
                            processed_table = {
                                "headers": table.get("headers", []),
                                "data": table.get("rows", []),
                                "type": "general"
                            }
                            
                            # Check if this looks like a holdings table
                            if self._is_holdings_table(processed_table):
                                processed_table["type"] = "holdings"
                                holdings = self._extract_holdings_from_table(processed_table)
                                processed_table["holdings"] = holdings
                                result["financial_data"]["holdings"].extend(holdings)
                            
                            result["tables"].append(processed_table)
            
            # If no tables were found directly, try to extract holdings from text
            if not result["financial_data"]["holdings"]:
                text_holdings = self._extract_holdings_from_text(result["text"])
                result["financial_data"]["holdings"].extend(text_holdings)
            
            # Update summary
            result["financial_data"]["summary"]["total_holdings"] = len(result["financial_data"]["holdings"])
            
            # Try to extract a total value if available
            for holding in result["financial_data"]["holdings"]:
                if holding.get("value") is not None:
                    result["financial_data"]["summary"]["total_value"] += holding["value"]
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing extracted data: {str(e)}", exc_info=True)
            return {
                "metadata": {
                    "filename": os.path.basename(file_path),
                    "processed_date": datetime.now().isoformat(),
                    "processor": "parsio",
                    "error": str(e)
                },
                "text": "",
                "tables": [],
                "financial_data": {
                    "holdings": [],
                    "transactions": [],
                    "summary": {
                        "total_value": 0,
                        "total_holdings": 0
                    }
                }
            }
    
    def _is_holdings_table(self, table):
        """
        Check if a table appears to be a holdings table.
        
        Args:
            table (dict): Table data
            
        Returns:
            bool: True if it looks like a holdings table
        """
        # Keywords that might indicate a holdings table
        holdings_keywords = [
            "isin", "security", "name", "quantity", "price", "value", "currency",
            "נייר", "ני\"ע", "כמות", "שער", "שווי", "מטבע"
        ]
        
        # Check headers
        if "headers" in table and table["headers"]:
            headers_text = " ".join([h.lower() for h in table["headers"]])
            for keyword in holdings_keywords:
                if keyword.lower() in headers_text:
                    return True
        
        # Check first row of data
        if "data" in table and table["data"] and len(table["data"]) > 0:
            first_row = " ".join([str(cell).lower() for cell in table["data"][0]])
            # Look for ISIN pattern
            if any(cell and isinstance(cell, str) and len(cell) == 12 and cell[:2].isalpha() and cell[2:].isalnum() 
                  for cell in table["data"][0]):
                return True
        
        return False
    
    def _extract_holdings_from_table(self, table):
        """
        Extract holdings from a table.
        
        Args:
            table (dict): Table data
            
        Returns:
            list: Extracted holdings
        """
        holdings = []
        
        if not table.get("data"):
            return holdings
        
        # Try to identify column meanings
        headers = table.get("headers", [])
        isin_col = -1
        name_col = -1
        quantity_col = -1
        price_col = -1
        value_col = -1
        currency_col = -1
        
        # Map columns based on headers
        for i, header in enumerate(headers):
            header_lower = header.lower() if isinstance(header, str) else ""
            if "isin" in header_lower:
                isin_col = i
            elif any(keyword in header_lower for keyword in ["name", "security", "שם", "נייר", "ני\"ע"]):
                name_col = i
            elif any(keyword in header_lower for keyword in ["quantity", "amount", "כמות", "יחידות"]):
                quantity_col = i
            elif any(keyword in header_lower for keyword in ["price", "מחיר", "שער"]):
                price_col = i
            elif any(keyword in header_lower for keyword in ["value", "שווי"]):
                value_col = i
            elif any(keyword in header_lower for keyword in ["currency", "מטבע"]):
                currency_col = i
        
        # If column meanings couldn't be determined from headers, try to infer from data
        if isin_col == -1 and name_col == -1:
            # Look at first row to infer columns
            for i, cell in enumerate(table["data"][0]):
                if cell and isinstance(cell, str):
                    # Check for ISIN pattern (2 letters followed by 10 alphanumeric characters)
                    if len(cell) == 12 and cell[:2].isalpha() and cell[2:].isalnum():
                        isin_col = i
                    # If it's a longer text, it might be a name
                    elif len(cell) > 5 and not cell.replace('.', '').isdigit():
                        name_col = i
                # Look for numeric columns for price, quantity, value
                elif isinstance(cell, (int, float)) or (isinstance(cell, str) and cell.replace('.', '').replace(',', '').isdigit()):
                    if price_col == -1:
                        price_col = i
                    elif quantity_col == -1:
                        quantity_col = i
                    elif value_col == -1:
                        value_col = i
        
        # Process each row
        for row in table["data"]:
            if len(row) < max(isin_col, name_col, quantity_col, price_col, value_col, currency_col) + 1:
                continue  # Skip rows that don't have enough columns
            
            # Extract values
            isin = row[isin_col] if isin_col >= 0 else None
            name = row[name_col] if name_col >= 0 else None
            quantity = self._parse_number(row[quantity_col]) if quantity_col >= 0 else None
            price = self._parse_number(row[price_col]) if price_col >= 0 else None
            value = self._parse_number(row[value_col]) if value_col >= 0 else None
            currency = row[currency_col] if currency_col >= 0 else self._detect_currency_in_row(row)
            
            # If we have at least an ISIN or a name, create a holding
            if isin or name:
                holding = {
                    "isin": isin,
                    "name": name,
                    "quantity": quantity,
                    "price": price,
                    "value": value,
                    "currency": currency
                }
                holdings.append(holding)
        
        return holdings
    
    def _extract_holdings_from_text(self, text):
        """
        Extract holdings from text using pattern matching.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            list: Extracted holdings
        """
        holdings = []
        
        # Look for ISIN patterns
        isin_pattern = r'([A-Z]{2}[A-Z0-9]{9}\d)'
        isin_matches = set(match for match in re.findall(isin_pattern, text))
        
        for isin in isin_matches:
            # Find context around this ISIN
            context_start = max(0, text.find(isin) - 300)
            context_end = min(len(text), text.find(isin) + 300)
            context = text[context_start:context_end]
            
            # Try to extract information
            name = self._extract_security_name(context)
            quantity = self._extract_quantity(context)
            price = self._extract_price(context)
            value = self._extract_value(context)
            currency = self._extract_currency(context)
            
            holdings.append({
                "isin": isin,
                "name": name or "Unknown Security",
                "quantity": quantity,
                "price": price,
                "value": value,
                "currency": currency
            })
        
        return holdings
    
    def _parse_number(self, value):
        """Parse a number from various formats."""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove non-numeric characters except for decimal point and minus sign
            clean_value = re.sub(r'[^\d.\-,]', '', value)
            # Replace comma with dot for decimal point if needed
            clean_value = clean_value.replace(',', '.')
            
            try:
                return float(clean_value)
            except ValueError:
                return None
        
        return None
    
    def _detect_currency_in_row(self, row):
        """Detect currency from row values."""
        row_text = ' '.join(str(cell) for cell in row if cell)
        
        currency_patterns = {
            "ILS": r'₪|ש"ח|שקל|NIS',
            "USD": r'\$|דולר|USD',
            "EUR": r'€|אירו|EUR'
        }
        
        for currency, pattern in currency_patterns.items():
            if re.search(pattern, row_text, re.IGNORECASE):
                return currency
        
        return "ILS"  # Default to ILS
    
    def _extract_security_name(self, context):
        """Extract security name from context."""
        patterns = [
            r'שם נייר[:\s]+([^\n]+)',
            r'שם המכשיר[:\s]+([^\n]+)',
            r'שם המנפיק[:\s]+([^\n]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_price(self, context):
        """Extract price from context."""
        patterns = [
            r'מחיר[:\s]+([\d,.]+)',
            r'שער[:\s]+([\d,.]+)',
            r'שווי ליחידה[:\s]+([\d,.]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        return None
    
    def _extract_quantity(self, context):
        """Extract quantity from context."""
        patterns = [
            r'כמות[:\s]+([\d,.]+)',
            r'יתרה[:\s]+([\d,.]+)',
            r'מספר יחידות[:\s]+([\d,.]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        return None
    
    def _extract_value(self, context):
        """Extract value from context."""
        patterns = [
            r'שווי[:\s]+([\d,.]+)',
            r'שווי שוק[:\s]+([\d,.]+)',
            r'שווי כולל[:\s]+([\d,.]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        return None
    
    def _extract_currency(self, context):
        """Extract currency from context."""
        patterns = {
            "ILS": r'₪|ש"ח|שקל|NIS',
            "USD": r'\$|דולר|USD',
            "EUR": r'€|אירו|EUR'
        }
        for currency, pattern in patterns.items():
            if re.search(pattern, context, re.IGNORECASE):
                return currency
        return "ILS"  # Default to ILS
    
    def save_extracted_content(self, content, output_dir="extracted_data"):
        """
        Save extracted content to JSON files.
        
        Args:
            content (dict): Extracted content
            output_dir (str): Directory to save the files
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate timestamp for unique filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Make sure we have a valid filename
            if 'metadata' in content and 'filename' in content['metadata']:
                base_filename = os.path.splitext(content['metadata']['filename'])[0]
            else:
                base_filename = f"document_{timestamp}"
                logger.warning(f"No filename found in content, using generated name: {base_filename}")
            
            # Save full content
            output_file = os.path.join(output_dir, f"{base_filename}_parsio_{timestamp}_full.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved full content to {output_file}")
            
            # Save tables separately
            if "tables" in content and content["tables"]:
                tables_file = os.path.join(output_dir, f"{base_filename}_parsio_{timestamp}_tables.json")
                with open(tables_file, 'w', encoding='utf-8') as f:
                    json.dump(content["tables"], f, ensure_ascii=False, indent=2)
                logger.info(f"Saved tables to {tables_file}")
            
            # Save text separately
            if "text" in content and content["text"]:
                text_file = os.path.join(output_dir, f"{base_filename}_parsio_{timestamp}_text.txt")
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(content["text"])
                logger.info(f"Saved text to {text_file}")
            
            logger.info(f"Saved all extracted content to {output_dir}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error saving extracted content: {str(e)}", exc_info=True)
            raise
    
    def test_pdf_file(self, file_path, output_to_console=True):
        """Test the extraction on an existing PDF file and print results."""
        try:
            logger.info(f"Testing extraction on file with Parsio: {file_path}")
            
            # Extract content using Parsio
            result = self.upload_and_extract(file_path)
            
            # Save the extracted content
            self.save_extracted_content(result)
            
            # Print summary of results
            if output_to_console:
                print(f"\n{'='*50}")
                print(f"PARSIO TEST RESULTS FOR: {os.path.basename(file_path)}")
                print(f"{'='*50}")
                
                print(f"Total text length: {len(result['text'])}")
                print(f"Total tables: {len(result['tables'])}")
                print(f"Total holdings: {len(result['financial_data']['holdings'])}")
                
                # Print some sample holdings if available
                if result['financial_data']['holdings']:
                    print("\nSample holdings:")
                    for i, holding in enumerate(result['financial_data']['holdings'][:5]):
                        print(f"  {i+1}. ISIN: {holding['isin']}, Name: {holding['name']}, Value: {holding['value']}")
                
                # If no holdings were found
                if len(result['financial_data']['holdings']) == 0:
                    print("\nNo holdings found in the document")
                    
                    # Print first 500 chars of text for debugging
                    print("\nFirst 500 chars of extracted text:")
                    print(result['text'][:500])
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing PDF file with Parsio: {str(e)}", exc_info=True)
            if output_to_console:
                print(f"ERROR: {str(e)}")
            raise 