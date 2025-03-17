import pdfplumber
import io
import pandas as pd
import re
import os
import tempfile
from utils.ocr_processor import extract_text_from_pdf
import logging
import hashlib

logger = logging.getLogger(__name__)

class SecuritiesPDFProcessor:
    """Processes PDF files to extract securities information."""
    
    def __init__(self):
        self.supported_banks = [
            "leumi", "hapoalim", "discount", "mizrahi", 
            "morgan", "goldman", "jp", "interactive", "schwab",
            "fidelity", "vanguard", "merrill"
        ]
    
    def process_pdf(self, pdf_file_path, bank_name=None):
        """Process a PDF file to extract securities information."""
        # Determine bank name from filename if not provided
        if not bank_name:
            file_basename = os.path.basename(pdf_file_path).lower()
            for bank in self.supported_banks:
                if bank in file_basename:
                    bank_name = bank
                    break
        
        logger.info(f"Processing securities PDF for bank: {bank_name}")
        
        # Extract text using OCR processor
        extracted_results, result_type = extract_text_from_pdf(pdf_file_path)
        
        if result_type == "table":
            return self._process_pdf_tables(extracted_results, bank_name)
        elif result_type == "text":
            return self._process_pdf_text(extracted_results, bank_name, pdf_file_path)
        else:
            return self._process_with_pdfplumber(pdf_file_path, bank_name)

    def _process_pdf_tables(self, tables, bank_name=None):
        """Process extracted tables from a PDF."""
        securities = []
        
        for table in tables:
            if isinstance(table, pd.DataFrame):
                securities.extend(self._extract_securities_from_df(table, bank_name))
                
        return securities

    def _process_pdf_text(self, text_results, bank_name=None, pdf_path=None):
        """Process extracted text from a PDF."""
        securities = []
        text = "\n".join(text_results) if isinstance(text_results, list) else text_results
        
        # Look for ISIN patterns
        isin_pattern = r'([A-Z]{2}[A-Z0-9]{10})'
        for match in re.finditer(isin_pattern, text):
            isin = match.group(1)
            context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
            
            security_data = {
                'isin': isin,
                'bank': bank_name or 'Unknown'
            }
            
            # Try to extract security name
            name_match = re.search(r'([A-Za-z0-9\s.,&\'-]{3,30})\s*?' + re.escape(isin), context)
            if name_match:
                security_data['security_name'] = name_match.group(1).strip()
            
            # Look for numbers (quantity, price, value)
            numbers = re.findall(r'[\d,.]+', context)
            numbers = [float(n.replace(',', '')) for n in numbers if n.replace(',', '').replace('.', '').isdigit()]
            
            if numbers:
                if len(numbers) >= 1:
                    security_data['quantity'] = numbers[0]
                if len(numbers) >= 2:
                    security_data['price'] = numbers[1]
                if len(numbers) >= 3:
                    security_data['market_value'] = numbers[2]
            
            securities.append(security_data)
            
        return securities

    def _process_with_pdfplumber(self, pdf_path, bank_name=None):
        """Process PDF using pdfplumber directly."""
        securities = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                
                if text:
                    return self._process_pdf_text(text, bank_name)
                    
        except Exception as e:
            logger.error(f"Error processing PDF with pdfplumber: {e}")
            
        return securities

    def _extract_securities_from_df(self, df, bank_name=None):
        """Extract securities information from a DataFrame."""
        securities = []
        
        for _, row in df.iterrows():
            security_data = {
                'isin': row.get('ISIN', self._generate_placeholder_isin(row.get('Security Name', 'Unknown'))),
                'security_name': row.get('Security Name', 'Unknown'),
                'quantity': row.get('Quantity', 0),
                'price': row.get('Price', 0),
                'market_value': row.get('Market Value', 0),
                'bank': bank_name or 'Unknown'
            }
            securities.append(security_data)
        
        return securities
    
    def _generate_placeholder_isin(self, security_name):
        """Generate a placeholder ISIN for securities without one."""
        name_hash = hashlib.md5(security_name.encode()).hexdigest()
        return f"XX{name_hash[:10].upper()}"
