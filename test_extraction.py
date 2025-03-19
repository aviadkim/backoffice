"""
סקריפט בדיקה לחילוץ נתונים מכל קבצי PDF בתיקיית uploads
"""

import os
import sys
import time
from utils.mistral_extractor import MistralExtractor

def main():
    # ספריית הקבצים לבדיקה
    uploads_dir = "uploads"
    
    # קבל את כל קבצי ה-PDF בספרייה
    pdf_files = [f for f in os.listdir(uploads_dir) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print("לא נמצאו קבצי PDF בתיקיית uploads")
        return
    
    print(f"נמצאו {len(pdf_files)} קבצי PDF לבדיקה")
    
    # יצירת אובייקט MistralExtractor
    extractor = MistralExtractor()
    
    # בדיקת כל אחד מהקבצים
    for i, pdf_file in enumerate(pdf_files):
        file_path = os.path.join(uploads_dir, pdf_file)
        print(f"\nבודק קובץ {i+1}/{len(pdf_files)}: {pdf_file}")
        
        try:
            # בדיקת הקובץ וחילוץ נתונים
            result = extractor.test_pdf_file(file_path)
            
            # בדיקה אם יש לפחות 20 אחזקות בכל הטבלאות
            total_holdings = len(result['financial_data']['holdings'])
            for table in result['tables']:
                if table.get('type') == 'holdings' and 'holdings' in table:
                    total_holdings += len(table['holdings'])
            
            if total_holdings >= 20:
                print(f"\n✅ הצלחה! נמצאו {total_holdings} אחזקות בקובץ {pdf_file}")
            else:
                print(f"\n❌ לא נמצאו מספיק אחזקות בקובץ {pdf_file} (רק {total_holdings})")
            
        except Exception as e:
            print(f"שגיאה בבדיקת הקובץ {pdf_file}: {str(e)}")
        
        # המתנה קצרה בין קבצים
        if i < len(pdf_files) - 1:
            print("ממתין 2 שניות לפני הקובץ הבא...")
            time.sleep(2)
    
    print("\nבדיקת כל הקבצים הסתיימה")

if __name__ == "__main__":
    main() 