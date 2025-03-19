import pdfplumber
import io
import pandas as pd
import re
import os
import tempfile
from utils.ocr_processor import extract_text_from_pdf
import logging
import hashlib
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SecuritiesPDFProcessor:
    """Processes PDF files to extract securities information."""
    
    def __init__(self):
        self.supported_banks = [
            "leumi", "hapoalim", "discount", "mizrahi", 
            "morgan", "goldman", "jp", "interactive", "schwab",
            "fidelity", "vanguard", "merrill"
        ]
    
    def process_pdf(self, pdf_path: str, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Process PDF file and extract securities information."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                if max_pages is not None:
                    total_pages = min(total_pages, int(max_pages))
                
                securities = []
                for page_num in range(total_pages):
                    page = pdf.pages[page_num]
                    tables = page.extract_tables()
                    
                    for table in tables:
                        extracted = self._process_table(table)
                        if extracted:
                            securities.extend(extracted)
                    
                    # If no tables found, try text extraction
                    if not tables:
                        text = page.extract_text()
                        extracted = self._process_text(text)
                        if extracted:
                            securities.extend(extracted)
                
                return securities
        except Exception as e:
            logger.error(f"Error processing securities PDF: {str(e)}", exc_info=True)
            return []

    def _process_table(self, table: List[List[str]]) -> List[Dict[str, Any]]:
        securities = []
        if not table or not table[0]:
            return securities
            
        headers = [str(h).lower() for h in table[0]]
        
        for row in table[1:]:
            if not row or all(cell == '' for cell in row):
                continue
                
            security = {}
            for idx, cell in enumerate(row):
                if idx >= len(headers):
                    continue
                    
                header = headers[idx]
                if any(term in header for term in ['name', 'security', 'description']):
                    security['security_name'] = str(cell).strip()
                elif 'isin' in header:
                    security['isin'] = str(cell).strip()
                elif any(term in header for term in ['quantity', 'units', 'shares']):
                    try:
                        security['quantity'] = float(str(cell).replace(',', ''))
                    except (ValueError, TypeError):
                        continue
                elif any(term in header for term in ['price', 'value per share']):
                    try:
                        security['price'] = float(str(cell).replace(',', ''))
                    except (ValueError, TypeError):
                        continue
                elif any(term in header for term in ['market value', 'total value']):
                    try:
                        security['market_value'] = float(str(cell).replace(',', ''))
                    except (ValueError, TypeError):
                        continue
            
            if security.get('security_name') and security.get('quantity'):
                securities.append(security)
        
        return securities

    def _process_text(self, text: str) -> List[Dict[str, Any]]:
        securities = []
        lines = text.split('\n')
        
        for line in lines:
            if not line.strip():
                continue
            
            # Match common patterns for securities data
            patterns = [
                # Pattern 1: Name ISIN Quantity Price Value
                r'([^0-9]+)\s*((?:[A-Z]{2})?[A-Z0-9]{10,12})?\s*(\d[,.\d]*)\s*(?:@\s*)?(\d[,.\d]*)\s*(\d[,.\d]*)',
                # Pattern 2: Name Quantity @ Price
                r'([^@]+)\s*(\d[,.\d]*)\s*@\s*(\d[,.\d]*)',
                # Pattern 3: Name (ISIN) Quantity
                r'([^(]+)\s*\(([A-Z0-9]{12})\)\s*(\d[,.\d]*)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    groups = match.groups()
                    security = {'security_name': groups[0].strip()}
                    
                    # Add ISIN if present
                    if len(groups) > 1 and groups[1] and len(groups[1]) >= 10:
                        security['isin'] = groups[1].strip()
                    
                    # Add quantity
                    try:
                        quantity_str = next(g for g in groups[1:] if g and any(c.isdigit() for c in g))
                        security['quantity'] = float(quantity_str.replace(',', ''))
                    except (StopIteration, ValueError):
                        continue
                    
                    # Add price if present
                    if len(groups) > 3:
                        try:
                            security['price'] = float(groups[-2].replace(',', ''))
                            security['market_value'] = float(groups[-1].replace(',', ''))
                        except (ValueError, IndexError):
                            pass
                    
                    securities.append(security)
                    break
        
        return securities
