import cv2
import easyocr
import os
import re
import numpy as np
from PIL import Image
import json
from datetime import datetime

def preprocess_image(image, method='adaptive'):
    """
    מעבד תמונה בשיטות שונות לשיפור זיהוי OCR
    """
    # המרה לאפור אם צריך
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # שיפור ניגודיות עם CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    if method == 'adaptive':
        # סף מסתגל - עובד טוב לתמונות עם תאורה לא אחידה
        processed = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
    elif method == 'otsu':
        # סף אוטסו - עובד טוב כאשר יש הבדל ברור בין הטקסט לרקע
        blur = cv2.GaussianBlur(enhanced, (5, 5), 0)
        _, processed = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == 'binary':
        # סף פשוט
        _, processed = cv2.threshold(enhanced, 127, 255, cv2.THRESH_BINARY)
    elif method == 'none':
        # ללא עיבוד נוסף, רק שיפור ניגודיות
        processed = enhanced
    else:
        processed = enhanced
    
    return processed

def find_table_regions(image):
    """
    מנסה לזהות אזורים בתמונה שנראים כמו טבלאות
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # זיהוי קווים אופקיים ואנכיים - עשוי לעזור לזהות טבלאות
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
    
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    
    # שילוב הקווים האופקיים והאנכיים
    table_mask = cv2.bitwise_or(horizontal_lines, vertical_lines)
    
    # זיהוי קונטורים - אלה עשויים להיות תאים בטבלה
    contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # סינון קונטורים קטנים
    min_area = 500
    table_regions = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > min_area:
            x, y, w, h = cv2.boundingRect(contour)
            table_regions.append((int(x), int(y), int(w), int(h)))
    
    return table_regions, table_mask

def extract_isins_from_text(text):
    """
    מחפש מספרי ISIN בטקסט
    מספר ISIN הוא רצף של 12 תווים המורכב מאותיות וספרות
    בדרך כלל מתחיל ב-2 אותיות של קוד המדינה
    """
    # תבנית בסיסית ל-ISIN
    isin_pattern = r'\b[A-Z]{2}[A-Z0-9]{10}\b'
    
    # חיפוש תבניות דומות ל-ISIN (במקרה שהזיהוי לא מושלם)
    potential_isin_pattern = r'\b[A-Z0-9]{10,14}\b'
    
    isins = re.findall(isin_pattern, text)
    potential_isins = []
    
    for word in text.split():
        if len(word) >= 10 and len(word) <= 14 and any(c.isdigit() for c in word) and any(c.isupper() for c in word):
            if word not in isins and re.match(potential_isin_pattern, word):
                potential_isins.append(word)
    
    return isins, potential_isins

def numpy_to_json_serializable(obj):
    """
    המרת מערכים של NumPy לפורמט שניתן להמיר ל-JSON
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, list):
        return [numpy_to_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(numpy_to_json_serializable(item) for item in obj)
    elif isinstance(obj, dict):
        return {k: numpy_to_json_serializable(v) for k, v in obj.items()}
    else:
        return obj

def main():
    # יצירת תיקיות לתוצאות
    output_dir = "page9_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # טעינת תמונת עמוד 9
    image_path = "extracted_data/images/mes 28/page_9.png"
    image = cv2.imread(image_path)
    if image is None:
        print(f"Could not load image: {image_path}")
        return
    
    # זיהוי אזורי טבלאות
    table_regions, table_mask = find_table_regions(image)
    cv2.imwrite(os.path.join(output_dir, "table_mask.png"), table_mask)
    
    # מסגור האזורים שזוהו כטבלאות
    table_image = image.copy()
    for x, y, w, h in table_regions:
        cv2.rectangle(table_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.imwrite(os.path.join(output_dir, "table_regions.png"), table_image)
    
    print(f"זוהו {len(table_regions)} אזורי טבלאות פוטנציאליים")
    
    # עיבוד העמוד בשיטות שונות
    methods = ['none', 'adaptive', 'otsu', 'binary']
    all_results = {}
    
    # אתחול מנוע EasyOCR
    reader = easyocr.Reader(['en'])
    
    for method in methods:
        print(f"\nמעבד את העמוד בשיטה: {method}")
        processed = preprocess_image(image, method)
        
        # שמירת התמונה המעובדת
        cv2.imwrite(os.path.join(output_dir, f"processed_{method}.png"), processed)
        
        # OCR על כל התמונה
        results = reader.readtext(processed)
        
        # שמירת התוצאות
        all_text = " ".join([text for _, text, _ in results])
        isins, potential_isins = extract_isins_from_text(all_text)
        
        print(f"נמצאו {len(isins)} מספרי ISIN ודאיים ו-{len(potential_isins)} מספרים פוטנציאליים")
        
        if isins:
            print("מספרי ISIN שזוהו:")
            for isin in isins:
                print(f"- {isin}")
        
        if potential_isins:
            print("מספרים פוטנציאליים שעשויים להיות ISIN:")
            for potential in potential_isins:
                print(f"- {potential}")
        
        # מסומנים במיוחד אזורי טקסט משמעותיים שעשויים להכיל נתונים על ניירות ערך
        securities_image = image.copy()
        for bbox, text, prob in results:
            if (any(isin in text for isin in isins) or 
                any(potential in text for potential in potential_isins) or
                'security' in text.lower() or 
                'securities' in text.lower() or
                'bond' in text.lower() or
                'stock' in text.lower() or
                'fund' in text.lower()):
                
                # המרה ל-integers כדי למנוע בעיות בציור
                box_points = [[int(p[0]), int(p[1])] for p in bbox]
                box = np.array(box_points).reshape((-1, 1, 2))
                cv2.polylines(securities_image, [box], True, (0, 0, 255), 2)
                
                # הוספת הטקסט שזוהה מעל התיבה
                x, y = box_points[0]
                cv2.putText(securities_image, text, (x, y-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        cv2.imwrite(os.path.join(output_dir, f"securities_{method}.png"), securities_image)
        
        # שמירת הטקסט המלא
        with open(os.path.join(output_dir, f"text_{method}.txt"), "w", encoding="utf-8") as f:
            f.write(all_text)
        
        # המרת הנתונים לפורמט שניתן להמיר ל-JSON
        json_ready_results = []
        for bbox, text, prob in results:
            json_ready_results.append({
                "bbox": numpy_to_json_serializable(bbox),
                "text": text,
                "confidence": float(prob)  # וידוא שהביטחון הוא float רגיל
            })
        
        # שמירת תוצאות מפורטות
        with open(os.path.join(output_dir, f"results_{method}.json"), "w", encoding="utf-8") as f:
            json_results = {
                "method": method,
                "text_segments": json_ready_results,
                "isins": isins,
                "potential_isins": potential_isins,
                "total_segments": len(results)
            }
            json.dump(json_results, f, indent=2)
        
        all_results[method] = {
            "isins": isins,
            "potential_isins": potential_isins,
            "text_segments_count": len(results)
        }
    
    # שמירת סיכום של כל השיטות
    with open(os.path.join(output_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    
    print("\nעיבוד הושלם. התוצאות נשמרו בתיקייה:", output_dir)

if __name__ == "__main__":
    main() 