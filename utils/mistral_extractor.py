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
                logger.debug("OCR parameters: model='mistral-ocr-latest', document={'type': 'document_url', 'document_url': (data_url_length) }")
                response = self.client.ocr.process(
                    model="mistral-ocr-latest",
                    document={
                        "type": "document_url",
                        "document_url": pdf_data_url
                    },
                    include_image_base64=True
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
            logger.info(f"Starting image extraction from response: {type(ocr_response)}")
            logger.info(f"Response attributes: {dir(ocr_response)}")
            
            # Debug - log more information about the response structure
            if hasattr(ocr_response, 'pages'):
                logger.info(f"Number of pages in response: {len(ocr_response.pages)}")
                for i, page in enumerate(ocr_response.pages):
                    logger.info(f"Page {i} attributes: {dir(page)}")
                    # Check if pages have direct image attributes
                    if hasattr(page, 'images'):
                        logger.info(f"Page {i} has {len(page.images)} images")
                    # Check if pages have 'content' containing base64 images
                    if hasattr(page, 'content'):
                        # Look for image patterns in content
                        img_patterns = re.findall(r'!\[(.*?)\]\((.*?)\)', page.content)
                        logger.info(f"Found {len(img_patterns)} image patterns in page {i} content")
            
            # Try both page.images and image patterns in content
            if hasattr(ocr_response, 'pages'):
                for page_idx, page in enumerate(ocr_response.pages):
                    # Method 1: Direct image objects in page
                    if hasattr(page, 'images') and page.images:
                        for img_idx, img in enumerate(page.images):
                            logger.info(f"Processing image {img_idx} from page {page_idx}")
                            image_data = {
                                "page_number": getattr(page, 'page_number', page_idx + 1),
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
                            
                            # Process image and add to results
                            self._process_image_data(image_data)
                            images.append(image_data)
                    
                    # Method 2: Extract images from content with regex patterns
                    elif hasattr(page, 'content'):
                        content = page.content
                        
                        # Find image patterns: ![alt](src)
                        img_patterns = re.findall(r'!\[(.*?)\]\((.*?)\)', content)
                        
                        for img_idx, (alt, src) in enumerate(img_patterns):
                            logger.info(f"Found image pattern in content: alt={alt}, src={src}")
                            
                            # Extract base64 data if present
                            base64_match = re.search(r'data:image/\w+;base64,([^"\')\s]+)', src)
                            image_data = {
                                "page_number": getattr(page, 'page_number', page_idx + 1),
                                "image_data": base64_match.group(1) if base64_match else None,
                                "text": "",
                                "tables": []
                            }
                            
                            # Extract text context around this image
                            # Look for text blocks after image reference
                            context_match = re.search(re.escape(f"![{alt}]({src})") + r'\s*(.*?)(?=!\[|$)', content, re.DOTALL)
                            if context_match:
                                image_data["text"] = context_match.group(1).strip()
                            
                            # Process image and add to results
                            self._process_image_data(image_data)
                            images.append(image_data)
                    
                    # Method 3: Check if the page itself has image_data attribute
                    elif hasattr(page, 'image_data'):
                        logger.info(f"Found image_data directly in page {page_idx}")
                        image_data = {
                            "page_number": getattr(page, 'page_number', page_idx + 1),
                            "image_data": page.image_data,
                            "text": getattr(page, 'text', '') or getattr(page, 'markdown', '') or getattr(page, 'content', ''),
                            "tables": []
                        }
                        
                        # Process image and add to results
                        self._process_image_data(image_data)
                        images.append(image_data)
            
            logger.info(f"Extracted {len(images)} images in total")
            return images
            
        except Exception as e:
            logger.error(f"Error extracting images: {str(e)}", exc_info=True)
            return []
    
    def _process_image_data(self, image_data):
        """Process extracted image data to clean text and extract tables."""
        try:
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
                    if "financial_data" not in image_data:
                        image_data["financial_data"] = {"holdings": []}
                    image_data["financial_data"]["holdings"].append(security)
                
                logger.info(f"Extracted text from image on page {image_data['page_number']}: {image_data['text'][:100]}...")
                
                # Try to extract tables from the image text
                image_data["tables"] = self._extract_tables(image_data["text"])
                logger.info(f"Extracted {len(image_data['tables'])} tables from image on page {image_data['page_number']}")
                
        except Exception as e:
            logger.error(f"Error processing image data: {str(e)}", exc_info=True)

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
            logger.debug("OCR parameters: model='mistral-ocr-latest', document={'type': 'document_url', 'document_url': (signed_url) }")
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": signed_url.url,
                },
                include_image_base64=True
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
            
            # Debug response structure
            if hasattr(ocr_response, 'pages'):
                logger.info(f"Response has {len(ocr_response.pages)} pages")
                for i, page in enumerate(ocr_response.pages[:1]):  # Log just first page to avoid too much logging
                    logger.info(f"Page {i} attributes: {dir(page)}")
            else:
                logger.info(f"Response does not have 'pages' attribute. Available attributes: {dir(ocr_response)}")
            
            # Process each page for text
            if hasattr(ocr_response, 'pages'):
                for page_idx, page in enumerate(ocr_response.pages):
                    # Extract text from different sources
                    page_text = ""
                    if hasattr(page, 'text'):
                        page_text += page.text + "\n"
                        logger.info(f"Found 'text' attribute in page {page_idx+1}, length: {len(page.text)}")
                    if hasattr(page, 'markdown'):
                        page_text += page.markdown + "\n"
                        logger.info(f"Found 'markdown' attribute in page {page_idx+1}, length: {len(page.markdown)}")
                    if hasattr(page, 'content'):
                        page_text += page.content + "\n"
                        logger.info(f"Found 'content' attribute in page {page_idx+1}, length: {len(page.content)}")
                    
                    # Enhanced ISIN detection with more patterns
                    # Standard ISIN (2 letters followed by 10 alphanumeric characters)
                    isin_patterns = [
                        r'([A-Z]{2}[A-Z0-9]{9}\d)',  # Standard ISIN
                        r'ISIN[:\s]+([A-Z]{2}[A-Z0-9]{9}\d)',  # ISIN: XX0000000000
                        r'מספר נייר[:\s]+([A-Z0-9]{10,12})',   # Hebrew "security number" followed by ISIN-like
                        r'נייר ערך[:\s]+([A-Z0-9]{10,12})'     # Hebrew "security" followed by ISIN-like
                    ]
                    
                    for pattern in isin_patterns:
                        isin_matches = re.finditer(pattern, page_text)
                        for match in isin_matches:
                            isin = match.group(1)
                            # Verify it seems like a valid ISIN
                            if re.match(r'^[A-Z]{2}[A-Z0-9]{9}\d$', isin):
                                # Look for associated data near the ISIN
                                context_start = max(0, match.start()-300)
                                context_end = min(len(page_text), match.end()+300)
                                context = page_text[context_start:context_end]
                                
                                # Extract security details
                                security = {
                                    "isin": isin,
                                    "name": self._extract_security_name(context) or "Unknown Security",
                                    "price": self._extract_price(context),
                                    "quantity": self._extract_quantity(context),
                                    "value": self._extract_value(context),
                                    "currency": self._extract_currency(context),
                                    "page": page_idx + 1
                                }
                                
                                # Check if this is a likely duplicate (same ISIN)
                                is_duplicate = False
                                for existing in financial_data["holdings"]:
                                    if existing["isin"] == isin:
                                        is_duplicate = True
                                        # Update with more complete information if available
                                        if not existing["name"] or existing["name"] == "Unknown Security":
                                            existing["name"] = security["name"]
                                        if existing["price"] is None and security["price"] is not None:
                                            existing["price"] = security["price"]
                                        if existing["quantity"] is None and security["quantity"] is not None:
                                            existing["quantity"] = security["quantity"]
                                        if existing["value"] is None and security["value"] is not None:
                                            existing["value"] = security["value"]
                                        break
                                
                                if not is_duplicate:
                                    financial_data["holdings"].append(security)
                                    logger.info(f"Found security with ISIN: {isin} on page {page_idx+1}")
                    
                    # Look for table-like structures in the page text
                    table_results = self._extract_tables_from_text(page_text)
                    if table_results:
                        logger.info(f"Found {len(table_results)} potential tables in page {page_idx+1}")
                    
                    extracted_text += page_text
                    logger.info(f"Extracted text and data from page {page_idx+1}")
            
            # Clean up extracted text
            extracted_text = re.sub(r'!\[img-\d+\.jpeg\]\(img-\d+\.jpeg\)', '', extracted_text)
            extracted_text = re.sub(r'\n\s*\n', '\n\n', extracted_text)
            
            logger.info(f"Total extracted text length: {len(extracted_text)}")
            logger.info(f"Found {len(financial_data['holdings'])} securities directly from text")
            
            # Extract structured tables from the entire text
            tables = self._extract_tables(extracted_text)
            logger.info(f"Extracted {len(tables)} tables from complete text")
            
            # Further analysis on the extracted text to find security holdings
            full_text_holdings = self._extract_holdings_from_full_text(extracted_text)
            if full_text_holdings:
                # Avoid duplicates by checking ISIN
                existing_isins = {h["isin"] for h in financial_data["holdings"]}
                for holding in full_text_holdings:
                    if holding["isin"] not in existing_isins:
                        financial_data["holdings"].append(holding)
                        existing_isins.add(holding["isin"])
            
            logger.info(f"Total unique holdings after full text analysis: {len(financial_data['holdings'])}")
            
            # Extract images and process them
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
            
    def _extract_tables_from_text(self, text):
        """Look for table-like structures in text and extract them."""
        tables = []
        try:
            # Pattern for simple table rows (columns separated by whitespace)
            # This is more relaxed than the markdown table pattern
            rows = text.split('\n')
            
            # Find consecutive lines that might form a table
            i = 0
            while i < len(rows):
                # Skip empty lines
                if not rows[i].strip():
                    i += 1
                    continue
                
                # Check if this might be a header row (contains keywords like "ISIN", "שם", etc.)
                header_keywords = ['isin', 'שם', 'נייר', 'כמות', 'מחיר', 'שער', 'שווי']
                potential_header = rows[i].lower()
                
                if any(keyword in potential_header for keyword in header_keywords):
                    # This could be a header, check the next lines for data rows
                    header_row = rows[i]
                    data_rows = []
                    j = i + 1
                    
                    # Collect potential data rows while they have similar structure
                    while j < len(rows) and j < i + 30:  # Look at most 30 rows ahead
                        if not rows[j].strip():  # Skip empty lines
                            j += 1
                            continue
                            
                        # Check if it has a similar structure to the header (roughly same number of whitespace chunks)
                        # Or contains numbers that might be quantities, prices, etc.
                        if (len(re.findall(r'\S+', rows[j])) >= len(re.findall(r'\S+', header_row)) * 0.7 and
                            len(re.findall(r'\S+', rows[j])) <= len(re.findall(r'\S+', header_row)) * 1.3) or \
                           re.search(r'\d+[.,]\d+', rows[j]):
                            data_rows.append(rows[j])
                            j += 1
                        else:
                            # This doesn't look like a continuation of the table
                            break
                    
                    # If we found some data rows, process this as a table
                    if len(data_rows) >= 2:  # Require at least 2 data rows
                        header_cols = re.findall(r'\S+(?:\s+\S+)*', header_row)
                        processed_data = []
                        
                        # Process each data row
                        for data_row in data_rows:
                            # Try to split into columns with similar spacing as header
                            data_cols = re.findall(r'\S+(?:\s+\S+)*', data_row)
                            if len(data_cols) >= 3:  # Require at least 3 columns to consider it a valid row
                                processed_data.append(data_cols)
                        
                        if processed_data:
                            tables.append({
                                "headers": header_cols,
                                "data": processed_data,
                                "type": "potential_holdings"
                            })
                
                i += 1
            
            logger.info(f"Extracted {len(tables)} potential tables from text section")
            return tables
            
        except Exception as e:
            logger.error(f"Error extracting tables from text: {str(e)}", exc_info=True)
            return []
    
    def _extract_holdings_from_full_text(self, text):
        """Extract holdings information from the full text using pattern matching."""
        holdings = []
        try:
            # Look for patterns that might indicate security holdings
            
            # Pattern 1: ISIN followed by details in proximity
            isin_matches = re.finditer(r'([A-Z]{2}[A-Z0-9]{9}\d)', text)
            for match in isin_matches:
                isin = match.group(1)
                # Get context around the ISIN
                context_start = max(0, match.start() - 300)
                context_end = min(len(text), match.end() + 300)
                context = text[context_start:context_end]
                
                # Extract details from context
                security = {
                    "isin": isin,
                    "name": self._extract_security_name(context) or "Unknown Security",
                    "price": self._extract_price(context),
                    "quantity": self._extract_quantity(context),
                    "value": self._extract_value(context),
                    "currency": self._extract_currency(context)
                }
                
                # Only add if we have at least some data beyond ISIN
                if security["name"] != "Unknown Security" or security["price"] or security["quantity"] or security["value"]:
                    holdings.append(security)
            
            # Pattern 2: Look for securities listed with name and details, even without ISIN
            # This pattern finds lines that look like security entries
            security_patterns = [
                r'([\w\s\-.]+)\s+(?:כמות|שער|מחיר|שווי)\s*[:=]?\s*([\d,.]+)',
                r'([\w\s\-.]+)\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)',
                r'נייר ערך[:\s]+([\w\s\-.]+)[^0-9]+(\d+)'
            ]
            
            for pattern in security_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    if len(match.groups()) >= 2:
                        security_name = match.group(1).strip()
                        # Skip if too short or looks like a header
                        if len(security_name) < 3 or security_name.lower() in ['isin', 'name', 'שם', 'כמות', 'מחיר']:
                            continue
                            
                        # Get context around the match
                        context_start = max(0, match.start() - 200)
                        context_end = min(len(text), match.end() + 200)
                        context = text[context_start:context_end]
                        
                        # Look for an ISIN in proximity
                        isin_match = re.search(r'([A-Z]{2}[A-Z0-9]{9}\d)', context)
                        isin = isin_match.group(1) if isin_match else None
                        
                        # If we already have this ISIN, skip
                        if isin and any(h["isin"] == isin for h in holdings):
                            continue
                            
                        # Extract other details from context
                        security = {
                            "isin": isin,
                            "name": security_name,
                            "price": self._extract_price(context),
                            "quantity": self._extract_quantity(context),
                            "value": self._extract_value(context),
                            "currency": self._extract_currency(context)
                        }
                        
                        # Only add if it has a name and at least one numeric field
                        if (security["price"] is not None or 
                            security["quantity"] is not None or 
                            security["value"] is not None):
                            holdings.append(security)
            
            logger.info(f"Extracted {len(holdings)} holdings from full text analysis")
            return holdings
            
        except Exception as e:
            logger.error(f"Error extracting holdings from full text: {str(e)}", exc_info=True)
            return []

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

    def test_pdf_file(self, file_path, output_to_console=True):
        """Test the extraction on an existing PDF file and print results."""
        try:
            logger.info(f"Testing extraction on file: {file_path}")
            
            # Full extraction using Mistral OCR
            result = self.extract_all_content(file_path)
            
            # Print summary of results
            if output_to_console:
                print(f"\n{'='*50}")
                print(f"TEST RESULTS FOR: {os.path.basename(file_path)}")
                print(f"{'='*50}")
                print(f"Total pages: {result['metadata']['total_pages']}")
                print(f"Total text length: {len(result['text'])}")
                print(f"Total tables: {len(result['tables'])}")
                print(f"Total images: {len(result['images'])}")
                print(f"Total holdings: {len(result['financial_data']['holdings'])}")
                
                # If tables with holdings exist, count them too
                holdings_in_tables = 0
                for table in result['tables']:
                    if table.get('type') == 'holdings' and 'holdings' in table:
                        holdings_in_tables += len(table['holdings'])
                
                print(f"Holdings in tables: {holdings_in_tables}")
                print(f"Total holdings (unique): {len(result['financial_data']['holdings']) + holdings_in_tables}")
                
                # Print some sample holdings if available
                if result['financial_data']['holdings']:
                    print("\nSample holdings from text:")
                    for i, holding in enumerate(result['financial_data']['holdings'][:5]):
                        print(f"  {i+1}. ISIN: {holding['isin']}, Name: {holding['name']}, Value: {holding['value']}")
                
                # Print sample holdings from tables
                table_holdings_printed = 0
                for table in result['tables']:
                    if table.get('type') == 'holdings' and 'holdings' in table:
                        if table_holdings_printed == 0:
                            print("\nSample holdings from tables:")
                        
                        for i, holding in enumerate(table['holdings'][:5]):
                            print(f"  {i+1}. ISIN: {holding['isin']}, Name: {holding['name']}, Value: {holding['value']}")
                            table_holdings_printed += 1
                            if table_holdings_printed >= 5:
                                break
                        
                        if table_holdings_printed >= 5:
                            break
                
                # If no holdings were found
                if len(result['financial_data']['holdings']) == 0 and holdings_in_tables == 0:
                    print("\nNo holdings found in the document")
                    
                    # Print first 500 chars of text for debugging
                    print("\nFirst 500 chars of extracted text:")
                    print(result['text'][:500])
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing PDF file: {str(e)}", exc_info=True)
            if output_to_console:
                print(f"ERROR: {str(e)}")
            raise 