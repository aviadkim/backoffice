import cv2
import easyocr
import os
import re

# יצירת תיקייה לתוצאות
results_dir = "ocr_results"
os.makedirs(results_dir, exist_ok=True)

# טעינת התמונות המעובדות
image_files = {
    "original": "extracted_data/images/mes 28/page_3.png",
    "binary": "simple_binary.png",
    "adaptive": "simple_adaptive.png",
    "otsu": "simple_otsu.png"
}

# אתחול מנוע EasyOCR
reader = easyocr.Reader(['en'])

# עיבוד כל תמונה
for name, image_path in image_files.items():
    print(f"\nProcessing {name} image...")
    
    # טעינת התמונה
    image = cv2.imread(image_path)
    if image is None:
        print(f"Could not load image: {image_path}")
        continue
    
    # OCR עם EasyOCR
    results = reader.readtext(image)
    print(f"Found {len(results)} text segments")
    
    # יצירת קובץ טקסט עם כל התוצאות
    all_text = ""
    for bbox, text, prob in results:
        all_text += text + " "
    
    # שמירת הטקסט לקובץ
    text_file = os.path.join(results_dir, f"{name}_text.txt")
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(all_text)
    
    # חיפוש דפוסים שנראים כמו ISINs
    # ISIN הוא 12 תווים: 2 אותיות של המדינה ו-10 ספרות/אותיות
    isin_pattern = r'\b[A-Z]{2}[A-Z0-9]{10}\b'
    
    # גם חיפוש כללי יותר - סדרות של לפחות 8 אותיות/ספרות
    potential_pattern = r'\b[A-Z0-9]{8,}\b'
    
    isins = []
    potentials = []
    
    # חיפוש בטקסט המלא
    isins = re.findall(isin_pattern, all_text)
    
    # חיפוש דפוסים דומים ל-ISIN
    for _, text, prob in results:
        if re.search(potential_pattern, text) and not re.search(isin_pattern, text):
            if any(c.isdigit() for c in text) and any(c.isupper() for c in text):
                potentials.append((text, prob))
    
    # הדפסת התוצאות
    if isins:
        print(f"Found {len(isins)} ISINs:")
        for isin in isins:
            print(f"  {isin}")
    else:
        print("No ISINs found")
    
    if potentials:
        print(f"Found {len(potentials)} potential ISINs:")
        for text, prob in potentials:
            print(f"  '{text}' (confidence: {prob:.2f})")
    
    # גם נשמור את כל המקטעים המזוהים בקובץ JSON
    import json
    json_file = os.path.join(results_dir, f"{name}_results.json")
    
    json_results = []
    for bbox, text, prob in results:
        json_results.append({
            "text": text,
            "confidence": prob,
            "is_potential_isin": re.search(potential_pattern, text) is not None
        })
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_results, f, indent=2)

print("\nProcessing complete. Check the 'ocr_results' directory for results.") 