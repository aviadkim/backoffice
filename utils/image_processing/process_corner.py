import cv2
import numpy as np
import easyocr
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt

def apply_preprocessing(image, method, params=None):
    """
    מיישם שיטות עיבוד מקדים שונות על התמונה
    
    Args:
        image: מערך תמונה
        method: שיטת העיבוד
        params: פרמטרים ספציפיים לשיטת העיבוד
    
    Returns:
        התמונה המעובדת
    """
    if params is None:
        params = {}
    
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    if method == 'original':
        return gray
    
    elif method == 'enhanced_contrast':
        clahe = cv2.createCLAHE(clipLimit=params.get('clip_limit', 2.0), 
                               tileGridSize=params.get('tile_grid_size', (8, 8)))
        return clahe.apply(gray)
    
    elif method == 'adaptive_threshold':
        enhanced = apply_preprocessing(image, 'enhanced_contrast')
        block_size = params.get('block_size', 11)
        c = params.get('c', 2)
        return cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                    cv2.THRESH_BINARY, block_size, c)
    
    elif method == 'otsu_threshold':
        enhanced = apply_preprocessing(image, 'enhanced_contrast')
        blur = cv2.GaussianBlur(enhanced, params.get('blur_kernel', (5, 5)), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh
    
    elif method == 'dilate':
        # שימוש בפעולת dilate כדי להרחיב את הטקסט - יכול לעזור עם טקסט מקוטע
        kernel_size = params.get('kernel_size', (2, 2))
        iterations = params.get('iterations', 1)
        kernel = np.ones(kernel_size, np.uint8)
        
        # תחילה מיישמים סף אדפטיבי או אוטסו
        base_method = params.get('base_method', 'adaptive_threshold')
        base_img = apply_preprocessing(image, base_method)
        
        return cv2.dilate(base_img, kernel, iterations=iterations)
    
    elif method == 'erode':
        # שימוש בפעולת erode כדי לצמצם את הטקסט - יכול לעזור עם טקסט שנמרח
        kernel_size = params.get('kernel_size', (2, 2))
        iterations = params.get('iterations', 1)
        kernel = np.ones(kernel_size, np.uint8)
        
        # תחילה מיישמים סף אדפטיבי או אוטסו
        base_method = params.get('base_method', 'adaptive_threshold')
        base_img = apply_preprocessing(image, base_method)
        
        return cv2.erode(base_img, kernel, iterations=iterations)
    
    elif method == 'denoise':
        # שימוש בפילטר הפחתת רעש
        h = params.get('h', 10)
        return cv2.fastNlMeansDenoising(gray, None, h=h, templateWindowSize=7, searchWindowSize=21)
    
    elif method == 'sharpen':
        # שימוש בפילטר חידוד על התמונה המקורית לשיפור הפרטים
        kernel = np.array([[-1, -1, -1],
                           [-1,  9, -1],
                           [-1, -1, -1]])
        return cv2.filter2D(gray, -1, kernel)
    
    elif method == 'canny_edges':
        # שימוש בגילוי שפות Canny - לפעמים עוזר לזיהוי טקסט
        low = params.get('low_threshold', 100)
        high = params.get('high_threshold', 200)
        edges = cv2.Canny(gray, low, high)
        # המרה לתמונה בינארית (שחור-לבן) לשימוש ב-OCR
        return cv2.threshold(edges, 0, 255, cv2.THRESH_BINARY)[1]
    
    elif method == 'gamma_correction':
        # תיקון גמא יכול לעזור עם תמונות בהירות או כהות מדי
        gamma = params.get('gamma', 1.5)
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(gray, table)
    
    # ברירת מחדל להחזרת התמונה המקורית
    return gray

def extract_text_with_easyocr(image, reader, languages=['en']):
    """
    מחלץ טקסט מתמונה עם EasyOCR
    
    Args:
        image: התמונה
        reader: מופע קורא EasyOCR
        languages: שפות לזיהוי
    
    Returns:
        מילון עם הטקסט המוצא ומידע נוסף
    """
    # הפעלת ה-OCR על התמונה
    results = reader.readtext(image)
    
    # מיזוג התוצאות לטקסט אחד
    all_text = " ".join([text for _, text, _ in results])
    
    # החזרת תוצאה עם מידע נוסף
    return {
        "text": all_text,
        "segments": len(results),
        "confidence": np.mean([conf for _, _, conf in results]) if results else 0,
        "details": [{"text": text, "confidence": conf, "bbox": box} for box, text, conf in results]
    }

def enhance_image_for_display(image, method):
    """
    שיפור התמונה לתצוגה
    """
    if method in ['original', 'enhanced_contrast', 'sharpen', 'denoise', 'gamma_correction']:
        # אלה תמונות בגווני אפור רגילים
        processed = image
    else:
        # אלה תמונות בינאריות (שחור-לבן), לכן נמיר אותן לתמונות בגווני אפור
        processed = image
    
    # מתיחת היסטוגרמה לשיפור הניגודיות לצורכי תצוגה
    if len(processed.shape) == 2:  # אם התמונה בגווני אפור
        equalized = cv2.equalizeHist(processed)
        return equalized
    else:
        return processed

def save_results_with_text_overlay(image, ocr_results, output_path):
    """
    שומר את התמונה עם הטקסט שזוהה ממוקם בתוכה
    """
    # יצירת עותק של התמונה
    visualized = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image.copy()
    
    # ציור תיבות סביב הטקסט שזוהה
    for item in ocr_results["details"]:
        bbox = item["bbox"]
        text = item["text"]
        confidence = item["confidence"]
        
        # המרה למערך numpy ולמספרים שלמים
        points = np.array(bbox).astype(np.int32)
        
        # ציור הקו
        cv2.polylines(visualized, [points], True, (0, 255, 0), 2)
        
        # מיקום לטקסט (בתחתית המלבן)
        x, y = points[0][0], points[0][1] - 10 if points[0][1] > 20 else points[0][1] + 20
        
        # הוספת הטקסט
        cv2.putText(visualized, f"{text} ({confidence:.2f})", (x, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # שמירת התמונה
    cv2.imwrite(output_path, visualized)

def main():
    # יצירת תיקייה לתוצאות
    output_dir = "corner_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # טעינת התמונה
    image_path = "uploads/corner.png"
    image = cv2.imread(image_path)
    if image is None:
        print(f"שגיאה: לא ניתן לטעון את התמונה {image_path}")
        return
    
    # הגדרת שיטות העיבוד לניסוי
    processing_methods = [
        ("original", {}),
        ("enhanced_contrast", {"clip_limit": 2.0, "tile_grid_size": (8, 8)}),
        ("adaptive_threshold", {"block_size": 11, "c": 2}),
        ("adaptive_threshold", {"block_size": 21, "c": 2}),
        ("otsu_threshold", {}),
        ("dilate", {"base_method": "adaptive_threshold", "kernel_size": (2, 2), "iterations": 1}),
        ("erode", {"base_method": "adaptive_threshold", "kernel_size": (2, 2), "iterations": 1}),
        ("denoise", {"h": 10}),
        ("sharpen", {}),
        ("gamma_correction", {"gamma": 1.5}),
        ("gamma_correction", {"gamma": 0.7})
    ]
    
    # אתחול קורא EasyOCR
    reader = easyocr.Reader(['en'])
    
    # עיבוד התמונה בכל שיטה וחילוץ הטקסט
    all_results = {}
    best_result = {"method": "", "params": {}, "text": "", "segments": 0, "confidence": 0}
    
    for method, params in processing_methods:
        method_name = f"{method}"
        if params:
            for key, value in params.items():
                if key not in ["base_method"]:  # לא כולל פרמטרים של שיטות בסיס
                    method_name += f"_{key}_{value}"
        
        print(f"\nמעבד את התמונה בשיטה: {method_name}")
        
        # עיבוד התמונה
        processed = apply_preprocessing(image, method, params)
        
        # שמירת התמונה המעובדת
        processed_path = os.path.join(output_dir, f"{method_name}.png")
        cv2.imwrite(processed_path, processed)
        
        # שיפור התמונה לתצוגה ושמירה
        enhanced = enhance_image_for_display(processed, method)
        enhanced_path = os.path.join(output_dir, f"{method_name}_enhanced.png")
        cv2.imwrite(enhanced_path, enhanced)
        
        # חילוץ טקסט
        ocr_results = extract_text_with_easyocr(processed, reader)
        
        # שמירת התמונה עם הטקסט שזוהה מסומן עליה
        visualized_path = os.path.join(output_dir, f"{method_name}_with_text.png")
        save_results_with_text_overlay(enhanced, ocr_results, visualized_path)
        
        # הדפסת סיכום התוצאות
        print(f"נמצאו {ocr_results['segments']} מקטעי טקסט עם ביטחון ממוצע {ocr_results['confidence']:.2f}")
        print(f"הטקסט שזוהה: {ocr_results['text']}")
        
        # שמירת התוצאות
        all_results[method_name] = {
            "method": method,
            "params": params,
            "text": ocr_results["text"],
            "segments": ocr_results["segments"],
            "confidence": ocr_results["confidence"],
            "details": ocr_results["details"]
        }
        
        # בדיקה אם זו התוצאה הטובה ביותר עד כה (לפי אורך הטקסט וביטחון)
        if ocr_results["segments"] > best_result["segments"] or (
            ocr_results["segments"] == best_result["segments"] and 
            ocr_results["confidence"] > best_result["confidence"]
        ):
            best_result = {
                "method": method,
                "params": params,
                "text": ocr_results["text"],
                "segments": ocr_results["segments"],
                "confidence": ocr_results["confidence"]
            }
    
    # שמירת כל התוצאות לקובץ JSON
    with open(os.path.join(output_dir, "all_results.json"), "w", encoding="utf-8") as f:
        # המרת מערכים numpy לרשימות Python רגילות
        json_serializable_results = {}
        for method, result in all_results.items():
            json_serializable_results[method] = {
                "method": result["method"],
                "params": result["params"],
                "text": result["text"],
                "segments": result["segments"],
                "confidence": float(result["confidence"]),
                "details": [
                    {
                        "text": detail["text"],
                        "confidence": float(detail["confidence"]),
                        "bbox": [[float(x), float(y)] for x, y in detail["bbox"]]
                    }
                    for detail in result["details"]
                ]
            }
        json.dump(json_serializable_results, f, indent=2, ensure_ascii=False)
    
    # הדפסת התוצאה הטובה ביותר
    print("\nהתוצאה הטובה ביותר:")
    print(f"שיטה: {best_result['method']} עם פרמטרים {best_result['params']}")
    print(f"מספר מקטעים: {best_result['segments']}")
    print(f"ביטחון ממוצע: {best_result['confidence']:.2f}")
    print(f"טקסט: {best_result['text']}")
    
    # שמירת הטקסט הטוב ביותר לקובץ טקסט
    with open(os.path.join(output_dir, "best_text.txt"), "w", encoding="utf-8") as f:
        f.write(best_result["text"])
    
    print(f"\nהעיבוד הסתיים. התוצאות נשמרו בתיקייה {output_dir}")

if __name__ == "__main__":
    main() 