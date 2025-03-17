import os
import tempfile
import logging
import pandas as pd
from utils.ocr_processor import extract_text_from_pdf, extract_transactions_from_text
from utils.securities_pdf_processor import SecuritiesPDFProcessor

logger = logging.getLogger(__name__)

class PDFProcessingIntegration:
    """Integration class for various PDF processing functionalities in FinAnalyzer."""
    
    def __init__(self):
        self.securities_processor = SecuritiesPDFProcessor()
    
    def process_financial_document(self, file_path_or_bytes, document_type=None):
        """
        Process a financial document to extract data based on document type.
        
        Args:
            file_path_or_bytes: File path or bytes content of the file
            document_type: Type of document (statement, securities, etc.)
            
        Returns:
            Extracted data, type of data (transactions, securities)
        """
        # Create temp file if needed
        temp_path = None
        if not isinstance(file_path_or_bytes, str):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(file_path_or_bytes)
                temp_path = tmp_file.name
            file_path = temp_path
        else:
            file_path = file_path_or_bytes
        
        try:
            if document_type == 'securities':
                # Process securities document
                securities_data = self.securities_processor.process_pdf(file_path)
                return securities_data, 'securities'
            else:
                # Default to regular financial document processing
                extracted_results, result_type = extract_text_from_pdf(file_path)
                
                if result_type == 'text':
                    # Extract transactions from text
                    transactions = extract_transactions_from_text(extracted_results)
                    return transactions, 'transactions'
                elif result_type == 'table':
                    # Process as tables (e.g., CSV-like tables from PDF)
                    # This might need custom handling based on your needs
                    transactions = []
                    for table in extracted_results:
                        # Convert table to transactions based on structure
                        # This is simplified and should be adapted to your actual format
                        for _, row in table.iterrows():
                            if len(row) >= 3:  # Minimum columns for transaction
                                transaction = {
                                    'date': row.iloc[0] if pd.notna(row.iloc[0]) else '',
                                    'description': row.iloc[1] if pd.notna(row.iloc[1]) else '',
                                    'amount': float(row.iloc[2]) if pd.notna(row.iloc[2]) else 0,
                                    'category': 'לא מסווג'
                                }
                                transactions.append(transaction)
                    
                    return transactions, 'transactions'
                else:
                    # Return empty results if extraction failed
                    return [], 'error'
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return [], 'error'
        finally:
            # Clean up temp file if it was created
            if temp_path:
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def auto_detect_document_type(self, file_path_or_bytes, filename=None):
        """
        Automatically detect the type of financial document.
        
        Args:
            file_path_or_bytes: File path or bytes content of the file
            filename: Original filename if available
            
        Returns:
            Document type (securities, statement, etc.)
        """
        # Try to determine from filename first
        if filename:
            filename_lower = filename.lower()
            if any(kw in filename_lower for kw in ['securities', 'portfolio', 'holdings', 'positions', 'ניירות ערך', 'אחזקות', 'תיק השקעות']):
                return 'securities'
            if any(kw in filename_lower for kw in ['statement', 'account', 'transaction', 'bank', 'credit', 'דף חשבון', 'כרטיס אשראי']):
                return 'statement'
        
        # If couldn't determine from filename, try to analyze content
        # Create temp file if needed
        temp_path = None
        if not isinstance(file_path_or_bytes, str):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(file_path_or_bytes)
                temp_path = tmp_file.name
            file_path = temp_path
        else:
            file_path = file_path_or_bytes
            
        try:
            # Extract first page text
            extracted_results, _ = extract_text_from_pdf(file_path)
            
            if extracted_results:
                first_page_text = extracted_results[0].lower() if isinstance(extracted_results, list) else str(extracted_results).lower()
                
                # Check for securities-related keywords
                if any(kw in first_page_text for kw in ['securities', 'portfolio', 'holdings', 'positions', 'investment', 'ניירות ערך', 'אחזקות', 'תיק השקעות', 'isin']):
                    return 'securities'
                
                # Check for transaction-related keywords
                if any(kw in first_page_text for kw in ['transaction', 'statement', 'account', 'balance', 'credit', 'debit', 'עסקאות', 'דף חשבון', 'יתרה', 'זכות', 'חובה']):
                    return 'statement'
            
            # Default to statement if couldn't determine
            return 'statement'
        except Exception as e:
            logger.error(f"Error detecting document type: {str(e)}")
            return 'statement'  # Default to statement
        finally:
            # Clean up temp file if it was created
            if temp_path:
                try:
                    os.unlink(temp_path)
                except:
                    pass

# Initialize the integration for easy import
pdf_processor = PDFProcessingIntegration()