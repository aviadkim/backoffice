import os
import tempfile
import logging
import pandas as pd
from typing import Tuple, List, Dict, Any, Union, BinaryIO, Optional, Callable
from utils.ocr_processor import extract_text_from_pdf
from utils.securities_pdf_processor import SecuritiesPDFProcessor

logger = logging.getLogger(__name__)

class PDFProcessingIntegration:
    """Integration class for various PDF processing functionalities."""
    
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
            callback: Progress callback function
            
        Returns:
            Tuple of (extracted data, result type)
        """
        if callback:
            callback(0, 1, "Starting document processing")
        
        # Create temp file if needed
        temp_path = None
        file_path = self._prepare_file_path(file_path_or_bytes)
        
        try:
            # Process based on document type
            if document_type == 'securities':
                securities_data = self.securities_processor.process_pdf(
                    file_path,
                    max_pages=max_pages
                )
                result_type = 'securities'
            else:
                # Extract text and tables
                content, content_type = extract_text_from_pdf(
                    file_path,
                    max_pages=max_pages
                )
                
                if not content:
                    return [], 'error'
                
                if any(keyword in str(content).lower() for keyword in ['transaction', 'payment', 'deposit', 'withdrawal']):
                    result_type = 'transactions'
                else:
                    result_type = content_type
                
                securities_data = content
            
            if callback:
                callback(1, 1, f"Completed processing {document_type} document")
                
            return securities_data, result_type
                    
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            if callback:
                callback(1, 1, f"Error processing document: {str(e)}")
            return [], 'error'
        
        finally:
            # Cleanup temp file if created
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def _prepare_file_path(self, file_path_or_bytes: Union[str, bytes, BinaryIO]) -> str:
        """Prepare file path for processing."""
        if isinstance(file_path_or_bytes, str):
            return file_path_or_bytes
        elif isinstance(file_path_or_bytes, bytes):
            # Create temp file
            temp_path = tempfile.mktemp(suffix='.pdf')
            with open(temp_path, 'wb') as f:
                f.write(file_path_or_bytes)
            return temp_path
        else:
            # Handle file-like object
            temp_path = tempfile.mktemp(suffix='.pdf')
            with open(temp_path, 'wb') as f:
                f.write(file_path_or_bytes.read())
            return temp_path
    
    def _get_total_pages(self, file_path: str) -> int:
        """Get total number of pages in PDF."""
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                return len(pdf.pages)
        except:
            return 0
    
    def _process_tables(self, tables: List[pd.DataFrame]) -> List[Dict[str, Any]]:
        """Process extracted tables."""
        results = []
        
        for table in tables:
            if isinstance(table, pd.DataFrame):
                # Convert table to list of dictionaries
                results.extend(table.to_dict('records'))
        
        return results
    
    def _process_text(self, text_content: List[str]) -> List[Dict[str, Any]]:
        """Process extracted text."""
        results = []
        
        for text in text_content:
            # Use Gemini to extract information
            import google.generativeai as genai
            from dotenv import load_dotenv
            import os
            import json
            
            load_dotenv()
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            
            # Create model
            model = genai.GenerativeModel('gemini-pro')
            
            # Create prompt
            prompt = f"""
            Extract financial information from the following text.
            Identify:
            - Date
            - Description
            - Amount
            - Category (if possible)
            
            Text:
            {text}
            
            Return the results as a JSON array of objects with these fields.
            """
            
            # Get response
            response = model.generate_content(prompt)
            
            # Parse response
            try:
                data = json.loads(response.text)
                results.extend(data)
            except:
                continue
        
        return results

    def process_document_in_chunks(
        self,
        file_path_or_bytes: Union[str, bytes, BinaryIO],
        chunk_size: int = 5,
        document_type: Optional[str] = None,
        callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Process a large document in chunks to manage memory usage.
        
        Args:
            file_path_or_bytes: File path or bytes content
            chunk_size: Number of pages to process in each chunk
            document_type: Type of document (statement, securities, etc.)
            callback: Progress callback function
            
        Returns:
            Tuple of (extracted data, result type)
        """
        if callback:
            callback(0, 1, "Starting chunked processing")
        
        file_path = self._prepare_file_path(file_path_or_bytes)
        total_pages = self._get_total_pages(file_path)
        
        if callback:
            callback(0, total_pages, "Starting document processing")
            
        all_results = []
        current_page = 0
        
        try:
            while current_page < total_pages:
                end_page = min(current_page + chunk_size, total_pages)
                
                if callback:
                    callback(current_page, total_pages, f"Processing pages {current_page+1} to {end_page}")
                
                # Process chunk
                if document_type == 'securities':
                    chunk_results = self.securities_processor.process_pdf(
                        file_path,
                        max_pages=chunk_size,
                        start_page=current_page
                    )
                    result_type = 'securities'
                else:
                    # Extract text and tables from chunk
                    content, content_type = extract_text_from_pdf(
                        file_path,
                        max_pages=chunk_size,
                        start_page=current_page
                    )
                    
                    if content:
                        if content_type == 'table':
                            chunk_results = self._process_tables(content)
                        else:
                            chunk_results = self._process_text(content)
                        result_type = 'transactions'
                    else:
                        chunk_results = []
                        result_type = 'error'
                
                all_results.extend(chunk_results)
                current_page += chunk_size
                
            if callback:
                callback(total_pages, total_pages, "Processing complete")
                
            return all_results, result_type
            
        except Exception as e:
            logger.error(f"Error in chunked processing: {str(e)}", exc_info=True)
            if callback:
                callback(1, 1, f"Error in chunked processing: {str(e)}")
            return [], 'error'
        
        finally:
            # Cleanup temp file if created
            if isinstance(file_path_or_bytes, (bytes, BinaryIO)) and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except:
                    pass

    def auto_detect_document_type(self, file_path_or_bytes: Union[str, bytes, BinaryIO], filename: str = None) -> str:
        """
        Auto-detect the type of document based on content and filename.
        
        Args:
            file_path_or_bytes: File path or content
            filename: Original filename (optional)
            
        Returns:
            Detected document type ('securities' or 'statement')
        """
        # Check filename first if provided
        if filename:
            filename_lower = filename.lower()
            if any(term in filename_lower for term in ['securities', 'portfolio', 'holdings', 'positions']):
                return 'securities'
            elif any(term in filename_lower for term in ['statement', 'transaction', 'account']):
                return 'statement'
        
        # Check content
        file_path = self._prepare_file_path(file_path_or_bytes)
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) > 0:
                    text = pdf.pages[0].extract_text().lower()
                    
                    # Check for securities-related terms
                    securities_terms = ['portfolio', 'securities', 'holdings', 'positions', 
                                     'stocks', 'bonds', 'investments', 'shares']
                    if any(term in text for term in securities_terms):
                        return 'securities'
                    
                    # Check for statement-related terms
                    statement_terms = ['account statement', 'transaction', 'balance', 
                                     'withdrawal', 'deposit', 'credit', 'debit']
                    if any(term in text for term in statement_terms):
                        return 'statement'
            
            # Default to statement if uncertain
            return 'statement'
            
        finally:
            # Cleanup temp file if created
            if isinstance(file_path_or_bytes, (bytes, BinaryIO)) and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except:
                    pass


# Initialize the integration for easy import
pdf_processor = PDFProcessingIntegration()