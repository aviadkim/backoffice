import os
import cv2
import easyocr
import numpy as np
import json
from datetime import datetime
import pytesseract
import re

# פונקציות עזר לעיבוד תמונה
def preprocess_image_with_method(image, method='adaptive'):
    """
    מעבד תמונה עם מספר שיטות שונות
    
    Args:
        image: תמונה כמערך numpy
        method: שיטת העיבוד ('adaptive', 'otsu', 'binary', 'none')
    
    Returns:
        התמונה המעובדת
    """
    # המרה לגריי אם צריך
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # שיפור ניגודיות עם CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    if method == 'none':
        return enhanced
    
    if method == 'adaptive':
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
    elif method == 'otsu':
        # Otsu's thresholding
        blur = cv2.GaussianBlur(enhanced, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == 'binary':
        # Binary thresholding
        _, thresh = cv2.threshold(enhanced, 127, 255, cv2.THRESH_BINARY)
    
    # הורדת רעש
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
    
    return denoised

def extract_text_with_easyocr(image, method='adaptive'):
    """
    מוציא טקסט מתמונה עם EasyOCR
    
    Args:
        image: תמונה כמערך numpy
        method: שיטת עיבוד מוקדם
    
    Returns:
        הטקסט המוצא
    """
    # עיבוד מוקדם
    processed_image = preprocess_image_with_method(image, method)
    
    # שמירת התמונה המעובדת לצורך דיבוג
    debug_dir = os.path.join("extracted_data", "debug")
    os.makedirs(debug_dir, exist_ok=True)
    method_timestamp = f"{method}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    cv2.imwrite(os.path.join(debug_dir, f"processed_{method_timestamp}.png"), processed_image)
    
    # OCR עם EasyOCR
    reader = easyocr.Reader(['en'])
    results = reader.readtext(processed_image)
    
    # מיזוג התוצאות
    text = ""
    for (bbox, text_result, prob) in results:
        # נוסיף מידע על המיקום בתמונה
        text += f"{text_result} "
    
    print(f"EasyOCR + {method}: זוהו {len(results)} מקטעי טקסט")
    return text.strip()

def extract_securities_from_text(text):
    """
    מוציא מידע על ניירות ערך מהטקסט
    
    Args:
        text: הטקסט לבדיקה
    
    Returns:
        רשימת ניירות ערך שנמצאו
    """
    # תבנית ISIN (12 תווים אלפאנומריים)
    isin_pattern = r'\b[A-Z0-9]{12}\b'
    
    # חיפוש כל התאמות ל-ISIN
    isin_matches = re.findall(isin_pattern, text)
    
    # ביטויים סדירים למידע נוסף
    # חיפוש תבניות כמו "USD 50,000" או דומה
    amount_pattern = r'\b(USD|EUR|GBP|CHF|JPY|CAD)\s*[0-9,.]+\b'
    
    # חיפוש תבניות אחוזים כמו "5.65%" או "5,65%"
    percentage_pattern = r'\b\d+[.,]\d+\s*%\b'
    
    # חיפוש תבניות תאריכים
    date_pattern = r'\b\d{2}[./-]\d{2}[./-]\d{2,4}\b'
    
    # חילוץ סכומים, אחוזים ותאריכים
    amounts = re.findall(amount_pattern, text)
    percentages = re.findall(percentage_pattern, text)
    dates = re.findall(date_pattern, text)
    
    # יצירת ניירות ערך מהתאמות ה-ISIN
    securities = []
    for isin in isin_matches:
        securities.append({"isin": isin})
    
    # הוספת סיכום של מידע אחר שנמצא
    summary = {
        "amounts": amounts,
        "percentages": percentages,
        "dates": dates
    }
    
    return securities, summary

def main():
    # נתיב לתמונת העמוד
    page_image_path = "extracted_data/images/mes 28/page_3.png"
    
    # טעינת התמונה
    image = cv2.imread(page_image_path)
    if image is None:
        print(f"שגיאה: לא ניתן לטעון את התמונה {page_image_path}")
        return
    
    # עיבוד עם מספר שיטות
    methods = ['adaptive', 'otsu', 'binary', 'none']
    best_results = {"method": None, "text": "", "securities": []}
    
    for method in methods:
        print(f"\nמעבד עם שיטה: {method}")
        
        # OCR עם EasyOCR
        text = extract_text_with_easyocr(image, method)
        print(f"אורך הטקסט: {len(text)}")
        print(f"תחילת הטקסט: {text[:100]}...")
        
        # חיפוש ניירות ערך
        securities, summary = extract_securities_from_text(text)
        print(f"נמצאו {len(securities)} ניירות ערך")
        print(f"סכומים: {summary['amounts'][:5]}...")
        print(f"אחוזים: {summary['percentages'][:5]}...")
        print(f"תאריכים: {summary['dates'][:5]}...")
        
        # שמירת התוצאות הטובות ביותר (לפי מספר ניירות הערך שנמצאו)
        if len(securities) > len(best_results["securities"]):
            best_results = {
                "method": method,
                "text": text,
                "securities": securities,
                "summary": summary
            }
    
    # שמירת התוצאות הטובות ביותר לקובץ
    results_dir = "extracted_data/single_page_results"
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(results_dir, f"page_3_results_{timestamp}.json")
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "best_method": best_results["method"],
            "text": best_results["text"],
            "securities": best_results["securities"],
            "summary": best_results["summary"]
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nהתוצאות הטובות ביותר (שיטה: {best_results['method']}):")
    print(f"נשמרו לקובץ: {results_file}")
    print(f"נמצאו {len(best_results['securities'])} ניירות ערך")
    
    # גם שמירת הטקסט לקובץ טקסט
    text_file = os.path.join(results_dir, f"page_3_text_{timestamp}.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(best_results["text"])
    
    print(f"הטקסט נשמר לקובץ: {text_file}")

if __name__ == "__main__":
    main() 