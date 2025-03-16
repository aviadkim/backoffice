import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
import pandas as pd
import tabula
import cv2
import numpy as np
import io
from PIL import Image

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using OCR."""
    # First try tabula for table extraction
    try:
        tables = tabula.read_pdf(pdf_file, pages='all', multiple_tables=True)
        if tables and len(tables) > 0 and not all(df.empty for df in tables):
            return tables, "table"
    except Exception as e:
        print(f"Tabula extraction failed: {e}")
    
    # If tabula fails, use OCR
    try:
        images = convert_from_path(pdf_file) if isinstance(pdf_file, str) else convert_from_bytes(pdf_file.read())
        text_results = []
        
        for img in images:
            # Enhance image for better OCR
            img_np = np.array(img)
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            
            # OCR
            text = pytesseract.image_to_string(thresh, lang='heb+eng')  # Hebrew + English
            text_results.append(text)
            
        return text_results, "text"
    except Exception as e:
        print(f"OCR extraction failed: {e}")
        return [], "error"

def extract_transactions_from_text(text_results):
    """Extract transaction data from OCR text results."""
    transactions = []
    # Add pattern matching logic to identify dates, amounts, and descriptions
    import re
    
    # Patterns for Hebrew/English financial documents
    date_pattern = r'\d{1,2}[/\.-]\d{1,2}[/\.-]\d{2,4}'
    amount_pattern = r'[-+]?[\d,]+\.\d{2}'
    
    for text in text_results:
        lines = text.split('\n')
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Look for amount pattern first as it's most distinctive
            amount_match = re.search(amount_pattern, line)
            if amount_match:
                # Extract amount
                amount_str = amount_match.group(0).replace(',', '')
                amount = float(amount_str)
                
                # Look for date
                date_match = re.search(date_pattern, line)
                date_str = date_match.group(0) if date_match else ""
                
                # Extract description (text around the date and amount)
                description = line
                if date_match:
                    description = description.replace(date_match.group(0), '')
                if amount_match:
                    description = description.replace(amount_match.group(0), '')
                    
                description = description.strip()
                
                # Add to transactions
                transactions.append({
                    "date": date_str,
                    "description": description,
                    "amount": amount,
                    "category": "לא מסווג"  # Default category
                })
    
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
