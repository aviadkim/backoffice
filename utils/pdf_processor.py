# utils/pdf_processor.py
import pdfplumber
import re
import pandas as pd
import tabula
import io
from typing import Dict, List, Any, Optional

class BankStatementParser:
    """Parser for extracting data from global bank and brokerage statements."""
    
    def __init__(self):
        self.institution_formats = {
            # Israeli Banks
            "bank_leumi": self._parse_bank_leumi,
            "bank_hapoalim": self._parse_bank_hapoalim,
            "bank_discount": self._parse_bank_discount,
            "bank_mizrahi": self._parse_bank_mizrahi,
            
            # Global Investment Banks & Brokerages
            "jp_morgan": self._parse_jp_morgan,
            "goldman_sachs": self._parse_goldman_sachs,
            "morgan_stanley": self._parse_morgan_stanley,
            "credit_suisse": self._parse_credit_suisse,
            "ubs": self._parse_ubs,
            "deutsche_bank": self._parse_deutsche_bank,
            "hsbc": self._parse_hsbc,
            "barclays": self._parse_barclays,
            "bnp_paribas": self._parse_bnp_paribas,
            
            # Global Brokerages
            "interactive_brokers": self._parse_interactive_brokers,
            "charles_schwab": self._parse_charles_schwab,
            "fidelity": self._parse_fidelity,
            "td_ameritrade": self._parse_td_ameritrade,
            "vanguard": self._parse_vanguard,
            "merrill_lynch": self._parse_merrill_lynch,
            "etrade": self._parse_etrade,
            "robinhood": self._parse_robinhood,
            
            # European Banks
            "santander": self._parse_santander,
            "ing": self._parse_ing,
            "societe_generale": self._parse_societe_generale,
            "unicredit": self._parse_unicredit,
            "bbva": self._parse_bbva,
            
            # Asian Financial Institutions
            "nomura": self._parse_nomura,
            "mitsubishi_ufj": self._parse_mitsubishi_ufj,
            "icbc": self._parse_icbc,
            "dbs": self._parse_dbs,
            
            # Default parser
            "default": self._parse_generic
        }
    
    def parse_statement(self, pdf_file, institution_type: str = None) -> Dict[str, Any]:
        """
        Parse a bank or brokerage statement PDF and extract securities data.
        
        Args:
            pdf_file: PDF file object or path
            institution_type: Type of financial institution statement to parse
            
        Returns:
            Dict containing extracted data
        """
        # Auto-detect institution if not specified
        if not institution_type:
            institution_type = self._detect_institution_type(pdf_file)
        
        # Get the appropriate parser
        parser_func = self.institution_formats.get(institution_type, self.institution_formats["default"])
        
        # Parse the statement
        return parser_func(pdf_file)
    
    def _detect_institution_type(self, pdf_file) -> str:
        """Detect the financial institution type from the PDF content."""
        # Open the first page
        with pdfplumber.open(pdf_file) as pdf:
            if len(pdf.pages) > 0:
                text = pdf.pages[0].extract_text().lower()
                
                # Check for institution identifiers
                # Israeli Banks
                if "bank leumi" in text or "בנק לאומי" in text:
                    return "bank_leumi"
                elif "bank hapoalim" in text or "בנק הפועלים" in text:
                    return "bank_hapoalim"
                elif "bank discount" in text or "בנק דיסקונט" in text:
                    return "bank_discount"
                elif "mizrahi tefahot" in text or "בנק מזרחי טפחות" in text:
                    return "bank_mizrahi"
                
                # Global Investment Banks
                elif "j.p. morgan" in text or "jpmorgan" in text:
                    return "jp_morgan"
                elif "goldman sachs" in text:
                    return "goldman_sachs"
                elif "morgan stanley" in text:
                    return "morgan_stanley"
                elif "credit suisse" in text:
                    return "credit_suisse"
                elif "ubs " in text or "ubs financial services" in text:
                    return "ubs"
                elif "deutsche bank" in text:
                    return "deutsche_bank"
                elif "hsbc" in text:
                    return "hsbc"
                elif "barclays" in text:
                    return "barclays"
                elif "bnp paribas" in text:
                    return "bnp_paribas"
                
                # Global Brokerages
                elif "interactive brokers" in text:
                    return "interactive_brokers"
                elif "charles schwab" in text:
                    return "charles_schwab"
                elif "fidelity investments" in text or "fidelity brokerage" in text:
                    return "fidelity"
                elif "td ameritrade" in text:
                    return "td_ameritrade"
                elif "vanguard" in text:
                    return "vanguard"
                elif "merrill lynch" in text or "merrill edge" in text:
                    return "merrill_lynch"
                elif "e*trade" in text or "etrade" in text:
                    return "etrade"
                elif "robinhood" in text:
                    return "robinhood"
                
                # European Banks
                elif "santander" in text:
                    return "santander"
                elif "ing " in text:
                    return "ing"
                elif "societe generale" in text:
                    return "societe_generale"
                elif "unicredit" in text:
                    return "unicredit"
                elif "bbva" in text:
                    return "bbva"
                
                # Asian Financial Institutions
                elif "nomura" in text:
                    return "nomura"
                elif "mitsubishi ufj" in text or "mufg" in text:
                    return "mitsubishi_ufj"
                elif "industrial and commercial bank of china" in text or "icbc" in text:
                    return "icbc"
                elif "dbs bank" in text or "dbs group" in text:
                    return "dbs"
        
        # Default fallback
        return "default"
    
    # Implementation for JP Morgan
    def _parse_jp_morgan(self, pdf_file) -> Dict[str, Any]:
        """Parse JP Morgan statement."""
        securities = []
        report_date = None
        account_number = None
        
        with pdfplumber.open(pdf_file) as pdf:
            # Extract report date (typically in the header)
            first_page_text = pdf.pages[0].extract_text()
            date_match = re.search(r'(?:As of|Statement Period|Date)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})', first_page_text)
            if date_match:
                report_date = date_match.group(1)
            
            # Extract account number
            account_match = re.search(r'(?:Account|A/C)[:\s#]+([A-Z0-9\-]+)', first_page_text)
            if account_match:
                account_number = account_match.group(1)
            
            # Look for securities tables - typically these have "Holdings" or "Securities" in the header
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                
                # Look for sections that might contain securities information
                if any(header in text for header in ["Holdings", "Portfolio Holdings", "Investment Detail", "Securities"]):
                    # Extract tables using tabula
                    tables = tabula.read_pdf(
                        io.BytesIO(pdf.stream.get_data()), 
                        pages=str(page_num + 1),  # tabula uses 1-based page numbering
                        multiple_tables=True
                    )
                    
                    for table in tables:
                        # Process the table to extract securities data
                        # JP Morgan typically includes columns for description, CUSIP/ISIN, quantity, price, and market value
                        if len(table.columns) >= 5:
                            # Look for ISIN/CUSIP pattern in any column
                            for col in table.columns:
                                table_with_isins = table[table[col].str.match(r'[A-Z0-9]{10,12}', na=False)].copy()
                                
                                if not table_with_isins.empty:
                                    # Process rows with ISIN/CUSIP
                                    for _, row in table_with_isins.iterrows():
                                        security = {
                                            'isin': row[col],  # Using the identified ISIN/CUSIP column
                                            'bank': 'JP Morgan'
                                        }
                                        
                                        # Try to extract other details based on common JP Morgan formatting
                                        # Description is usually in the column before or after the ISIN
                                        desc_col = table.columns[max(0, list(table.columns).index(col) - 1)]
                                        if desc_col != col and desc_col in row:
                                            security['security_name'] = row[desc_col]
                                        
                                        # Look for numeric columns that might be quantity, price, value
                                        for potential_col in table.columns:
                                            cell_value = row[potential_col]
                                            if pd.notna(cell_value) and isinstance(cell_value, (int, float)):
                                                if 'quantity' not in security and cell_value < 1000000:  # Likely quantity
                                                    security['quantity'] = cell_value
                                                elif 'price' not in security and cell_value < 10000:  # Likely price
                                                    security['price'] = cell_value
                                                elif 'market_value' not in security:  # Likely market value
                                                    security['market_value'] = cell_value
                                        
                                        securities.append(security)
        
        return {
            'bank_name': 'JP Morgan',
            'report_date': report_date,
            'account_number': account_number,
            'securities': securities
        }
    
    # Implementation for Interactive Brokers
    def _parse_interactive_brokers(self, pdf_file) -> Dict[str, Any]:
        """Parse Interactive Brokers statement."""
        securities = []
        report_date = None
        account_number = None
        
        with pdfplumber.open(pdf_file) as pdf:
            # Extract report date (typically at the top of the statement)
            first_page_text = pdf.pages[0].extract_text()
            date_match = re.search(r'Statement Period:\s+(\w+\s+\d{1,2},?\s+\d{4})\s+to\s+(\w+\s+\d{1,2},?\s+\d{4})', first_page_text)
            if date_match:
                report_date = date_match.group(2)  # Use the end date
            
            # Extract account number
            account_match = re.search(r'Account:\s+([A-Z0-9]+)', first_page_text)
            if account_match:
                account_number = account_match.group(1)
            
            # Interactive Brokers typically has a section labeled "Open Positions" or "Portfolio"
            position_pages = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if "Open Positions" in text or "Portfolio" in text or "POSITIONS" in text:
                    position_pages.append(i + 1)  # Store 1-based page numbers for tabula
            
            # Process position pages
            if position_pages:
                tables = tabula.read_pdf(
                    io.BytesIO(pdf.stream.get_data()),
                    pages=','.join(map(str, position_pages)),
                    multiple_tables=True
                )
                
                for table in tables:
                    # Interactive Brokers typically shows Symbol, Description, Quantity, Price, and Value
                    if len(table.columns) >= 5:
                        # Look for columns that might contain the relevant information
                        symbol_col = next((col for col in table.columns if any(s in str(col).lower() for s in ['symbol', 'ticker'])), None)
                        quantity_col = next((col for col in table.columns if any(s in str(col).lower() for s in ['quantity', 'position', 'size'])), None)
                        price_col = next((col for col in table.columns if any(s in str(col).lower() for s in ['price', 'mark'])), None)
                        value_col = next((col for col in table.columns if any(s in str(col).lower() for s in ['value', 'market value'])), None)
                        
                        # Process rows
                        for _, row in table.iterrows():
                            # Skip rows without a symbol
                            if symbol_col and pd.notna(row[symbol_col]) and str(row[symbol_col]).strip():
                                security = {
                                    'symbol': str(row[symbol_col]).strip(),
                                    'bank': 'Interactive Brokers'
                                }
                                
                                # Extract ISIN from description if present
                                # IB often includes ISIN in parentheses in the description
                                desc_col = next((col for col in table.columns if any(s in str(col).lower() for s in ['description', 'name'])), None)
                                if desc_col and pd.notna(row[desc_col]):
                                    security['security_name'] = str(row[desc_col]).strip()
                                    isin_match = re.search(r'\(([A-Z]{2}[A-Z0-9]{10})\)', str(row[desc_col]))
                                    if isin_match:
                                        security['isin'] = isin_match.group(1)
                                
                                # Extract other fields if present
                                if quantity_col and pd.notna(row[quantity_col]):
                                    try:
                                        security['quantity'] = float(str(row[quantity_col]).replace(',', ''))
                                    except ValueError:
                                        pass
                                
                                if price_col and pd.notna(row[price_col]):
                                    try:
                                        security['price'] = float(str(row[price_col]).replace(',', ''))
                                    except ValueError:
                                        pass
                                
                                if value_col and pd.notna(row[value_col]):
                                    try:
                                        security['market_value'] = float(str(row[value_col]).replace(',', ''))
                                    except ValueError:
                                        pass
                                
                                securities.append(security)
        
        return {
            'bank_name': 'Interactive Brokers',
            'report_date': report_date,
            'account_number': account_number,
            'securities': securities
        }
    
    # Implementation stubs for other institutions
    # You can implement these following the same pattern as JP Morgan and Interactive Brokers
    def _parse_goldman_sachs(self, pdf_file):
        """Parse Goldman Sachs statement."""
        # Implementation similar to JP Morgan but adapted for Goldman Sachs format
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Goldman Sachs',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_morgan_stanley(self, pdf_file):
        """Parse Morgan Stanley statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Morgan Stanley',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_credit_suisse(self, pdf_file):
        """Parse Credit Suisse statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Credit Suisse',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_ubs(self, pdf_file):
        """Parse UBS statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'UBS',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_deutsche_bank(self, pdf_file):
        """Parse Deutsche Bank statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Deutsche Bank',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_hsbc(self, pdf_file):
        """Parse HSBC statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'HSBC',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_barclays(self, pdf_file):
        """Parse Barclays statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Barclays',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_bnp_paribas(self, pdf_file):
        """Parse BNP Paribas statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'BNP Paribas',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_charles_schwab(self, pdf_file):
        """Parse Charles Schwab statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Charles Schwab',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_fidelity(self, pdf_file):
        """Parse Fidelity statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Fidelity',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_td_ameritrade(self, pdf_file):
        """Parse TD Ameritrade statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'TD Ameritrade',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_vanguard(self, pdf_file):
        """Parse Vanguard statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Vanguard',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_merrill_lynch(self, pdf_file):
        """Parse Merrill Lynch statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Merrill Lynch',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_etrade(self, pdf_file):
        """Parse E*TRADE statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'E*TRADE',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_robinhood(self, pdf_file):
        """Parse Robinhood statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Robinhood',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_santander(self, pdf_file):
        """Parse Santander statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Santander',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_ing(self, pdf_file):
        """Parse ING statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'ING',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_societe_generale(self, pdf_file):
        """Parse Societe Generale statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Societe Generale',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_unicredit(self, pdf_file):
        """Parse UniCredit statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'UniCredit',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_bbva(self, pdf_file):
        """Parse BBVA statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'BBVA',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_nomura(self, pdf_file):
        """Parse Nomura statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Nomura',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_mitsubishi_ufj(self, pdf_file):
        """Parse Mitsubishi UFJ statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Mitsubishi UFJ',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_icbc(self, pdf_file):
        """Parse ICBC statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'ICBC',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_dbs(self, pdf_file):
        """Parse DBS statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'DBS',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    # Israeli banks implementations (as previously shown)
    def _parse_bank_leumi(self, pdf_file) -> Dict[str, Any]:
        """Parse Bank Leumi statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Bank Leumi',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_bank_hapoalim(self, pdf_file) -> Dict[str, Any]:
        """Parse Bank Hapoalim statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Bank Hapoalim',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_bank_discount(self, pdf_file) -> Dict[str, Any]:
        """Parse Bank Discount statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Bank Discount',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_bank_mizrahi(self, pdf_file) -> Dict[str, Any]:
        """Parse Bank Mizrahi Tefahot statement."""
        securities = []
        # Implementation details...
        
        return {
            'bank_name': 'Bank Mizrahi Tefahot',
            'report_date': '01/01/2023',  # Replace with actual extraction
            'securities': securities
        }
    
    def _parse_generic(self, pdf_file) -> Dict[str, Any]:
        """Generic PDF parser - attempt to extract structured data."""
        securities = []
        report_date = None
        
        # Implementation of generic parser as shown previously
        # ...
        
        return {
            'bank_name': 'Unknown Institution',
            'report_date': report_date,
            'securities': securities
        }