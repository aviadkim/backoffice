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
        if not bank_name:
            file_basename = os.path.basename(pdf_file_path).lower()
            for bank in self.supported_banks:
                if bank in file_basename:
                    bank_name = bank
                    break
        
        logger.info(f"Processing securities PDF for bank: {bank_name}")
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
            if table.empty:
                continue
            
            securities_cols = ['security', 'name', 'isin', 'symbol', 'cusip']
            quantity_cols = ['quantity', 'amount', 'units', 'shares']
            price_cols = ['price', 'value per share']
            value_cols = ['market value', 'value', 'total']
            
            # Find matching columns
            sec_col = next((col for col in table.columns if any(s in str(col).lower() for s in securities_cols)), None)
            qty_col = next((col for col in table.columns if any(s in str(col).lower() for s in quantity_cols)), None)
            price_col = next((col for col in table.columns if any(s in str(col).lower() for s in price_cols)), None)
            val_col = next((col for col in table.columns if any(s in str(col).lower() for s in value_cols)), None)
            
            # Process rows with appropriate columns
            if sec_col:
                for _, row in table.iterrows():
                    security_data = {'bank': bank_name or 'Unknown'}
                    
                    # Extract security details and values
                    if sec_col and pd.notna(row[sec_col]):
                        security_name = str(row[sec_col]).strip()
                        security_data['security_name'] = security_name
                        isin_match = re.search(r'([A-Z]{2}[A-Z0-9]{10})', security_name)
                        if isin_match:
                            security_data['isin'] = isin_match.group(1)
                    
                    # Extract numeric values
                    for col, key in [(qty_col, 'quantity'), (price_col, 'price'), (val_col, 'market_value')]:
                        if col and pd.notna(row[col]):
                            try:
                                value = float(str(row[col]).replace(',', '').replace('$', ''))
                                security_data[key] = value
                            except (ValueError, TypeError):
                                pass
                    
                    if 'security_name' in security_data and any(k in security_data for k in ['quantity', 'price', 'market_value']):
                        if 'isin' not in security_data:
                            security_data['isin'] = self._generate_placeholder_isin(security_data['security_name'])
                        securities.append(security_data)
        
        return securities
    
    def _process_pdf_text(self, text_results, bank_name=None, pdf_path=None):
        """Process extracted text from a PDF."""
        # ... implementation ...
        pass
        
    def _process_with_pdfplumber(self, pdf_path, bank_name=None):
        """Process PDF using pdfplumber directly."""
        # ... implementation ...
        pass
        
    def _extract_securities_from_df(self, df, bank_name=None):
        """Extract securities information from a DataFrame."""
        # ... implementation ...
        pass
        
    def _generate_placeholder_isin(self, security_name):
        """Generate a placeholder ISIN for securities without one."""
        name_hash = hashlib.md5(security_name.encode()).hexdigest()
        country_code = "XX"
        identifier = name_hash[:10].upper()
        return f"{country_code}{identifier}"

# Test function for direct usage
def process_pdf_file(file_path, bank_name=None):
    processor = SecuritiesPDFProcessor()
    return processor.process_pdf(file_path, bank_name)
