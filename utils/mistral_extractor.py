import os
import base64
import logging
import re
import json
from mistralai import Mistral
from dotenv import load_dotenv
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mistral_extractor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# טעינת משתני סביבה
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
logger.debug(f"MISTRAL_API_KEY exists: {bool(MISTRAL_API_KEY)}")

class MistralExtractor:
    """
    מחלץ תוכן מקבצי PDF באמצעות Mistral OCR API.
    """
    
    def __init__(self):
        """Initialize the MistralExtractor with API key."""
        self.api_key = MISTRAL_API_KEY
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is not set")
        logger.debug(f"MISTRAL_API_KEY exists: {bool(self.api_key)}")
        self.client = Mistral(api_key=self.api_key)

    def process_pdf_file(self, pdf_path):
        """Process a local PDF file and extract text using Mistral OCR."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Processing local PDF: {pdf_path}")
        
        try:
            # Read the PDF file
            logger.debug("Reading PDF file...")
            with open(pdf_path, "rb") as f:
                pdf_content = f.read()
            logger.debug(f"Read {len(pdf_content)} bytes from PDF file")
            
            # Convert to base64
            logger.debug("Converting PDF to base64...")
            pdf_base64 = base64.b64encode(pdf_content).decode("utf-8")
            logger.debug(f"Base64 string length: {len(pdf_base64)}")
            
            # Create a data URL
            pdf_data_url = f"data:application/pdf;base64,{pdf_base64}"
            logger.debug(f"Data URL length: {len(pdf_data_url)}")
            
            # Send request to Mistral API
            logger.debug("Sending request to Mistral API...")
            try:
                response = self.client.ocr.process(
                    model="mistral-ocr-latest",
                    document={
                        "type": "document_url",
                        "document_url": pdf_data_url
                    }
                )
                logger.debug("Successfully received response from Mistral API")
                logger.debug(f"Response type: {type(response)}")
                logger.debug(f"Response content: {response}")
            except Exception as e:
                logger.error(f"Error calling Mistral API: {str(e)}", exc_info=True)
                raise
            
            # Extract text from all pages
            text = ""
            logger.debug("Processing response pages...")
            if hasattr(response, "pages"):
                logger.debug(f"Number of pages: {len(response.pages)}")
                for page in response.pages:
                    logger.debug(f"Processing page: {page}")
                    if hasattr(page, "markdown"):
                        text += page.markdown + "\n"
            else:
                logger.warning("Response has no 'pages' attribute")
                logger.debug(f"Response attributes: {dir(response)}")
            
            logger.debug(f"Extracted text: {text[:500]}...")  # Log first 500 chars
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error processing local PDF: {str(e)}", exc_info=True)
            raise
    
    def extract_financial_data(self, text, filename):
        """
        Extract financial data from the OCR text.
        
        Args:
            text (str): The OCR text to process
            filename (str): The name of the original file
            
        Returns:
            dict: Extracted financial data
        """
        logger.info(f"Extracting financial data from text of length {len(text)}")
        logger.debug(f"First 500 chars of text: {text[:500]}")
        
        try:
            # Initialize data structure
            data = {
                "filename": filename,
                "transactions": [],
                "summary": {
                    "total_income": 0,
                    "total_expenses": 0,
                    "balance": 0,
                    "num_transactions": 0
                },
                "metadata": {
                    "bank_name": self._detect_bank_name(text),
                    "statement_date": self._extract_statement_date(text),
                    "account_number": self._extract_account_number(text),
                    "currency": self._detect_currency(text)
                }
            }
            
            # Try different patterns for transaction extraction
            patterns = [
                # Pattern for standard bank statement format
                r"(\d{2}[-/]\d{2}[-/]\d{4})\s+([^|]+?)\s+([-]?\d+[.,]\d{2})\s+([-]?\d+[.,]\d{2})",
                # Pattern for credit card statement
                r"(\d{2}[-/]\d{2}[-/]\d{4})\s+([^|]+?)\s+([-]?\d+[.,]\d{2})",
                # Pattern for investment portfolio
                r"\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|"
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    try:
                        if len(match.groups()) == 4:  # Standard bank statement
                            date, description, amount, balance = match.groups()
                            amount = float(amount.replace(',', '.'))
                            balance = float(balance.replace(',', '.'))
                        elif len(match.groups()) == 3:  # Credit card statement
                            date, description, amount = match.groups()
                            amount = float(amount.replace(',', '.'))
                            balance = None
                        else:  # Investment portfolio
                            date, description, amount, balance = match.groups()
                            amount = float(amount.replace(',', '.'))
                            balance = float(balance.replace(',', '.'))
                        
                        transaction = {
                            "date": self._normalize_date(date),
                            "description": description.strip(),
                            "amount": amount,
                            "balance": balance
                        }
                        
                        data["transactions"].append(transaction)
                        
                        # Update summary
                        if amount > 0:
                            data["summary"]["total_income"] += amount
                        else:
                            data["summary"]["total_expenses"] += abs(amount)
                            
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Could not parse transaction: {match.group(0)}, error: {str(e)}")
                        continue
            
            # Update final summary
            data["summary"]["num_transactions"] = len(data["transactions"])
            if data["transactions"]:
                data["summary"]["balance"] = data["transactions"][-1]["balance"] if data["transactions"][-1]["balance"] is not None else 0
            
            logger.info(f"Successfully extracted {len(data['transactions'])} transactions")
            return data
            
        except Exception as e:
            logger.error(f"Error extracting financial data: {str(e)}", exc_info=True)
            return {
                "filename": filename,
                "error": str(e),
                "transactions": [],
                "summary": {
                    "total_income": 0,
                    "total_expenses": 0,
                    "balance": 0,
                    "num_transactions": 0
                }
            }
    
    def _detect_bank_name(self, text):
        """Detect bank name from the text."""
        bank_patterns = {
            "Bank Hapoalim": r"Bank Hapoalim|בנק הפועלים",
            "Bank Leumi": r"Bank Leumi|בנק לאומי",
            "Discount Bank": r"Discount Bank|בנק דיסקונט",
            "Mizrahi-Tefahot": r"Mizrahi-Tefahot|מזרחי-טפחות",
            "First International": r"First International|הבינלאומי הראשון"
        }
        
        for bank_name, pattern in bank_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return bank_name
        return "Unknown Bank"
    
    def _extract_statement_date(self, text):
        """Extract statement date from the text."""
        date_patterns = [
            r"(\d{2}[-/]\d{2}[-/]\d{4})",  # DD/MM/YYYY
            r"(\d{4}[-/]\d{2}[-/]\d{2})",  # YYYY/MM/DD
            r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})"  # DD Month YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_account_number(self, text):
        """Extract account number from the text."""
        account_patterns = [
            r"Account No\.?\s*:?\s*(\d+)",
            r"Account Number\s*:?\s*(\d+)",
            r"חשבון\s*:?\s*(\d+)"
        ]
        
        for pattern in account_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _detect_currency(self, text):
        """Detect currency from the text."""
        currency_patterns = {
            "ILS": r"₪|ILS|שקלים",
            "USD": r"\$|USD|דולר",
            "EUR": r"€|EUR|אירו"
        }
        
        for currency, pattern in currency_patterns.items():
            if re.search(pattern, text):
                return currency
        return "ILS"  # Default to ILS
    
    def _normalize_date(self, date_str):
        """Normalize date string to YYYY-MM-DD format."""
        try:
            # Handle DD/MM/YYYY format
            if re.match(r"\d{2}[-/]\d{2}[-/]\d{4}", date_str):
                day, month, year = re.split(r"[-/]", date_str)
                return f"{year}-{month}-{day}"
            # Handle YYYY/MM/DD format
            elif re.match(r"\d{4}[-/]\d{2}[-/]\d{2}", date_str):
                year, month, day = re.split(r"[-/]", date_str)
                return f"{year}-{month}-{day}"
            # Handle DD Month YYYY format
            elif re.match(r"\d{1,2}\s+[A-Za-z]+\s+\d{4}", date_str):
                day, month, year = date_str.split()
                month_map = {
                    "January": "01", "February": "02", "March": "03",
                    "April": "04", "May": "05", "June": "06",
                    "July": "07", "August": "08", "September": "09",
                    "October": "10", "November": "11", "December": "12"
                }
                month_num = month_map.get(month.capitalize(), "01")
                return f"{year}-{month_num}-{day.zfill(2)}"
            return date_str
        except Exception as e:
            logger.warning(f"Could not normalize date: {date_str}, error: {str(e)}")
            return date_str

    def _extract_images(self, ocr_response):
        """Extract images and their associated text from the OCR response."""
        images = []
        try:
            if hasattr(ocr_response, 'pages'):
                for page in ocr_response.pages:
                    if hasattr(page, 'images'):
                        for img in page.images:
                            image_data = {
                                "page_number": getattr(page, 'page_number', 0),
                                "image_data": img.image_data if hasattr(img, 'image_data') else None,
                                "text": "",
                                "tables": []
                            }
                            
                            # Try to extract text from the image
                            if hasattr(img, 'text'):
                                image_data["text"] = img.text
                            elif hasattr(img, 'markdown'):
                                image_data["text"] = img.markdown
                            elif hasattr(img, 'content'):
                                image_data["text"] = img.content
                            
                            # Clean up the extracted text
                            if image_data["text"]:
                                # Remove image references
                                image_data["text"] = re.sub(r'!\[img-\d+\.jpeg\]\(img-\d+\.jpeg\)', '', image_data["text"])
                                # Clean up whitespace
                                image_data["text"] = re.sub(r'\n\s*\n', '\n\n', image_data["text"])
                                # Extract financial data from image text
                                isin_matches = re.finditer(r'([A-Z]{2}[A-Z0-9]{9}\d)', image_data["text"])
                                for match in isin_matches:
                                    isin = match.group(1)
                                    # Look for associated data near the ISIN
                                    context = image_data["text"][max(0, match.start()-200):min(len(image_data["text"]), match.end()+200)]
                                    
                                    # Extract security details
                                    security = {
                                        "isin": isin,
                                        "name": self._extract_security_name(context),
                                        "price": self._extract_price(context),
                                        "quantity": self._extract_quantity(context),
                                        "value": self._extract_value(context),
                                        "currency": self._extract_currency(context)
                                    }
                                    
                                    # Add to financial data
                                    if not hasattr(image_data, "financial_data"):
                                        image_data["financial_data"] = {"holdings": []}
                                    image_data["financial_data"]["holdings"].append(security)
                                
                                logger.info(f"Extracted text from image on page {image_data['page_number']}: {image_data['text'][:100]}...")
                            
                            # Try to extract tables from the image text
                            if image_data["text"]:
                                image_data["tables"] = self._extract_tables(image_data["text"])
                                logger.info(f"Extracted {len(image_data['tables'])} tables from image on page {image_data['page_number']}")
                            
                            images.append(image_data)
            
            return images
            
        except Exception as e:
            logger.error(f"Error extracting images: {str(e)}", exc_info=True)
            return []

    def extract_all_content(self, file_path):
        """Extract all content from a PDF file using Mistral OCR."""
        try:
            logger.info(f"Starting content extraction from {file_path}")
            
            # Upload the PDF file
            with open(file_path, "rb") as pdf_file:
                uploaded_file = self.client.files.upload(
                    file={
                        "file_name": os.path.basename(file_path),
                        "content": pdf_file.read(),
                    },
                    purpose="ocr"
                )
            
            logger.info(f"File uploaded successfully with ID: {uploaded_file.id}")
            
            # Get signed URL for the uploaded file
            signed_url = self.client.files.get_signed_url(file_id=uploaded_file.id)
            logger.info("Got signed URL for file")
            
            # Process the document with OCR
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": signed_url.url,
                }
            )
            
            logger.info("OCR processing completed")
            
            # Extract text and tables from the response
            extracted_text = ""
            financial_data = {
                "holdings": [],
                "transactions": [],
                "summary": {
                    "total_value": 0,
                    "total_holdings": 0
                }
            }
            
            if hasattr(ocr_response, 'pages'):
                for page in ocr_response.pages:
                    # Extract text from different sources
                    page_text = ""
                    if hasattr(page, 'text'):
                        page_text += page.text + "\n"
                    if hasattr(page, 'markdown'):
                        page_text += page.markdown + "\n"
                    if hasattr(page, 'content'):
                        page_text += page.content + "\n"
                    
                    # Extract financial data
                    isin_matches = re.finditer(r'([A-Z]{2}[A-Z0-9]{9}\d)', page_text)
                    for match in isin_matches:
                        isin = match.group(1)
                        # Look for associated data near the ISIN
                        context = page_text[max(0, match.start()-200):min(len(page_text), match.end()+200)]
                        
                        # Extract security details
                        security = {
                            "isin": isin,
                            "name": self._extract_security_name(context),
                            "price": self._extract_price(context),
                            "quantity": self._extract_quantity(context),
                            "value": self._extract_value(context),
                            "currency": self._extract_currency(context)
                        }
                        
                        financial_data["holdings"].append(security)
                    
                    extracted_text += page_text
                    logger.info(f"Extracted text and data from page {getattr(page, 'page_number', 0)}")
            
            # Clean up extracted text
            extracted_text = re.sub(r'!\[img-\d+\.jpeg\]\(img-\d+\.jpeg\)', '', extracted_text)
            extracted_text = re.sub(r'\n\s*\n', '\n\n', extracted_text)
            
            logger.info(f"Total extracted text length: {len(extracted_text)}")
            logger.info(f"Found {len(financial_data['holdings'])} securities")
            
            # Extract tables
            tables = self._extract_tables(extracted_text)
            logger.info(f"Extracted {len(tables)} tables")
            
            # Extract images
            images = self._extract_images(ocr_response) if hasattr(ocr_response, 'pages') else []
            logger.info(f"Extracted {len(images)} images")
            
            # Create result structure
            result = {
                "metadata": {
                    "filename": os.path.basename(file_path),
                    "total_pages": len(ocr_response.pages) if hasattr(ocr_response, 'pages') else 1,
                    "file_size": os.path.getsize(file_path),
                    "processed_date": datetime.now().isoformat()
                },
                "text": extracted_text,
                "tables": tables,
                "images": images,
                "financial_data": financial_data
            }
            
            # Save the extracted content
            self.save_extracted_content(result)
            
            logger.info(f"Extracted {len(tables)} tables and {len(images)} images")
            return result
            
        except Exception as e:
            logger.error(f"Error in extract_all_content: {str(e)}", exc_info=True)
            raise

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

    def _extract_tables(self, text):
        """Extract tables from the text content."""
        tables = []
        try:
            # Split text into sections
            sections = text.split('\n\n')
            
            for section in sections:
                # Look for table-like structures
                if '|' in section and '-' in section:
                    # Split into rows
                    rows = [row.strip() for row in section.split('\n') if row.strip()]
                    
                    # Skip if too few rows
                    if len(rows) < 2:
                        continue
                        
                    # Extract headers
                    headers = [cell.strip() for cell in rows[0].split('|') if cell.strip()]
                    
                    # Skip if no headers
                    if not headers:
                        continue
                    
                    # Extract data rows
                    data_rows = []
                    for row in rows[1:]:
                        cells = [cell.strip() for cell in row.split('|') if cell.strip()]
                        if cells and len(cells) == len(headers):
                            data_rows.append(cells)
                    
                    # Only add if we have data
                    if data_rows:
                        # Try to identify if this is a holdings table
                        is_holdings_table = any(header.lower() in ['isin', 'שם נייר', 'מחיר', 'כמות', 'שווי'] for header in headers)
                        
                        table = {
                            "headers": headers,
                            "data": data_rows,
                            "type": "holdings" if is_holdings_table else "general"
                        }
                        
                        # If this is a holdings table, extract financial data
                        if is_holdings_table:
                            holdings = []
                            isin_index = -1
                            name_index = -1
                            price_index = -1
                            quantity_index = -1
                            value_index = -1
                            
                            # Find column indices
                            for i, header in enumerate(headers):
                                header_lower = header.lower()
                                if 'isin' in header_lower:
                                    isin_index = i
                                elif 'שם' in header_lower or 'נייר' in header_lower:
                                    name_index = i
                                elif 'מחיר' in header_lower or 'שער' in header_lower:
                                    price_index = i
                                elif 'כמות' in header_lower or 'יחידות' in header_lower:
                                    quantity_index = i
                                elif 'שווי' in header_lower:
                                    value_index = i
                            
                            # Extract holdings from each row
                            for row in data_rows:
                                holding = {
                                    "isin": row[isin_index] if isin_index >= 0 and isin_index < len(row) else None,
                                    "name": row[name_index] if name_index >= 0 and name_index < len(row) else None,
                                    "price": self._parse_number(row[price_index]) if price_index >= 0 and price_index < len(row) else None,
                                    "quantity": self._parse_number(row[quantity_index]) if quantity_index >= 0 and quantity_index < len(row) else None,
                                    "value": self._parse_number(row[value_index]) if value_index >= 0 and value_index < len(row) else None,
                                    "currency": self._detect_currency_in_row(row)
                                }
                                holdings.append(holding)
                            
                            table["holdings"] = holdings
                        
                        tables.append(table)
            
            logger.info(f"Extracted {len(tables)} tables from text")
            return tables
            
        except Exception as e:
            logger.error(f"Error extracting tables: {str(e)}", exc_info=True)
            return []

    def _parse_number(self, text):
        """Parse number from text, handling different formats."""
        if not text:
            return None
        try:
            # Remove currency symbols and other non-numeric characters
            clean_text = re.sub(r'[^\d.,\-]', '', text)
            # Replace comma with dot for decimal point
            clean_text = clean_text.replace(',', '.')
            # Convert to float
            return float(clean_text)
        except (ValueError, TypeError):
            return None

    def _detect_currency_in_row(self, row):
        """Detect currency from row values."""
        row_text = ' '.join(str(cell) for cell in row)
        currency_patterns = {
            "ILS": r'₪|ש"ח|שקל|NIS',
            "USD": r'\$|דולר|USD',
            "EUR": r'€|אירו|EUR'
        }
        for currency, pattern in currency_patterns.items():
            if re.search(pattern, row_text, re.IGNORECASE):
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
            output_file = os.path.join(output_dir, f"{base_filename}_{timestamp}_full.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved full content to {output_file}")
            
            # Save tables separately
            if "tables" in content and content["tables"]:
                tables_file = os.path.join(output_dir, f"{base_filename}_{timestamp}_tables.json")
                with open(tables_file, 'w', encoding='utf-8') as f:
                    json.dump(content["tables"], f, ensure_ascii=False, indent=2)
                logger.info(f"Saved tables to {tables_file}")
            
            # Save text separately
            if "text" in content and content["text"]:
                text_file = os.path.join(output_dir, f"{base_filename}_{timestamp}_text.txt")
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(content["text"])
                logger.info(f"Saved text to {text_file}")
            
            # Save images data separately
            if "images" in content and content["images"]:
                images_file = os.path.join(output_dir, f"{base_filename}_{timestamp}_images.json")
                with open(images_file, 'w', encoding='utf-8') as f:
                    json.dump(content["images"], f, ensure_ascii=False, indent=2)
                logger.info(f"Saved images data to {images_file}")
            
            logger.info(f"Saved all extracted content to {output_dir}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error saving extracted content: {str(e)}", exc_info=True)
            raise 