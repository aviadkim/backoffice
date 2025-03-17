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

def extract_text_from_pdf(pdf_path: str) -> list:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries containing extracted text and metadata
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            extracted_data = []
            
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Process text based on content
                    if 'Bank Statement' in text:
                        # Extract transactions and balance
                        transactions = []
                        balance = None
                        
                        for line in text.split('\n'):
                            # Try to find balance
                            balance_match = re.search(r'Balance:\s*\$(\d+(?:,\d+)?(?:\.\d+)?)', line)
                            if balance_match:
                                balance = float(balance_match.group(1).replace(',', ''))
                                
                            # Try to find transaction
                            date_match = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', line)
                            if date_match:
                                transaction = {'date': date_match.group(1)}
                                
                                # Try to find description
                                desc_match = re.search(r'Description:\s*(.+?)(?=Amount:|Balance:|$)', line)
                                if desc_match:
                                    transaction['description'] = desc_match.group(1).strip()
                                
                                # Try to find amount
                                amount_match = re.search(r'Amount:\s*\$([-]?\d+(?:,\d+)?(?:\.\d+)?)', line)
                                if amount_match:
                                    transaction['amount'] = float(amount_match.group(1).replace(',', ''))
                                
                                transactions.append(transaction)
                        
                        extracted_data.append({
                            'type': 'bank_statement',
                            'transactions': transactions,
                            'balance': balance
                        })
                        
                    elif 'Performance Report' in text:
                        # Extract performance data
                        performance_data = []
                        
                        for line in text.split('\n'):
                            period_match = re.search(r'Period:\s*(.+)', line)
                            if period_match:
                                period = {
                                    'period': period_match.group(1).strip()
                                }
                                
                                # Try to find return
                                return_match = re.search(r'Return:\s*([-]?\d+(?:\.\d+)?)', line)
                                if return_match:
                                    period['return'] = float(return_match.group(1))
                                
                                # Try to find annual return
                                annual_match = re.search(r'Annual Return:\s*([-]?\d+(?:\.\d+)?)', line)
                                if annual_match:
                                    period['annual_return'] = float(annual_match.group(1))
                                
                                performance_data.append(period)
                        
                        extracted_data.append({
                            'type': 'performance_report',
                            'periods': performance_data
                        })
                    
                    else:
                        # Generic text extraction
                        extracted_data.append({
                            'type': 'text',
                            'content': text
                        })
            
            return extracted_data
            
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}", exc_info=True)
        return []

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