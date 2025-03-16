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
    # This will depend on the structure of your financial documents
    
    # Example simple pattern (very basic, would need refinement):
    import re
    date_pattern = r'\d{1,2}/\d{1,2}/\d{2,4}'
    amount_pattern = r'[-+]?\d+[.,]\d{2}'
    
    for text in text_results:
        lines = text.split('\n')
        for line in lines:
            if re.search(amount_pattern, line):
                # Basic parsing - would need to be customized for your documents
                date = re.search(date_pattern, line)
                amount = re.search(amount_pattern, line)
                if date and amount:
                    date_str = date.group(0)
                    amount_str = amount.group(0).replace(',', '')
                    
                    # Extract description (everything between date and amount)
                    description = line.replace(date_str, '').replace(amount_str, '').strip()
                    
                    transactions.append({
                        "date": date_str,
                        "description": description,
                        "amount": float(amount_str.replace(',', '.')),
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
