import pdfplumber
import io
import pandas as pd
import re
import os
import tempfile
from utils.ocr_processor import extract_text_from_pdf
import logging
import hashlib
from typing import List, Dict, Any, Callable, Optional
from dotenv import load_dotenv
import google.generativeai as genai

logger = logging.getLogger(__name__)

class SecuritiesPDFProcessor:
    """Processor for extracting securities information from PDF files."""
    
    def __init__(self):
        """Initialize the processor."""
        load_dotenv()
        self.supported_banks = [
            "leumi", "hapoalim", "discount", "mizrahi", 
            "morgan", "goldman", "jp", "interactive", "schwab",
            "fidelity", "vanguard", "merrill"
        ]
        
        # Configure Gemini API
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')
    
    def process_pdf(self, pdf_file_path: str, max_pages: Optional[int] = None, start_page: int = 0) -> List[Dict[str, Any]]:
        """Process PDF file and extract securities information."""
        try:
            # Read PDF file
            with pdfplumber.open(pdf_file_path) as pdf:
                total_pages = len(pdf.pages)
                if max_pages is not None:
                    total_pages = min(total_pages, start_page + max_pages)
                
                all_securities = []
                for page_num in range(start_page, total_pages):
                    page = pdf.pages[page_num]
                    
                    # Extract tables and text
                    tables = page.extract_tables()
                    text = page.extract_text()
                    
                    # Process tables
                    for table in tables:
                        securities = self._process_table(table)
                        all_securities.extend(securities)
                    
                    # Process text if no tables found
                    if not tables and text:
                        securities = self._process_text(text)
                        all_securities.extend(securities)
                
                return all_securities
                
        except Exception as e:
            logger.error(f"Error processing securities PDF: {str(e)}", exc_info=True)
            return []
    
    def _extract_securities_from_text(self, text: str) -> list:
        """Extract securities information from text."""
        securities = []
        
        # Split text into lines
        lines = text.split('\n')
        
        # Regular expressions for different fields
        isin_pattern = r'[A-Z]{2}[A-Z0-9]{10}'
        quantity_pattern = r'Quantity:\s*(\d+(?:,\d+)?(?:\.\d+)?)'
        price_pattern = r'Price:\s*\$(\d+(?:,\d+)?(?:\.\d+)?)'
        market_value_pattern = r'Market Value:\s*\$(\d+(?:,\d+)?(?:\.\d+)?)'
        
        current_security = None
        
        for line in lines:
            # Try to find security name and ISIN
            isin_match = re.search(isin_pattern, line)
            if isin_match:
                if current_security:
                    securities.append(current_security)
                
                current_security = {
                    'isin': isin_match.group(0),
                    'security_name': line.split(isin_match.group(0))[0].strip().rstrip('(').strip(),
                    'quantity': 0,
                    'price': 0,
                    'market_value': 0
                }
                continue
            
            if current_security:
                # Try to find quantity
                quantity_match = re.search(quantity_pattern, line)
                if quantity_match:
                    current_security['quantity'] = float(quantity_match.group(1).replace(',', ''))
                    continue
                
                # Try to find price
                price_match = re.search(price_pattern, line)
                if price_match:
                    current_security['price'] = float(price_match.group(1).replace(',', ''))
                    continue
                
                # Try to find market value
                market_value_match = re.search(market_value_pattern, line)
                if market_value_match:
                    current_security['market_value'] = float(market_value_match.group(1).replace(',', ''))
                    continue
        
        # Add last security if exists
        if current_security:
            securities.append(current_security)
        
        return securities
    
    def _generate_placeholder_isin(self, security_name: str) -> str:
        """Generate a placeholder ISIN for securities without one."""
        name_hash = hashlib.md5(security_name.encode()).hexdigest()
        country_code = "XX"
        identifier = name_hash[:10].upper()
        return f"{country_code}{identifier}"

    def _process_pdf_tables(self, tables, bank_name=None, progress_callback=None):
        """
        Process extracted tables from a PDF.
        
        Args:
            tables: List of extracted tables as DataFrames
            bank_name: Name of the bank
            progress_callback: Progress callback function
            
        Returns:
            List of securities data dictionaries
        """
        securities = []
        
        if not tables:
            logger.warning("No tables found in the PDF")
            return securities
        
        table_count = len(tables)
        for i, table in enumerate(tables):
            if progress_callback:
                progress_callback(50 + (i * 50 // table_count), 100, 
                                 f"Processing table {i+1}/{table_count}")
            
            if isinstance(table, pd.DataFrame) and not table.empty:
                # Look for relevant column patterns
                securities_cols = ['security', 'name', 'isin', 'symbol', 'cusip']
                quantity_cols = ['quantity', 'amount', 'units', 'shares']
                price_cols = ['price', 'value per share']
                value_cols = ['market value', 'value', 'total']
                
                # Find matching columns
                sec_col = next((col for col in table.columns if any(s in str(col).lower() for s in securities_cols)), None)
                qty_col = next((col for col in table.columns if any(s in str(col).lower() for s in quantity_cols)), None)
                price_col = next((col for col in table.columns if any(s in str(col).lower() for s in price_cols)), None)
                val_col = next((col for col in table.columns if any(s in str(col).lower() for s in value_cols)), None)
                
                # If no security name column found, try to find ISIN patterns in any column
                if not sec_col:
                    for col in table.columns:
                        isin_pattern = r'[A-Z]{2}[A-Z0-9]{10}'
                        has_isins = False
                        
                        for _, value in table[col].items():
                            if isinstance(value, str) and re.search(isin_pattern, value):
                                sec_col = col
                                has_isins = True
                                break
                        
                        if has_isins:
                            break
                
                # Process rows with appropriate columns
                if sec_col:
                    for _, row in table.iterrows():
                        security_data = {'bank': bank_name or 'Unknown'}
                        
                        # Extract security details and values
                        if sec_col and pd.notna(row[sec_col]):
                            security_name = str(row[sec_col]).strip()
                            security_data['security_name'] = security_name
                            
                            # Extract ISIN if present in the name
                            isin_match = re.search(r'([A-Z]{2}[A-Z0-9]{10})', security_name)
                            if isin_match:
                                security_data['isin'] = isin_match.group(1)
                        
                        # Extract numeric values
                        for col, key in [(qty_col, 'quantity'), (price_col, 'price'), (val_col, 'market_value')]:
                            if col and pd.notna(row[col]):
                                try:
                                    # Convert value to float, handling various formats
                                    value_str = str(row[col])
                                    # Remove currency symbols, commas, etc.
                                    value_str = re.sub(r'[^\d.-]', '', value_str)
                                    value = float(value_str)
                                    security_data[key] = value
                                except (ValueError, TypeError):
                                    pass
                        
                        # Only add if we have at minimum a security name or ISIN
                        if 'security_name' in security_data:
                            # Generate ISIN if missing
                            if 'isin' not in security_data:
                                security_data['isin'] = self._generate_placeholder_isin(security_data['security_name'])
                            
                            # Calculate market value if missing but have price and quantity
                            if 'market_value' not in security_data and 'price' in security_data and 'quantity' in security_data:
                                security_data['market_value'] = security_data['price'] * security_data['quantity']
                            
                            securities.append(security_data)
        
        if progress_callback:
            progress_callback(100, 100, f"Extracted {len(securities)} securities from tables")
        
        return securities
    
    def _process_pdf_text(self, text_results, bank_name=None, pdf_path=None, progress_callback=None):
        """
        Process extracted text from a PDF.
        
        Args:
            text_results: List of extracted text strings
            bank_name: Name of the bank
            pdf_path: Path to the PDF file
            progress_callback: Progress callback function
            
        Returns:
            List of securities data dictionaries
        """
        securities = []
        
        if not text_results:
            logger.warning("No text content found in the PDF")
            return securities
        
        # Connect all text for processing
        combined_text = "\n".join(text_results) if isinstance(text_results, list) else text_results
        
        if progress_callback:
            progress_callback(60, 100, "Analyzing text content for securities data")
        
        # Look for ISIN patterns
        isin_pattern = r'([A-Z]{2}[A-Z0-9]{10})'
        isin_matches = re.finditer(isin_pattern, combined_text)
        
        for i, match in enumerate(isin_matches):
            isin = match.group(1)
            # Get surrounding context (50 chars before and after)
            start_idx = max(0, match.start() - 50)
            end_idx = min(len(combined_text), match.end() + 50)
            context = combined_text[start_idx:end_idx]
            
            if progress_callback and i % 5 == 0:  # Update every 5 matches to avoid too many callbacks
                progress_callback(60 + (i * 30 // 100), 100, f"Processing security {i+1}")
            
            security_data = {
                'isin': isin,
                'bank': bank_name or 'Unknown'
            }
            
            # Try to extract security name
            # Look for name before ISIN (common format)
            name_pattern = r'([A-Za-z0-9\s.,&\'-]{3,30})\s*?' + re.escape(isin)
            name_match = re.search(name_pattern, context)
            
            if name_match:
                security_data['security_name'] = name_match.group(1).strip()
            else:
                # Try looking for name after ISIN
                name_pattern = re.escape(isin) + r'\s*?([A-Za-z0-9\s.,&\'-]{3,30})'
                name_match = re.search(name_pattern, context)
                if name_match:
                    security_data['security_name'] = name_match.group(1).strip()
            
            # Look for quantity, price, and market value near the ISIN
            # First look for numbers
            number_pattern = r'([\d,.]+)'
            number_matches = re.findall(number_pattern, context)
            
            # Convert matches to floats and assign based on magnitude
            numbers = []
            for num_str in number_matches:
                try:
                    # Remove commas and convert to float
                    num = float(num_str.replace(',', ''))
                    numbers.append(num)
                except ValueError:
                    continue
            
            # Sort numbers by size
            numbers.sort()
            
            # Assign based on typical magnitude patterns
            if numbers:
                if len(numbers) >= 3:
                    # If we have at least 3 numbers, assume the pattern
                    security_data['quantity'] = numbers[-3]  # Typically medium number
                    security_data['price'] = numbers[-2]     # Typically medium-large number
                    security_data['market_value'] = numbers[-1]  # Typically largest number
                elif len(numbers) == 2:
                    # With 2 numbers, guess based on magnitude
                    if numbers[1] / numbers[0] > 50:  # Significant difference suggests price and value
                        security_data['price'] = numbers[0]
                        security_data['market_value'] = numbers[1]
                    else:  # Otherwise assume quantity and price
                        security_data['quantity'] = numbers[0]
                        security_data['price'] = numbers[1]
                elif len(numbers) == 1:
                    # With just 1 number, assume it's market value
                    security_data['market_value'] = numbers[0]
            
            # Add to results if we have minimum required data
            if 'isin' in security_data:
                securities.append(security_data)
        
        if progress_callback:
            progress_callback(95, 100, f"Extracted {len(securities)} securities from text")
        
        return securities
    
    def _process_with_pdfplumber(self, pdf_path, bank_name=None, max_pages=None, progress_callback=None):
        """
        Process PDF using pdfplumber directly.
        
        Args:
            pdf_path: Path to the PDF file
            bank_name: Name of the bank
            max_pages: Maximum number of pages to process
            progress_callback: Progress callback function
            
        Returns:
            List of securities data dictionaries
        """
        securities = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Determine pages to process
                total_pages = len(pdf.pages)
                pages_to_process = min(total_pages, max_pages or total_pages)
                
                if progress_callback:
                    progress_callback(0, 100, f"Processing {pages_to_process} pages with pdfplumber")
                
                # Check if this is a specific bank we have custom handlers for
                if bank_name and bank_name.lower() in self.supported_banks:
                    # Call bank-specific processor if available
                    processor_method = getattr(self, f"_process_{bank_name.lower()}", None)
                    if processor_method and callable(processor_method):
                        return processor_method(pdf, max_pages, progress_callback)
                
                # Generic processing
                all_text = ""
                for i, page in enumerate(pdf.pages[:pages_to_process]):
                    if progress_callback:
                        progress_callback(i * 100 // pages_to_process, 100, 
                                         f"Processing page {i+1}/{pages_to_process}")
                    
                    # Extract text
                    text = page.extract_text() or ""
                    all_text += text + "\n"
                    
                    # Try to extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            # Convert table to DataFrame
                            df = pd.DataFrame(table[1:], columns=table[0] if table[0] else None)
                            extracted_securities = self._extract_securities_from_df(df, bank_name)
                            securities.extend(extracted_securities)
                
                # Process extracted text if we didn't find securities from tables
                if not securities and all_text:
                    text_securities = self._process_pdf_text([all_text], bank_name, pdf_path, progress_callback)
                    securities.extend(text_securities)
                
                if progress_callback:
                    progress_callback(100, 100, f"Extracted {len(securities)} securities")
                
                return securities
                    
        except Exception as e:
            logger.error(f"Error processing PDF with pdfplumber: {e}", exc_info=True)
            return securities
    
    def _extract_securities_from_df(self, df, bank_name=None):
        """
        Extract securities information from a DataFrame.
        
        Args:
            df: DataFrame containing securities data
            bank_name: Name of the bank
            
        Returns:
            List of securities data dictionaries
        """
        securities = []
        
        if df.empty:
            return securities
        
        # Look for columns that might contain securities information
        security_name_col = None
        isin_col = None
        quantity_col = None
        price_col = None
        market_value_col = None
        
        # Check each column for patterns
        for col in df.columns:
            col_str = str(col).lower()
            
            if col_str in ['name', 'security', 'description', 'instrument', 'security name', 'שם נייר']:
                security_name_col = col
            elif col_str in ['isin', 'international securities identification number']:
                isin_col = col
            elif col_str in ['quantity', 'amount', 'units', 'shares', 'כמות']:
                quantity_col = col
            elif col_str in ['price', 'שער', 'rate', 'price per unit', 'מחיר']:
                price_col = col
            elif col_str in ['market value', 'value', 'notional', 'שווי', 'שווי שוק']:
                market_value_col = col
        
        # If we couldn't identify columns, check content
        if not security_name_col and not isin_col:
            # Look for ISIN pattern in any column
            for col in df.columns:
                has_isin = False
                for val in df[col]:
                    if isinstance(val, str) and re.search(r'[A-Z]{2}[A-Z0-9]{10}', val):
                        isin_col = col
                        has_isin = True
                        break
                if has_isin:
                    break
        
        # Extract securities
        for _, row in df.iterrows():
            security_data = {'bank': bank_name or 'Unknown'}
            
            # Extract security name if column exists
            if security_name_col and pd.notna(row.get(security_name_col)):
                security_data['security_name'] = str(row.get(security_name_col)).strip()
            
            # Extract ISIN
            if isin_col and pd.notna(row.get(isin_col)):
                isin_val = str(row.get(isin_col))
                isin_match = re.search(r'([A-Z]{2}[A-Z0-9]{10})', isin_val)
                if isin_match:
                    security_data['isin'] = isin_match.group(1)
            
            # Extract numeric fields
            for col, field in [
                (quantity_col, 'quantity'),
                (price_col, 'price'),
                (market_value_col, 'market_value')
            ]:
                if col and pd.notna(row.get(col)):
                    try:
                        val_str = str(row.get(col))
                        # Clean up the value
                        val_str = re.sub(r'[^\d.-]', '', val_str)
                        val = float(val_str)
                        security_data[field] = val
                    except (ValueError, TypeError):
                        pass
            
            # Check if we have enough data to consider this a security
            if 'security_name' in security_data or 'isin' in security_data:
                # Generate ISIN if missing
                if 'isin' not in security_data and 'security_name' in security_data:
                    security_data['isin'] = self._generate_placeholder_isin(security_data['security_name'])
                
                # Calculate market value if missing but have price and quantity
                if 'market_value' not in security_data and 'price' in security_data and 'quantity' in security_data:
                    security_data['market_value'] = security_data['price'] * security_data['quantity']
                
                securities.append(security_data)
        
        return securities
    
    # Methods for specific banks can be implemented as needed
    def _process_jp_morgan(self, pdf, max_pages=None, progress_callback=None):
        """JP Morgan specific processing."""
        # Implementation for JP Morgan statement format
        securities = []
        # ... custom processing ...
        return securities
    
    def _process_interactive_brokers(self, pdf, max_pages=None, progress_callback=None):
        """Interactive Brokers specific processing."""
        # Implementation for IB statement format  
        securities = []
        # ... custom processing ...
        return securities
    
    def _process_table(self, table: List[List[str]]) -> List[Dict[str, Any]]:
        """Process a table and extract securities information."""
        securities = []
        
        # Convert table to DataFrame for easier processing
        df = pd.DataFrame(table[1:], columns=table[0] if table else [])
        
        for _, row in df.iterrows():
            security = {}
            
            # Try to identify columns
            for col in row.index:
                col_lower = str(col).lower()
                if any(term in col_lower for term in ['name', 'security', 'description']):
                    security['security_name'] = str(row[col]).strip()
                elif 'isin' in col_lower:
                    security['isin'] = str(row[col]).strip()
                elif any(term in col_lower for term in ['quantity', 'units', 'shares']):
                    try:
                        security['quantity'] = float(str(row[col]).replace(',', ''))
                    except:
                        continue
                elif any(term in col_lower for term in ['price', 'value per share']):
                    try:
                        security['price'] = float(str(row[col]).replace(',', ''))
                    except:
                        continue
                elif any(term in col_lower for term in ['market value', 'total value']):
                    try:
                        security['market_value'] = float(str(row[col]).replace(',', ''))
                    except:
                        continue
            
            # Only add if we have the required fields
            if all(field in security for field in ['security_name', 'quantity', 'market_value']):
                # Calculate price if not provided
                if 'price' not in security and security['quantity'] > 0:
                    security['price'] = security['market_value'] / security['quantity']
                securities.append(security)
        
        return securities
        
    def _process_text(self, text: str) -> List[Dict[str, Any]]:
        """Process text content to extract securities information."""
        securities = []
        
        # Split into lines
        lines = text.split('\n')
        
        # Process each line
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Try to extract security information using regex
            import re
            
            # Look for patterns like:
            # Security Name (ISIN) Quantity Price Market Value
            pattern = r'([^()]+)\s*(?:\(([\w\d]+)\))?\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*(\d+(?:,\d+)?(?:\.\d+)?)'
            
            match = re.search(pattern, line)
            if match:
                security = {
                    'security_name': match.group(1).strip(),
                    'isin': match.group(2) if match.group(2) else '',
                    'quantity': float(match.group(3).replace(',', '')),
                    'price': float(match.group(4).replace(',', '')),
                    'market_value': float(match.group(5).replace(',', ''))
                }
                securities.append(security)
        
        return securities