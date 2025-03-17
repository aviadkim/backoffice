import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
import pandas as pd
import tabula
import cv2
import numpy as np
import io
import re  # Add missing import for regex
from PIL import Image
from typing import Tuple, List, Union, Dict, Any

def extract_text_from_pdf(pdf_path: str) -> Tuple[Union[List[str], List[pd.DataFrame]], str]:
    """Extract text or tables from PDF using OCR."""
    try:
        # First try pdfplumber for text extraction
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text_content = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
            
            if text_content:
                return text_content, 'text'
        
        # If pdfplumber fails, try OCR
        images = convert_from_path(pdf_path)
        ocr_text = []
        
        for img in images:
            # Improve image quality for OCR
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            # Apply adaptive thresholding
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
            if text.strip():
                ocr_text.append(text)
        
        return ocr_text if ocr_text else [], 'text'
        
    except Exception as e:
        print(f"Text extraction error: {e}")
        return [], 'error'

def extract_tables(pdf_path: str) -> List[pd.DataFrame]:
    """Extract tables from PDF."""
    import tabula
    try:
        return tabula.read_pdf(pdf_path, pages='all')
    except:
        return []

def extract_text(pdf_path: str) -> List[str]:
    """Extract text from PDF using OCR."""
    try:
        # Convert PDF to images
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path)
        
        texts = []
        for img in images:
            # Convert PIL image to OpenCV format
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # OCR the image
            text = pytesseract.image_to_string(img_cv, lang='eng+heb')
            texts.append(text)
            
        return texts
        
    except Exception as e:
        print(f"Text extraction error: {e}")
        return []

def extract_transactions_from_text(text_results: Union[str, List[str]]) -> List[Dict[str, Any]]:
    """Extract transaction data from text with improved pattern matching."""
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
    segments = re.split(r'\n+|\r\n+', cleaned_text)
    
    transactions = []
    for segment in segments:
        if len(segment.strip()) < 5:  # Skip very short segments
            continue
            
        transaction = {'raw_text': segment}
        
        # Extract structured data
        for field, pattern in patterns.items():
            matches = re.findall(pattern, segment, re.IGNORECASE)
            if matches:
                transaction[field] = matches[0]
        
        if transaction.keys() - {'raw_text'}:  # If we found any structured data
            transactions.append(transaction)
    
    return transactions

def process_image(image_path):
    """Maintain backward compatibility with existing code."""
    try:
        image = Image.open(image_path)
        img_np = np.array(image)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        text = pytesseract.image_to_string(thresh, lang='heb+eng')
        return text
    except Exception as e:
        return f"Error processing image: {str(e)}"
