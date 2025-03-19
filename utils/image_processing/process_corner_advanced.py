import cv2
import numpy as np
import easyocr
import os
import json
import pytesseract
from PIL import Image

def segment_by_text_regions(image):
    """
    מבצע סגמנטציה של אזורי טקסט בתמונה באמצעות MSER
    """
    # המרה לגווני אפור אם צריך
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # שימוש ב-MSER לאיתור אזורי טקסט פוטנציאליים
    mser = cv2.MSER_create()
    regions, _ = mser.detectRegions(gray)
    
    # יצירת מסכה ריקה בגודל התמונה
    mask = np.zeros(gray.shape, dtype=np.uint8)
    
    # מילוי המסכה באזורים שנמצאו
    for region in regions:
        region = region.reshape(-1, 1, 2)
        cv2.fillPoly(mask, [region], (255))
    
    # הפעלת מורפולוגיה לחיבור אזורים סמוכים
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    
    # מציאת קונטורים באזורים המחוברים
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # יצירת עותק של התמונה המקורית
    result = image.copy() if len(image.shape) == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    # סינון קונטורים קטנים מדי
    filtered_contours = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        aspect_ratio = w / float(h) if h > 0 else 0
        
        # סינון לפי גודל ויחס צד
        if area > 100 and (aspect_ratio > 0.1 and aspect_ratio < 10):
            filtered_contours.append(contour)
    
    # ציור הקונטורים ויצירת חלקי תמונה לזיהוי
    text_regions = []
    for i, contour in enumerate(filtered_contours):
        x, y, w, h = cv2.boundingRect(contour)
        # הוספת שוליים לאזור
        padding = 5
        x_start = max(0, x - padding)
        y_start = max(0, y - padding)
        x_end = min(image.shape[1], x + w + padding)
        y_end = min(image.shape[0], y + h + padding)
        
        # חיתוך האזור מהתמונה המקורית
        region_img = gray[y_start:y_end, x_start:x_end]
        
        # הוספת האזור לרשימה
        text_regions.append({
            "id": i,
            "bbox": (x_start, y_start, x_end, y_end),
            "image": region_img
        })
        
        # ציור מלבן סביב האזור
        cv2.rectangle(result, (x_start, y_start), (x_end, y_end), (0, 255, 0), 2)
        cv2.putText(result, str(i), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    return result, text_regions

def apply_advanced_preprocessing(image):
    """
    מיישם מספר שיטות עיבוד מתקדמות על התמונה
    """
    results = {}
    
    # המרה לגווני אפור
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # 1. שיטת Sauvola - סף אדפטיבי מקומי לבינריזציה
    # מכיוון ש-OpenCV לא מיישם ישירות את Sauvola, נשתמש בגישה דומה
    window_size = 25
    k = 0.2
    # חישוב ממוצע וסטיית תקן מקומיים
    mean = cv2.boxFilter(gray, -1, (window_size, window_size), 
                        borderType=cv2.BORDER_REFLECT)
    mean_sq = cv2.boxFilter(gray**2, -1, (window_size, window_size), 
                           borderType=cv2.BORDER_REFLECT)
    variance = mean_sq - mean**2
    std_dev = np.sqrt(np.maximum(variance, 0))
    
    # חישוב הסף של Sauvola
    threshold = mean * (1 + k * ((std_dev / 128) - 1))
    sauvola = np.zeros_like(gray)
    sauvola[gray > threshold] = 255
    results["sauvola"] = sauvola.astype(np.uint8)
    
    # 2. שיפור חדות באמצעות Unsharp Mask
    blurred = cv2.GaussianBlur(gray, (0, 0), 3)
    unsharp_mask = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
    results["unsharp_mask"] = unsharp_mask
    
    # 3. סינון נויזס בייסיאני
    denoise = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    results["denoise"] = denoise
    
    # 4. התאמת היסטוגרמה עם CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    clahe_img = clahe.apply(gray)
    results["clahe"] = clahe_img
    
    # 5. שילוב: CLAHE + Otsu
    blur = cv2.GaussianBlur(clahe_img, (5, 5), 0)
    _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results["clahe_otsu"] = otsu
    
    # 6. שילוב: CLAHE + Denoise + Otsu
    blur_denoise = cv2.GaussianBlur(cv2.fastNlMeansDenoising(clahe_img, None, h=10), (5, 5), 0)
    _, denoise_otsu = cv2.threshold(blur_denoise, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results["clahe_denoise_otsu"] = denoise_otsu
    
    # 7. שיטת מורפולוגיה - TopHat לשיפור טקסט
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
    results["tophat"] = tophat
    
    # 8. שיפור ניגודיות והשוואת היסטוגרמה
    enhanced = cv2.equalizeHist(gray)
    results["equalized"] = enhanced
    
    return results

def extract_text_from_regions(regions, reader, output_dir):
    """
    מחלץ טקסט מאזורים שנמצאו בתמונה
    """
    results = {}
    
    for region in regions:
        region_id = region["id"]
        region_img = region["image"]
        
        # שמירת תמונת האזור
        region_path = os.path.join(output_dir, f"region_{region_id}.png")
        cv2.imwrite(region_path, region_img)
        
        # זיהוי טקסט באמצעות EasyOCR
        ocr_results = reader.readtext(region_img)
        ocr_text = " ".join([text for _, text, _ in ocr_results])
        
        # זיהוי טקסט באמצעות Tesseract
        try:
            pil_img = Image.fromarray(region_img)
            tesseract_text = pytesseract.image_to_string(pil_img, lang='eng')
        except Exception as e:
            tesseract_text = f"Error: {str(e)}"
        
        results[region_id] = {
            "bbox": region["bbox"],
            "easyocr": {
                "text": ocr_text,
                "confidence": np.mean([conf for _, _, conf in ocr_results]) if ocr_results else 0,
                "details": [{"text": text, "confidence": conf} for _, text, conf in ocr_results]
            },
            "tesseract": {
                "text": tesseract_text
            }
        }
    
    return results

def extract_text_with_multiple_engines(image, output_dir, filename_prefix):
    """
    מחלץ טקסט מתמונה באמצעות מספר מנועי OCR
    """
    # המרה של התמונה למערך numpy אם היא לא כבר
    if not isinstance(image, np.ndarray):
        image = np.array(image)
    
    # המרה לגווני אפור אם צריך
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # שמירת התמונה המקורית
    original_path = os.path.join(output_dir, f"{filename_prefix}_original.png")
    cv2.imwrite(original_path, gray)
    
    # הפעלת Tesseract על התמונה המקורית
    try:
        pil_img = Image.fromarray(gray)
        tesseract_text = pytesseract.image_to_string(pil_img, lang='eng')
    except Exception as e:
        tesseract_text = f"Error: {str(e)}"
    
    # שמירת הטקסט מ-Tesseract
    with open(os.path.join(output_dir, f"{filename_prefix}_tesseract.txt"), "w", encoding="utf-8") as f:
        f.write(tesseract_text)
    
    # אתחול קורא EasyOCR
    reader = easyocr.Reader(['en'])
    
    # הפעלת EasyOCR על התמונה המקורית
    easyocr_results = reader.readtext(gray)
    easyocr_text = " ".join([text for _, text, _ in easyocr_results])
    
    # שמירת הטקסט מ-EasyOCR
    with open(os.path.join(output_dir, f"{filename_prefix}_easyocr.txt"), "w", encoding="utf-8") as f:
        f.write(easyocr_text)
    
    # סימון התוצאות על התמונה
    visualized = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    for bbox, text, conf in easyocr_results:
        points = np.array(bbox).astype(np.int32)
        cv2.polylines(visualized, [points], True, (0, 255, 0), 2)
        x, y = points[0][0], points[0][1] - 10
        cv2.putText(visualized, f"{text} ({conf:.2f})", (x, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # שמירת התמונה עם התוצאות
    result_path = os.path.join(output_dir, f"{filename_prefix}_results.png")
    cv2.imwrite(result_path, visualized)
    
    return {
        "tesseract": {
            "text": tesseract_text
        },
        "easyocr": {
            "text": easyocr_text,
            "segments": len(easyocr_results),
            "confidence": np.mean([conf for _, _, conf in easyocr_results]) if easyocr_results else 0,
            "details": [{"text": text, "confidence": conf} for _, text, conf in easyocr_results]
        }
    }

def main():
    # יצירת תיקייה לתוצאות
    output_dir = "corner_advanced_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # טעינת התמונה
    image_path = "uploads/corner.png"
    image = cv2.imread(image_path)
    if image is None:
        print(f"שגיאה: לא ניתן לטעון את התמונה {image_path}")
        return
    
    print("1. מבצע סגמנטציה של אזורי טקסט...")
    # ביצוע סגמנטציה של אזורי טקסט
    segmented_image, text_regions = segment_by_text_regions(image)
    cv2.imwrite(os.path.join(output_dir, "text_regions.png"), segmented_image)
    
    print(f"נמצאו {len(text_regions)} אזורי טקסט פוטנציאליים")
    
    print("2. מחלץ טקסט מכל אזור...")
    # אתחול קורא EasyOCR
    reader = easyocr.Reader(['en'])
    
    # חילוץ טקסט מהאזורים
    region_results = extract_text_from_regions(text_regions, reader, output_dir)
    
    print("3. שומר תוצאות מהאזורים...")
    # שמירת תוצאות האזורים
    with open(os.path.join(output_dir, "region_results.json"), "w", encoding="utf-8") as f:
        json_serializable_results = {}
        for region_id, result in region_results.items():
            json_serializable_results[str(region_id)] = {
                "bbox": result["bbox"],
                "easyocr": {
                    "text": result["easyocr"]["text"],
                    "confidence": float(result["easyocr"]["confidence"]),
                    "details": [
                        {"text": detail["text"], "confidence": float(detail["confidence"])}
                        for detail in result["easyocr"]["details"]
                    ]
                },
                "tesseract": {
                    "text": result["tesseract"]["text"]
                }
            }
        json.dump(json_serializable_results, f, indent=2, ensure_ascii=False)
    
    print("4. מיישם שיטות עיבוד מתקדמות...")
    # יישום שיטות עיבוד מתקדמות
    advanced_results = apply_advanced_preprocessing(image)
    
    print("5. מבצע OCR על כל תמונה מעובדת...")
    all_texts = {}
    
    # חילוץ טקסט מכל תמונה מעובדת
    for method_name, processed_image in advanced_results.items():
        print(f"  מעבד תמונה: {method_name}")
        
        # שמירת התמונה המעובדת
        processed_path = os.path.join(output_dir, f"{method_name}.png")
        cv2.imwrite(processed_path, processed_image)
        
        # חילוץ טקסט
        ocr_results = extract_text_with_multiple_engines(processed_image, output_dir, method_name)
        
        all_texts[method_name] = ocr_results
    
    print("6. שומר תוצאות סופיות...")
    # שמירת כל התוצאות לקובץ JSON
    with open(os.path.join(output_dir, "advanced_results.json"), "w", encoding="utf-8") as f:
        json_serializable_results = {}
        for method_name, result in all_texts.items():
            json_serializable_results[method_name] = {
                "tesseract": {
                    "text": result["tesseract"]["text"]
                },
                "easyocr": {
                    "text": result["easyocr"]["text"],
                    "segments": result["easyocr"]["segments"],
                    "confidence": float(result["easyocr"]["confidence"]),
                    "details": [
                        {"text": detail["text"], "confidence": float(detail["confidence"])}
                        for detail in result["easyocr"]["details"]
                    ]
                }
            }
        json.dump(json_serializable_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nהעיבוד המתקדם הסתיים. התוצאות נשמרו בתיקייה {output_dir}")
    
    # איסוף כל הטקסט לקובץ אחד
    all_extracted_text = []
    all_extracted_text.append("=== טקסט שחולץ מאזורים ===")
    for region_id, result in sorted(region_results.items(), key=lambda x: int(x[0])):
        all_extracted_text.append(f"אזור {region_id}:")
        all_extracted_text.append(f"EasyOCR: {result['easyocr']['text']}")
        all_extracted_text.append(f"Tesseract: {result['tesseract']['text']}")
        all_extracted_text.append("-" * 40)
    
    all_extracted_text.append("\n=== טקסט שחולץ משיטות עיבוד שונות ===")
    for method_name, result in all_texts.items():
        all_extracted_text.append(f"שיטה: {method_name}")
        all_extracted_text.append(f"EasyOCR: {result['easyocr']['text']}")
        all_extracted_text.append(f"Tesseract: {result['tesseract']['text']}")
        all_extracted_text.append("-" * 40)
    
    # שמירת כל הטקסט לקובץ אחד
    with open(os.path.join(output_dir, "all_extracted_text.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(all_extracted_text))

if __name__ == "__main__":
    main() 