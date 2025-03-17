import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
import pandas as pd
import tabula
import cv2
import numpy as np
import io
import re
from PIL import Image
from typing import Tuple, List, Union, Dict, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str, max_pages: Optional[int] = None, 
                         progress_callback: Optional[Callable] = None) -> Tuple[Union[List[str], List[pd.DataFrame]], str]:
    """
    Extract text or tables from PDF using OCR with support for chunked processing.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to process (None for all)
        progress_callback: Optional callback function for progress reporting
        
    Returns:
        Tuple of (extracted content, result type)
    """
    try:
        # First try pdfplumber for text extraction
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text_content = []
            
            # Limit pages if needed
            total_pages = len(pdf.pages)
            pages_to_process = min(total_pages, max_pages or total_pages)
            
            for page_idx, page in enumerate(pdf.pages[:pages_to_process]):
                if progress_callback:
                    progress_callback(page_idx, pages_to_process, f"Extracting text from page {page_idx+1}/{pages_to_process}")
                
                text = page.extract_text()
                if text:
                    text_content.append(text)
            
            if text_content:
                return text_content, 'text'
            
            if progress_callback:
                progress_callback(0, pages_to_process, "Text extraction failed, trying OCR")
        
        # If pdfplumber fails, try OCR
        images = convert_from_path(pdf_path, first_page=1, last_page=max_pages)
        ocr_text = []
        
        for img_idx, img in enumerate(images):
            if progress_callback:
                progress_callback(img_idx, len(images), f"Performing OCR on page {img_idx+1}/{len(images)}")
            
            # Improve image quality for OCR
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Apply different preprocessing techniques for better OCR
            # First try adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # OCR with improved settings
            text = pytesseract.image_to_string(
                thresh,
                lang='eng+heb',
                config='--psm 6 --oem 3'
            )
            
            # If text is too short, try different preprocessing
            if len(text.strip()) < 50:
                # Try Otsu's thresholding
                _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                text = pytesseract.image_to_string(
                    otsu,
                    lang='eng+heb',
                    config='--psm 6 --oem 3'
                )
            
            if text.strip():
                ocr_text.append(text)
        
        return ocr_text if ocr_text else [], 'text'
        
    except Exception as e:
        logger.error(f"Text extraction error: {str(e)}", exc_info=True)
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