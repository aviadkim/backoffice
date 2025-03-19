import pdfplumber
import io
import logging
import os
import tempfile
from typing import Tuple, List, Dict, Any, Union, BinaryIO, Optional, Callable
from dotenv import load_dotenv
import google.generativeai as genai
import pandas as pd
import tabula
import re

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str, start_page: int = 0, max_pages: Optional[int] = None) -> Tuple[List[Any], str]:
    """Extract text and tables from PDF file.
    
    Args:
        file_path: Path to PDF file
        start_page: Starting page number (0-based)
        max_pages: Maximum number of pages to process
        
    Returns:
        Tuple of (content, content_type) where:
        - content is list of extracted text/tables
        - content_type is 'text' or 'table'
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            content = []
            content_type = 'text'  # Default to text
            
            # Calculate page range
            total_pages = len(pdf.pages)
            if max_pages:
                end_page = min(start_page + max_pages, total_pages)
            else:
                end_page = total_pages
                
            for page_num in range(start_page, end_page):
                page = pdf.pages[page_num]
                
                # Try to extract tables first
                tables = page.extract_tables()
                if tables:
                    content.extend(tables)
                    content_type = 'table'
                else:
                    # If no tables, extract text
                    text = page.extract_text()
                    if text:
                        content.append(text)
                        
            return content, content_type
            
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}", exc_info=True)
        return [], 'error'

def extract_tables(pdf_path: str, pages: Optional[str] = 'all', 
                  progress_callback: Optional[Callable] = None) -> List[pd.DataFrame]:
    """
    Extract tables from PDF.
    
    Args:
        pdf_path: Path to PDF file
        pages: Pages to extract tables from ('all' or specific page numbers)
        progress_callback: Optional callback function for progress reporting
        
    Returns:
        List of extracted DataFrames
    """
    try:
        if progress_callback:
            progress_callback(0, 1, "Extracting tables from PDF")
            
        tables = tabula.read_pdf(pdf_path, pages=pages, multiple_tables=True)
        
        if progress_callback:
            progress_callback(1, 1, f"Extracted {len(tables)} tables")
            
        return tables
    except Exception as e:
        logger.error(f"Table extraction error: {str(e)}", exc_info=True)
        return []

def extract_transactions_from_text(text_results: Union[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Extract transaction data from text with improved pattern matching and error handling.
    
    Args:
        text_results: Text content as string or list of strings
        
    Returns:
        List of transaction dictionaries
    """
    try:
        if isinstance(text_results, str):
            text_results = [text_results]
            
        combined_text = "\n".join(text_results)
        cleaned_text = ' '.join(combined_text.split())  # Normalize whitespace
        
        # Enhanced pattern matching
        patterns = {
            'date': r'\b\d{1,2}[/\.-]\d{1,2}[/\.-]\d{2,4}\b',
            'amount': r'[-+]?[\d,]+\.?\d*',
            'isin': r'[A-Z]{2}[A-Z0-9]{10}',
            'quantity': r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:shares|units|יחידות|מניות)\b',
            'price': r'\$?\d+(?:,\d{3})*(?:\.\d+)?'
        }
        
        # Break text into logical segments
        segments = re.split(r'\n+|\r\n+', combined_text)
        
        transactions = []
        # Track unique identifiers to avoid duplicates
        seen_segments = set()
        
        for segment in segments:
            segment = segment.strip()
            if len(segment) < 5 or segment in seen_segments:  # Skip very short segments or duplicates
                continue
                
            seen_segments.add(segment)
            transaction = {'raw_text': segment}
            
            # Extract date
            date_matches = re.findall(patterns['date'], segment)
            if date_matches:
                transaction['date'] = date_matches[0]
                
                # Remove date from segment for cleaner description
                segment_without_date = re.sub(patterns['date'], '', segment).strip()
                
                # Extract amount (prefer last number as it's often the amount)
                amount_matches = re.findall(patterns['amount'], segment_without_date)
                if amount_matches:
                    try:
                        # Convert last match to float (usually the transaction amount)
                        amount_str = amount_matches[-1].replace(',', '')
                        amount = float(amount_str)
                        transaction['amount'] = amount
                        
                        # Remove amount from segment for description
                        segment_for_desc = segment_without_date.replace(amount_matches[-1], '').strip()
                        transaction['description'] = segment_for_desc
                        
                        # Basic category detection
                        transaction['category'] = "לא מסווג"  # Default category
                        if amount > 0:
                            transaction['category'] = "הכנסה"
                        elif any(kw in segment_for_desc.lower() for kw in ["שכר", "משכורת", "salary", "deposit"]):
                            transaction['category'] = "הכנסה"
                        elif any(kw in segment_for_desc.lower() for kw in ["שכירות", "דירה", "rent", "mortgage"]):
                            transaction['category'] = "דיור"
                        elif any(kw in segment_for_desc.lower() for kw in ["מזון", "סופר", "מסעדה", "food", "restaurant", "grocery"]):
                            transaction['category'] = "מזון"
                        
                        # Only add if we have date and amount at minimum
                        if 'date' in transaction and 'amount' in transaction:
                            transactions.append(transaction)
                    except ValueError:
                        # Skip if amount conversion fails
                        pass
        
        return transactions
    except Exception as e:
        logger.error(f"Error extracting transactions: {str(e)}", exc_info=True)
        return []

def process_image(image_path, lang='heb+eng'):
    """
    Process an image to extract text using OCR with improved error handling.
    
    Args:
        image_path: Path to image file
        lang: OCR language
        
    Returns:
        Extracted text
    """
    try:
        image = Image.open(image_path)
        img_np = np.array(image)
        
        # Convert if needed
        if len(img_np.shape) == 3 and img_np.shape[2] >= 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np  # Already grayscale
            
        # Try multiple preprocessing methods
        results = []
        
        # Method 1: OTSU thresholding
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        results.append(pytesseract.image_to_string(otsu, lang=lang))
        
        # Method 2: Adaptive thresholding
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        results.append(pytesseract.image_to_string(thresh, lang=lang))
        
        # Method 3: Original image
        results.append(pytesseract.image_to_string(gray, lang=lang))
        
        # Select best result based on length
        best_result = max(results, key=lambda x: len(x.strip()))
        return best_result
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        return f"Error processing image: {str(e)}"