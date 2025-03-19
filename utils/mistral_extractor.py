import os
import base64
import logging
import re
import json
from mistralai import Mistral
from dotenv import load_dotenv
from datetime import datetime
import time

# הגדרת לוגים
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
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
        """Initialize the Mistral OCR extractor."""
        self.api_key = MISTRAL_API_KEY
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is not set")
        
        logger.debug(f"MISTRAL_API_KEY exists: {bool(self.api_key)}")
        logger.debug("Initializing Mistral client...")
        
        try:
            self.client = Mistral(api_key=self.api_key)
            self.model = "mistral-ocr-latest"  # מודל ה-OCR של Mistral
            logger.info("Mistral OCR extractor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Mistral client: {str(e)}")
            raise
    
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

    def extract_all_content(self, pdf_path):
        """Extract all content from PDF including text, tables and images."""
        try:
            logger.info(f"Starting to process PDF file: {pdf_path}")
            start_time = time.time()
            
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file not found: {pdf_path}")
                return None
            
            # Initialize OCR
            try:
                logger.info("Initializing OCR client...")
                ocr = self.client.ocr
                logger.info("OCR initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OCR: {str(e)}", exc_info=True)
                return None
            
            # Process PDF
            logger.info("Starting PDF processing")
            try:
                logger.info("Reading PDF file...")
                with open(pdf_path, 'rb') as file:
                    pdf_content = file.read()
                logger.info(f"Read {len(pdf_content)} bytes from PDF file")
                
                logger.info("Converting PDF to base64...")
                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                data_url = f"data:application/pdf;base64,{pdf_base64}"
                
                logger.info("Sending request to Mistral API...")
                result = self.client.chat.completions.create(
                    model="mistral-large-latest",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Extract all text and tables from this PDF document. Include any financial data, account numbers, dates, and transaction details. Format tables in markdown format."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": data_url
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=4096
                )
                
                if not result:
                    logger.error("OCR processing returned no results")
                    return None
                    
                logger.info("Successfully received response from Mistral API")
                
            except Exception as e:
                logger.error(f"Error during PDF processing: {str(e)}", exc_info=True)
                return None
            
            # Initialize result structure
            extracted_content = {
                "metadata": {
                    "filename": os.path.basename(pdf_path),
                    "total_pages": 1,  # We'll update this based on the content
                    "file_size": os.path.getsize(pdf_path),
                    "processed_date": datetime.now().isoformat()
                },
                "tables": [],
                "text": [],
                "images": [],
                "summary": {
                    "total_income": 0,
                    "total_expenses": 0,
                    "balance": 0,
                    "num_transactions": 0
                },
                "transactions": []
            }
            
            # Process the response
            try:
                content = result.choices[0].message.content
                logger.info(f"Extracted content length: {len(content)} characters")
                
                # Split into pages
                pages = content.split("\n\n")
                logger.info(f"Found {len(pages)} pages")
                
                # Process each page
                for page_num, page_content in enumerate(pages, 1):
                    try:
                        page_start_time = time.time()
                        logger.info(f"Processing page {page_num}/{len(pages)}")
                        
                        # Extract text from page
                        if page_content:
                            logger.info(f"Extracted {len(page_content)} characters from page {page_num}")
                            extracted_content["text"].append({
                                "page": page_num,
                                "content": page_content
                            })
                        
                        # Extract tables from page
                        table_pattern = r"\|[^|]+\|[^|]+\|[\s\S]*?(?=\n\n|\Z)"
                        tables = re.finditer(table_pattern, page_content)
                        
                        for table_match in tables:
                            table_text = table_match.group(0)
                            logger.info(f"Found table on page {page_num}")
                            
                            # Parse table
                            rows = [row.strip().split('|') for row in table_text.split('\n')]
                            rows = [[cell.strip() for cell in row if cell.strip()] for row in rows if any(cell.strip() for cell in row)]
                            
                            if len(rows) >= 2:  # At least header and one data row
                                table_data = {
                                    "page": page_num,
                                    "headers": rows[0],
                                    "rows": rows[1:],
                                    "source": "text"
                                }
                                extracted_content["tables"].append(table_data)
                                logger.info(f"Added table with {len(rows)-1} rows")
                        
                        page_processing_time = time.time() - page_start_time
                        logger.info(f"Page {page_num}/{len(pages)} processed in {page_processing_time:.2f} seconds")
                        
                    except Exception as e:
                        logger.error(f"Error processing page {page_num}: {str(e)}", exc_info=True)
                        continue
                
                # Update metadata
                extracted_content["metadata"]["total_pages"] = len(pages)
                
                total_processing_time = time.time() - start_time
                logger.info(f"Total processing completed in {total_processing_time:.2f} seconds")
                logger.info(f"Extracted {len(extracted_content['tables'])} tables and {len(extracted_content['text'])} text sections")
                
                return extracted_content
                
            except Exception as e:
                logger.error(f"Error processing response: {str(e)}", exc_info=True)
                return None
            
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}", exc_info=True)
            return None

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
            base_filename = os.path.splitext(content['filename'])[0]
            
            # Save full content
            output_file = os.path.join(output_dir, f"{base_filename}_{timestamp}_full.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            # Save tables separately
            if content["tables"]:
                tables_file = os.path.join(output_dir, f"{base_filename}_{timestamp}_tables.json")
                with open(tables_file, 'w', encoding='utf-8') as f:
                    json.dump(content["tables"], f, ensure_ascii=False, indent=2)
            
            # Save text separately
            text_file = os.path.join(output_dir, f"{base_filename}_{timestamp}_text.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(content["text"])
            
            # Save images data separately
            if content["images"]:
                images_file = os.path.join(output_dir, f"{base_filename}_{timestamp}_images.json")
                with open(images_file, 'w', encoding='utf-8') as f:
                    json.dump(content["images"], f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved extracted content to {output_dir}")
            
        except Exception as e:
            logger.error(f"Error saving extracted content: {str(e)}", exc_info=True)
            raise 