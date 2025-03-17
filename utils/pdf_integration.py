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
    
    def __init__(self) -> None:
        """Initialize the PDF processing integration with required processors."""
        self.securities_processor = SecuritiesPDFProcessor()
    
    def process_financial_document(
        self,
        file_path_or_bytes: Union[str, bytes, BinaryIO],
        document_type: Optional[str] = None,
        max_pages: Optional[int] = None,
        callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Process a financial document to extract data.
        
        Args:
            file_path_or_bytes: File path or bytes content of the file
            document_type: Type of document (statement, securities, etc.)
            max_pages: Maximum number of pages to process
            callback: Optional progress callback function
            
        Returns:
            Tuple of (extracted data, result type)
        """
        # Create temp file if needed
        temp_path = None
        file_path = self._prepare_file_path(file_path_or_bytes)
        
        try:
            # Get total pages to calculate progress
            total_pages = self._get_total_pages(file_path)
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
                transactions = self._process_table_results(extracted_results, callback)
                return transactions, 'transactions'
            else:
                logger.warning(f"Extraction failed for {file_path}")
                return [], 'error'
        except FileNotFoundError as e:
            logger.error(f"File not found error: {str(e)}", exc_info=True)
            return [], 'error'
        except PermissionError as e:
            logger.error(f"Permission error accessing file: {str(e)}", exc_info=True)
            return [], 'error'
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            return [], 'error'
        finally:
            self._cleanup_temp_file(temp_path)

    def _prepare_file_path(self, file_path_or_bytes: Union[str, bytes, BinaryIO]) -> str:
        """
        Prepare the file path, creating a temp file if needed.
        
        Args:
            file_path_or_bytes: Input file path or content
            
        Returns:
            Path to the file to process
        """
        if isinstance(file_path_or_bytes, str):
            return file_path_or_bytes
            
        # Create temp file
        temp_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            if isinstance(file_path_or_bytes, bytes):
                tmp_file.write(file_path_or_bytes)
            else:
                tmp_file.write(file_path_or_bytes.read())
            temp_path = tmp_file.name
        
        return temp_path
    
    def _get_total_pages(self, file_path: str) -> int:
        """
        Get the total number of pages in a PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Number of pages
        """
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            return len(pdf.pages)
    
    def _process_table_results(
        self, 
        tables: List[pd.DataFrame],
        callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process extracted tables into transactions.
        
        Args:
            tables: List of DataFrames representing tables
            callback: Optional progress callback
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        for i, table in enumerate(tables):
            if callback and len(tables) > 1:
                callback(i, len(tables), f"Processing table {i+1}/{len(tables)}")
                
            for _, row in table.iterrows():
                if len(row) >= 3:
                    transaction = {
                        'date': row.iloc[0] if pd.notna(row.iloc[0]) else '',
                        'description': row.iloc[1] if pd.notna(row.iloc[1]) else '',
                        'amount': float(row.iloc[2]) if pd.notna(row.iloc[2]) else 0,
                        'category': 'לא מסווג'
                    }
                    transactions.append(transaction)
        return transactions
    
    def _cleanup_temp_file(self, temp_path: Optional[str]) -> None:
        """
        Clean up a temporary file if it exists.
        
        Args:
            temp_path: Path to the temporary file
        """
        if temp_path:
            try:
                os.unlink(temp_path)
            except (OSError, PermissionError) as e:
                logger.warning(f"Failed to remove temp file {temp_path}: {str(e)}")

    def auto_detect_document_type(
        self, 
        file_path_or_bytes: Union[str, bytes, BinaryIO],
        filename: Optional[str] = None
    ) -> str:
        """
        Automatically detect the type of financial document.
        
        Args:
            file_path_or_bytes: File path or bytes content
            filename: Original filename if available
            
        Returns:
            Document type (securities, statement, etc.)
        """
        # Try to determine from filename first
        if filename:
            doc_type = self._detect_type_from_filename(filename)
            if doc_type:
                return doc_type

        # If couldn't determine from filename, analyze content
        temp_path = None
        file_path = self._prepare_file_path(file_path_or_bytes)
        temp_path = None if file_path == file_path_or_bytes else file_path
        
        try:
            doc_type = self._detect_type_from_content(file_path)
            return doc_type
        except Exception as e:
            logger.error(f"Error detecting document type: {str(e)}")
            return 'statement'  # Default to statement
        finally:
            self._cleanup_temp_file(temp_path)
    
    def _detect_type_from_filename(self, filename: str) -> Optional[str]:
        """
        Detect document type from filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            Document type or None if couldn't determine
        """
        filename_lower = filename.lower()
        securities_keywords = [
            'securities', 'portfolio', 'holdings', 'positions', 
            'ניירות ערך', 'אחזקות', 'תיק השקעות'
        ]
        statement_keywords = [
            'statement', 'account', 'transaction', 'bank', 'credit', 
            'דף חשבון', 'כרטיס אשראי'
        ]
        
        if any(kw in filename_lower for kw in securities_keywords):
            return 'securities'
        if any(kw in filename_lower for kw in statement_keywords):
            return 'statement'
        
        return None
    
    def _detect_type_from_content(self, file_path: str) -> str:
        """
        Detect document type from content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Document type
        """
        extracted_results, _ = extract_text_from_pdf(file_path, max_pages=1)
        
        if not extracted_results:
            return 'statement'  # Default if no text extracted
            
        text = extracted_results[0].lower() if isinstance(extracted_results, list) else str(extracted_results).lower()
        
        securities_keywords = [
            'securities', 'portfolio', 'holdings', 'positions', 'investment',
            'ניירות ערך', 'אחזקות', 'תיק השקעות', 'isin'
        ]
        statement_keywords = [
            'transaction', 'statement', 'account', 'balance', 'credit', 'debit',
            'עסקאות', 'דף חשבון', 'יתרה', 'זכות', 'חובה'
        ]
        
        if any(kw in text for kw in securities_keywords):
            return 'securities'
        if any(kw in text for kw in statement_keywords):
            return 'statement'
            
        return 'statement'  # Default if no keywords matched

    def process_document_in_chunks(
        self,
        file_path_or_bytes: Union[str, bytes, BinaryIO],
        chunk_size: int = 5,
        document_type: Optional[str] = None,
        callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Process a large document in chunks to avoid memory issues.
        
        Args:
            file_path_or_bytes: File path or bytes content
            chunk_size: Number of pages to process at once
            document_type: Type of document to process
            callback: Progress callback function
            
        Returns:
            Combined results, result type
        """
        # Prepare file path
        file_path = self._prepare_file_path(file_path_or_bytes)
        temp_path = None if file_path == file_path_or_bytes else file_path
        
        try:
            # Get total pages
            total_pages = self._get_total_pages(file_path)
            
            # For small documents, process normally
            if total_pages <= chunk_size:
                return self.process_financial_document(file_path, document_type, callback=callback)
            
            if callback:
                callback(0, total_pages, "Starting chunked processing")
            
            # Auto-detect document type if needed
            if not document_type:
                document_type = self.auto_detect_document_type(file_path)
            
            # Process in chunks
            all_results = []
            result_type = None
            
            for start_page in range(1, total_pages + 1, chunk_size):
                end_page = min(start_page + chunk_size - 1, total_pages)
                
                if callback:
                    callback(start_page - 1, total_pages, f"Processing pages {start_page}-{end_page}")
                
                # Process this chunk
                chunk_results, chunk_type = self._process_page_chunk(
                    file_path, start_page, end_page, document_type
                )
                
                # Track result type and combine results
                if not result_type:
                    result_type = chunk_type
                
                if chunk_type == result_type and chunk_results:
                    all_results.extend(chunk_results)
            
            if callback:
                callback(total_pages, total_pages, "Completed chunked processing")
            
            return all_results, result_type or 'error'
                
        except Exception as e:
            logger.error(f"Error in chunked processing: {str(e)}", exc_info=True)
            return [], 'error'
        finally:
            self._cleanup_temp_file(temp_path)
    
    def _process_page_chunk(
        self, 
        file_path: str, 
        start_page: int, 
        end_page: int, 
        document_type: str
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Process a specific chunk of pages from a PDF.
        
        Args:
            file_path: Path to the PDF file
            start_page: Starting page number (1-based)
            end_page: Ending page number (inclusive)
            document_type: Type of document
            
        Returns:
            Results from this chunk, result type
        """
        # Create a temporary PDF with just these pages
        chunk_path = None
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as chunk_file:
                chunk_path = chunk_file.name
            
            # Extract pages to new file
            from PyPDF2 import PdfReader, PdfWriter
            reader = PdfReader(file_path)
            writer = PdfWriter()
            
            for page_num in range(start_page - 1, end_page):
                writer.add_page(reader.pages[page_num])
            
            with open(chunk_path, 'wb') as out_file:
                writer.write(out_file)
            
            # Process this chunk
            return self.process_financial_document(
                chunk_path, 
                document_type,
                callback=None  # No callback for chunks
            )
        except Exception as e:
            logger.error(f"Error processing page chunk {start_page}-{end_page}: {str(e)}")
            return [], 'error'
        finally:
            # Remove chunk file
            self._cleanup_temp_file(chunk_path)


# Initialize the integration for easy importpdf_processor = PDFProcessingIntegration()