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
        max_pages: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Process a financial document to extract data.
        
        Args:
            file_path_or_bytes: File path or bytes content of the file
            document_type: Type of document (statement, securities, etc.)
            max_pages: Maximum number of pages to process
            
        Returns:
            Tuple of (extracted data, result type)
        """
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
                return securities_data, 'securities'
            else:
                # Extract text and tables
                content, content_type = extract_text_from_pdf(
                    file_path,
                    max_pages=max_pages
                )
                
                if not content:
                    return [], 'error'
                
                return content, content_type
                    
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


# Initialize the integration for easy import
pdf_processor = PDFProcessingIntegration()