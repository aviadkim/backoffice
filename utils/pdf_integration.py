import os
import tempfile
import logging
import pandas as pd
from typing import Tuple, List, Dict, Any, Union, BinaryIO, Optional, Callable
from utils.ocr_processor import extract_text_from_pdf, extract_transactions_from_text
from utils.securities_pdf_processor import SecuritiesPDFProcessor

logger = logging.getLogger(__name__)

class PDFProcessingIntegration:
    """Integration class for various PDF processing functionalities in FinAnalyzer."""
    
    def __init__(self):
        self.securities_processor = SecuritiesPDFProcessor()
    
    def process_financial_document(self, file_path_or_bytes, document_type=None, max_pages=None, callback=None):
        """Process a financial document to extract data."""
        # Create temp file if needed
        temp_path = None
        if not isinstance(file_path_or_bytes, str):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                if isinstance(file_path_or_bytes, bytes):
                    tmp_file.write(file_path_or_bytes)
                else:
                    tmp_file.write(file_path_or_bytes.read())
                temp_path = tmp_file.name
            file_path = temp_path
        else:
            file_path = file_path_or_bytes
        
        try:
            # Get total pages to calculate progress
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                if callback:
                    callback(0, total_pages, "Initialized PDF processing")
            
            # Process based on document type
            if document_type == 'securities':
                securities_data = self.securities_processor.process_pdf(
                    file_path, 
                    max_pages=max_pages,
                    progress_callback=callback
                )
                return securities_data, 'securities'
            else:
                # Default to regular financial document processing
                extracted_results, result_type = extract_text_from_pdf(
                    file_path, 
                    max_pages=max_pages,
                    progress_callback=callback
                )
                
                if callback:
                    callback(total_pages, total_pages, "Extraction completed, processing results")
                
                if result_type == 'text':
                    # Extract transactions from text
                    transactions = extract_transactions_from_text(extracted_results)
                    return transactions, 'transactions'
                elif result_type == 'table':
                    # Process as tables
                    transactions = []
                    for i, table in enumerate(extracted_results):
                        if callback and len(extracted_results) > 1:
                            callback(i, len(extracted_results), f"Processing table {i+1}/{len(extracted_results)}")
                            
                        for _, row in table.iterrows():
                            if len(row) >= 3:
                                transaction = {
                                    'date': row.iloc[0] if pd.notna(row.iloc[0]) else '',
                                    'description': row.iloc[1] if pd.notna(row.iloc[1]) else '',
                                    'amount': float(row.iloc[2]) if pd.notna(row.iloc[2]) else 0,
                                    'category': 'לא מסווג'
                                }
                                transactions.append(transaction)
                    return transactions, 'transactions'
                else:
                    logger.warning(f"Extraction failed for {file_path}")
                    return [], 'error'
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            return [], 'error'
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except:
                    pass

    def auto_detect_document_type(self, file_path_or_bytes: Union[str, bytes, BinaryIO], filename: Optional[str] = None) -> str:
        """Automatically detect document type."""
        if filename:
            filename_lower = filename.lower()
            if any(kw in filename_lower for kw in ['securities', 'portfolio', 'holdings', 'positions', 'ניירות ערך', 'אחזקות', 'תיק השקעות']):
                return 'securities'
            if any(kw in filename_lower for kw in ['statement', 'account', 'transaction', 'bank', 'credit', 'דף חשבון', 'כרטיס אשראי']):
                return 'statement'

        temp_path = None
        try:
            if not isinstance(file_path_or_bytes, str):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    if isinstance(file_path_or_bytes, bytes):
                        tmp_file.write(file_path_or_bytes)
                    else:
                        tmp_file.write(file_path_or_bytes.read())
                    temp_path = tmp_file.name
                file_path = temp_path
            else:
                file_path = file_path_or_bytes

            extracted_results, _ = extract_text_from_pdf(file_path, max_pages=1)
            
            if extracted_results:
                first_page_text = extracted_results[0].lower() if isinstance(extracted_results, list) else str(extracted_results).lower()
                
                if any(kw in first_page_text for kw in ['securities', 'portfolio', 'holdings', 'positions', 'investment', 'ניירות ערך', 'אחזקות', 'תיק השקעות', 'isin']):
                    return 'securities'
                if any(kw in first_page_text for kw in ['transaction', 'statement', 'account', 'balance', 'credit', 'debit', 'עסקאות', 'דף חשבון', 'יתרה', 'זכות', 'חובה']):
                    return 'statement'

            return 'statement'  # Default
        except Exception as e:
            logger.error(f"Error detecting document type: {str(e)}")
            return 'statement'  # Default on error
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except:
                    pass

    def process_document_in_chunks(self, file_path_or_bytes, chunk_size=5, document_type=None, callback=None):
        """Process a large document in chunks."""
        import pdfplumber
        
        temp_path = None
        try:
            if not isinstance(file_path_or_bytes, str):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    if isinstance(file_path_or_bytes, bytes):
                        tmp_file.write(file_path_or_bytes)
                    else:
                        tmp_file.write(file_path_or_bytes.read())
                    temp_path = tmp_file.name
                file_path = temp_path
            else:
                file_path = file_path_or_bytes
        
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                if total_pages <= chunk_size:
                    return self.process_financial_document(file_path, document_type, callback=callback)
                
                if callback:
                    callback(0, total_pages, "Starting chunked processing")
                
                if not document_type:
                    document_type = self.auto_detect_document_type(file_path)
                
                all_results = []
                result_type = None
                
                for start_page in range(1, total_pages + 1, chunk_size):
                    end_page = min(start_page + chunk_size - 1, total_pages)
                    
                    if callback:
                        callback(start_page - 1, total_pages, f"Processing pages {start_page}-{end_page}")
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as chunk_file:
                        chunk_path = chunk_file.name
                    
                    try:
                        from PyPDF2 import PdfReader, PdfWriter
                        reader = PdfReader(file_path)
                        writer = PdfWriter()
                        
                        for page_num in range(start_page - 1, end_page):
                            writer.add_page(reader.pages[page_num])
                        
                        with open(chunk_path, 'wb') as out_file:
                            writer.write(out_file)
                        
                        chunk_results, chunk_type = self.process_financial_document(
                            chunk_path, 
                            document_type,
                            callback=None
                        )
                        
                        if not result_type:
                            result_type = chunk_type
                        
                        if chunk_type == result_type and chunk_results:
                            all_results.extend(chunk_results)
                    finally:
                        try:
                            os.unlink(chunk_path)
                        except:
                            pass
                
                if callback:
                    callback(total_pages, total_pages, "Completed chunked processing")
                
                return all_results, result_type
                
        except Exception as e:
            logger.error(f"Error in chunked processing: {str(e)}", exc_info=True)
            return [], 'error'
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except:
                    pass

# Initialize the integration for easy import
pdf_processor = PDFProcessingIntegration()