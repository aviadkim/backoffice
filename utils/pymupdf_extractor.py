import os
import re
import json
import logging
import fitz  # PyMuPDF
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pymupdf_extractor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PyMuPDFExtractor:
    """
    מחלץ תוכן מקבצי PDF באמצעות PyMuPDF.
    """
    
    def __init__(self):
        """Initialize the PyMuPDFExtractor."""
        pass

    def extract_content(self, file_path):
        """
        Extract all content from a PDF file using PyMuPDF.
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            dict: Extracted content
        """
        try:
            logger.info(f"Starting content extraction from {file_path} with PyMuPDF")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            # Open the PDF file
            doc = fitz.open(file_path)
            
            # Initialize result structure
            result = {
                "metadata": {
                    "filename": os.path.basename(file_path),
                    "total_pages": len(doc),
                    "file_size": os.path.getsize(file_path),
                    "processed_date": datetime.now().isoformat()
                },
                "text": "",
                "tables": [],
                "images": [],
                "financial_data": {
                    "holdings": [],
                    "transactions": [],
                    "summary": {
                        "total_value": 0,
                        "total_holdings": 0
                    }
                }
            }
            
            # Process each page
            for page_idx, page in enumerate(doc):
                logger.info(f"Processing page {page_idx+1}/{len(doc)}")
                
                # Extract text
                page_text = page.get_text()
                result["text"] += page_text + "\n\n"
                
                # Extract tables (PyMuPDF doesn't have built-in table extraction, 
                # but we can approximate using text blocks)
                blocks = page.get_text("blocks")
                tables = self._extract_tables_from_blocks(blocks)
                if tables:
                    logger.info(f"Found {len(tables)} potential tables on page {page_idx+1}")
                    result["tables"].extend(tables)
                
                # Extract images
                images = self._extract_images_from_page(page, page_idx+1)
                result["images"].extend(images)
                
                # Look for ISIN numbers in the text
                holdings = self._extract_holdings_from_text(page_text)
                for holding in holdings:
                    # Add page number to the holding
                    holding["page"] = page_idx + 1
                    # Check if this holding is already in the list
                    existing_holdings = [h for h in result["financial_data"]["holdings"] if h["isin"] == holding["isin"]]
                    if existing_holdings:
                        # Update existing holding with more information if available
                        existing = existing_holdings[0]
                        if not existing["name"] or existing["name"] == "Unknown Security":
                            existing["name"] = holding["name"]
                        if existing["price"] is None and holding["price"] is not None:
                            existing["price"] = holding["price"]
                        if existing["quantity"] is None and holding["quantity"] is not None:
                            existing["quantity"] = holding["quantity"]
                        if existing["value"] is None and holding["value"] is not None:
                            existing["value"] = holding["value"]
                    else:
                        # Add new holding
                        result["financial_data"]["holdings"].append(holding)
            
            # Close the document
            doc.close()
            
            # Try to extract data from tables
            for table in result["tables"]:
                if self._is_holdings_table(table):
                    table["type"] = "holdings"
                    holdings = self._extract_holdings_from_table(table)
                    table["holdings"] = holdings
                    
                    # Add holdings to the financial data, avoiding duplicates
                    existing_isins = [h["isin"] for h in result["financial_data"]["holdings"] if h["isin"]]
                    for holding in holdings:
                        if holding["isin"] and holding["isin"] in existing_isins:
                            continue
                        result["financial_data"]["holdings"].append(holding)
                        if holding["isin"]:
                            existing_isins.append(holding["isin"])
            
            # Update summary information
            result["financial_data"]["summary"]["total_holdings"] = len(result["financial_data"]["holdings"])
            for holding in result["financial_data"]["holdings"]:
                if holding.get("value") is not None:
                    result["financial_data"]["summary"]["total_value"] += holding["value"]
            
            logger.info(f"Completed extraction from {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error in extract_content: {str(e)}", exc_info=True)
            raise
    
    def _extract_tables_from_blocks(self, blocks):
        """
        Extract potential tables from text blocks.
        
        PyMuPDF doesn't have built-in table detection, so this is an approximation
        that looks for grid-like structures in the text blocks.
        
        Args:
            blocks (list): List of text blocks from PyMuPDF
            
        Returns:
            list: Extracted tables
        """
        tables = []
        try:
            # Group blocks by y-position to find potential rows
            y_positions = {}
            for block in blocks:
                # Each block is (x0, y0, x1, y1, "text", block_no, block_type)
                if block[6] == 0:  # Text blocks
                    y_key = round(block[1], 0)  # Round y0 position to group nearby rows
                    if y_key not in y_positions:
                        y_positions[y_key] = []
                    y_positions[y_key].append(block)
            
            # Sort y-positions (rows) by vertical position
            sorted_y_keys = sorted(y_positions.keys())
            
            # Look for sequences of rows with similar structure (potential tables)
            current_table_rows = []
            current_row_count = 0
            
            for i, y_key in enumerate(sorted_y_keys):
                row_blocks = sorted(y_positions[y_key], key=lambda b: b[0])  # Sort blocks horizontally
                
                # If this row has multiple cells and looks like a potential table row
                if len(row_blocks) >= 3:
                    # If we're starting a new potential table
                    if current_row_count == 0:
                        current_table_rows = [row_blocks]
                        current_row_count = 1
                    else:
                        # Check if this row's structure is similar to the previous rows
                        prev_row = current_table_rows[-1]
                        
                        # Simple heuristic: similar number of cells and similar x-positions
                        if 0.7 <= len(row_blocks) / len(prev_row) <= 1.3:
                            current_table_rows.append(row_blocks)
                            current_row_count += 1
                        else:
                            # Row doesn't match the pattern, check if we have enough rows for a table
                            if current_row_count >= 3:
                                # Process the completed table
                                table = self._process_table_rows(current_table_rows)
                                if table:
                                    tables.append(table)
                            
                            # Start a new potential table with this row
                            current_table_rows = [row_blocks]
                            current_row_count = 1
                else:
                    # Not a potential table row, check if we have a completed table
                    if current_row_count >= 3:
                        table = self._process_table_rows(current_table_rows)
                        if table:
                            tables.append(table)
                    
                    # Reset counters
                    current_table_rows = []
                    current_row_count = 0
            
            # Process any remaining table
            if current_row_count >= 3:
                table = self._process_table_rows(current_table_rows)
                if table:
                    tables.append(table)
            
            return tables
            
        except Exception as e:
            logger.error(f"Error extracting tables from blocks: {str(e)}", exc_info=True)
            return []
    
    def _process_table_rows(self, table_rows):
        """
        Process a set of rows detected as a potential table.
        
        Args:
            table_rows (list): List of rows, each containing text blocks
            
        Returns:
            dict: Processed table
        """
        try:
            # Assume first row is headers
            headers = []
            for block in table_rows[0]:
                headers.append(block[4].strip())
            
            # Process data rows
            data = []
            for row_idx in range(1, len(table_rows)):
                row_data = []
                for block in table_rows[row_idx]:
                    row_data.append(block[4].strip())
                
                if row_data:
                    data.append(row_data)
            
            # Create table structure
            table = {
                "headers": headers,
                "data": data,
                "type": "general"
            }
            
            return table
            
        except Exception as e:
            logger.error(f"Error processing table rows: {str(e)}", exc_info=True)
            return None
    
    def _extract_images_from_page(self, page, page_num):
        """
        Extract images from a PDF page.
        
        Args:
            page (fitz.Page): PyMuPDF page object
            page_num (int): Page number
            
        Returns:
            list: Extracted images
        """
        images = []
        try:
            # Get list of images on the page
            img_list = page.get_images(full=True)
            
            for img_idx, img in enumerate(img_list):
                # img[0] is the xref of the image
                xref = img[0]
                
                try:
                    base_image = page.parent.extract_image(xref)
                    if base_image:
                        # Process each image
                        image_data = {
                            "page_number": page_num,
                            "image_index": img_idx,
                            "width": base_image["width"],
                            "height": base_image["height"],
                            "extension": base_image["ext"],
                            # We don't include the actual image data to keep the result size manageable
                        }
                        
                        images.append(image_data)
                except Exception as img_error:
                    logger.warning(f"Error extracting image {img_idx} from page {page_num}: {str(img_error)}")
            
            return images
            
        except Exception as e:
            logger.error(f"Error extracting images from page {page_num}: {str(e)}", exc_info=True)
            return []
    
    def _extract_holdings_from_text(self, text):
        """
        Extract holdings from text using pattern matching.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            list: Extracted holdings
        """
        holdings = []
        try:
            # Look for ISIN patterns
            isin_pattern = r'([A-Z]{2}[A-Z0-9]{9}\d)'
            isin_matches = re.finditer(isin_pattern, text)
            
            for match in isin_matches:
                isin = match.group(1)
                
                # Get context around the ISIN
                context_start = max(0, match.start() - 500)
                context_end = min(len(text), match.end() + 500)
                context = text[context_start:context_end]
                
                # Extract details
                holding = {
                    "isin": isin,
                    "name": self._extract_security_name(context) or "Unknown Security",
                    "price": self._extract_price(context),
                    "quantity": self._extract_quantity(context),
                    "value": self._extract_value(context),
                    "currency": self._extract_currency(context)
                }
                
                holdings.append(holding)
            
            # Also look for ticker symbols
            ticker_pattern = r'\b([A-Z]{1,5})\b'
            ticker_matches = re.finditer(ticker_pattern, text)
            ticker_positions = {}
            
            for match in ticker_matches:
                ticker = match.group(1)
                if len(ticker) >= 2:  # Ignore single-letter tickers
                    if ticker not in ticker_positions:
                        ticker_positions[ticker] = []
                    ticker_positions[ticker].append(match.start())
            
            # Process tickers that appear multiple times (more likely to be securities)
            for ticker, positions in ticker_positions.items():
                if len(positions) >= 2:
                    # Get context around the first occurrence
                    pos = positions[0]
                    context_start = max(0, pos - 300)
                    context_end = min(len(text), pos + 300)
                    context = text[context_start:context_end]
                    
                    # Check if context looks like it contains security information
                    if re.search(r'share|stock|security|price|quantity|value|תמצית|ניירות ערך|שווי|שער|כמות', context, re.IGNORECASE):
                        holding = {
                            "isin": None,
                            "ticker": ticker,
                            "name": self._extract_security_name(context) or ticker,
                            "price": self._extract_price(context),
                            "quantity": self._extract_quantity(context),
                            "value": self._extract_value(context),
                            "currency": self._extract_currency(context)
                        }
                        
                        # Only add if we have at least price, quantity or value
                        if holding["price"] is not None or holding["quantity"] is not None or holding["value"] is not None:
                            holdings.append(holding)
            
            return holdings
            
        except Exception as e:
            logger.error(f"Error extracting holdings from text: {str(e)}", exc_info=True)
            return []
    
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
            if not isinstance(header, str):
                continue
            header_lower = header.lower()
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
                if not isinstance(cell, str):
                    continue
                # Check for ISIN pattern (2 letters followed by 10 alphanumeric characters)
                if len(cell) == 12 and cell[:2].isalpha() and cell[2:].isalnum():
                    isin_col = i
                # If it's a longer text, it might be a name
                elif len(cell) > 5 and not cell.replace('.', '').isdigit():
                    name_col = i
                # Look for numeric columns for price, quantity, value
                elif cell.replace('.', '').replace(',', '').isdigit():
                    if price_col == -1:
                        price_col = i
                    elif quantity_col == -1:
                        quantity_col = i
                    elif value_col == -1:
                        value_col = i
        
        # Process each row
        for row in table["data"]:
            if len(row) < max(filter(lambda x: x >= 0, [isin_col, name_col, quantity_col, price_col, value_col, currency_col]), default=-1) + 1:
                continue  # Skip rows that don't have enough columns
            
            # Extract values
            isin = row[isin_col] if isin_col >= 0 and isin_col < len(row) else None
            name = row[name_col] if name_col >= 0 and name_col < len(row) else None
            quantity = self._parse_number(row[quantity_col]) if quantity_col >= 0 and quantity_col < len(row) else None
            price = self._parse_number(row[price_col]) if price_col >= 0 and price_col < len(row) else None
            value = self._parse_number(row[value_col]) if value_col >= 0 and value_col < len(row) else None
            currency = row[currency_col] if currency_col >= 0 and currency_col < len(row) else self._detect_currency_in_row(row)
            
            # If we have at least an ISIN or a name, create a holding
            if isin or name:
                holding = {
                    "isin": isin,
                    "name": name or "Unknown Security",
                    "quantity": quantity,
                    "price": price,
                    "value": value,
                    "currency": currency
                }
                holdings.append(holding)
        
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
            r'שם המנפיק[:\s]+([^\n]+)',
            r'נייר ערך[:\s]+([^\n]+)'
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
            output_file = os.path.join(output_dir, f"{base_filename}_pymupdf_{timestamp}_full.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved full content to {output_file}")
            
            # Save tables separately
            if "tables" in content and content["tables"]:
                tables_file = os.path.join(output_dir, f"{base_filename}_pymupdf_{timestamp}_tables.json")
                with open(tables_file, 'w', encoding='utf-8') as f:
                    json.dump(content["tables"], f, ensure_ascii=False, indent=2)
                logger.info(f"Saved tables to {tables_file}")
            
            # Save text separately
            if "text" in content and content["text"]:
                text_file = os.path.join(output_dir, f"{base_filename}_pymupdf_{timestamp}_text.txt")
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
            logger.info(f"Testing extraction on file with PyMuPDF: {file_path}")
            
            # Extract content
            result = self.extract_content(file_path)
            
            # Save the extracted content
            self.save_extracted_content(result)
            
            # Print summary of results
            if output_to_console:
                print(f"\n{'='*50}")
                print(f"PYMUPDF TEST RESULTS FOR: {os.path.basename(file_path)}")
                print(f"{'='*50}")
                print(f"Total pages: {result['metadata']['total_pages']}")
                print(f"Total text length: {len(result['text'])}")
                print(f"Total tables: {len(result['tables'])}")
                print(f"Total images: {len(result['images'])}")
                print(f"Total holdings: {len(result['financial_data']['holdings'])}")
                
                # Print some sample holdings if available
                if result['financial_data']['holdings']:
                    print("\nSample holdings:")
                    for i, holding in enumerate(result['financial_data']['holdings'][:5]):
                        print(f"  {i+1}. ISIN: {holding.get('isin')}, Name: {holding.get('name')}, Value: {holding.get('value')}")
                
                # If no holdings were found
                if len(result['financial_data']['holdings']) == 0:
                    print("\nNo holdings found in the document")
                    
                    # Print first 500 chars of text for debugging
                    print("\nFirst 500 chars of extracted text:")
                    print(result['text'][:500])
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing PDF file with PyMuPDF: {str(e)}", exc_info=True)
            if output_to_console:
                print(f"ERROR: {str(e)}")
            raise 