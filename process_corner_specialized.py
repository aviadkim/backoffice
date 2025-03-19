import cv2
import numpy as np
import easyocr
import os
import json
import pytesseract
import re
from PIL import Image
from matplotlib import pyplot as plt

def extract_numbers_from_text(text):
    """
    מחלץ מספרים מתוך טקסט באמצעות ביטויים רגולריים
    """
    # חיפוש מספרים בפורמטים שונים, כולל מספרים עם נקודה עשרונית
    pattern = r'\b\d+[\.,]?\d*\b'
    matches = re.findall(pattern, text)
    return matches

def extract_alphanumeric_from_text(text):
    """
    מחלץ רצפים אלפאנומריים מתוך הטקסט שיכולים להיות מספרי מזהים
    """
    # חיפוש רצפים אלפאנומריים בני 8-12 תווים, שיכולים להיות מספרי ISIN או מספרי זיהוי אחרים
    patterns = [
        r'\b[A-Z0-9]{12}\b',  # ISIN format: 12 alphanumeric
        r'\b[A-Z0-9]{10,11}\b',  # Other ID formats
        r'\b[A-Z0-9]{8,9}\b'   # Shorter ID formats
    ]
    
    matches = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, text))
    
    return matches

def preprocess_for_number_detection(image):
    """
    מעבד תמונה עם דגש על זיהוי מספרים
    """
    # המרה לגווני אפור
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # החלקה ושיפור חדות
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
    
    # התאמת ניגודיות
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(sharpened)
    
    # ניסיון בינריזציה עם סף מותאם
    _, binary_global = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # ניסיון עם סף אדפטיבי
    binary_adaptive = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 11, 2)
    
    # שימוש בפעולות מורפולוגיות לשיפור הספרות
    kernel = np.ones((2, 2), np.uint8)
    dilated = cv2.dilate(binary_adaptive, kernel, iterations=1)
    eroded = cv2.erode(dilated, kernel, iterations=1)
    
    # נסיון עם tophat לבידוד הטקסט הכהה (ספרות) על רקע בהיר
    kernel_tophat = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel_tophat)
    _, binary_tophat = cv2.threshold(tophat, 10, 255, cv2.THRESH_BINARY)
    
    return {
        "sharpened": sharpened,
        "enhanced": enhanced,
        "binary_global": binary_global,
        "binary_adaptive": binary_adaptive,
        "eroded": eroded,
        "binary_tophat": binary_tophat
    }

def split_image_to_grid(image, rows=3, cols=3):
    """
    מחלק את התמונה לרשת של תמונות קטנות יותר
    זה יכול לעזור לזהות טקסט בחלקים ספציפיים של התמונה
    """
    # המרה לגווני אפור אם צריך
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    height, width = gray.shape
    cell_height = height // rows
    cell_width = width // cols
    
    # יצירת רשת של תמונות קטנות
    grid_cells = []
    for r in range(rows):
        for c in range(cols):
            # חישוב גבולות התא
            start_row = r * cell_height
            end_row = min((r + 1) * cell_height, height)
            start_col = c * cell_width
            end_col = min((c + 1) * cell_width, width)
            
            # חיתוך התא מהתמונה המקורית
            cell = gray[start_row:end_row, start_col:end_col].copy()
            
            # הוספת התא לרשימה עם הקואורדינטות שלו
            grid_cells.append({
                "id": f"row{r}_col{c}",
                "image": cell,
                "coords": (start_row, end_row, start_col, end_col)
            })
    
    return grid_cells

def process_grid_cell(cell, output_dir):
    """
    מעבד תא בודד מהרשת
    """
    cell_id = cell["id"]
    cell_image = cell["image"]
    coords = cell["coords"]
    
    # שמירת התמונה המקורית של התא
    cv2.imwrite(os.path.join(output_dir, f"grid_cell_{cell_id}_original.png"), cell_image)
    
    # עיבוד התא
    processed_images = preprocess_for_number_detection(cell_image)
    
    # שמירת התמונות המעובדות
    for method, processed in processed_images.items():
        cv2.imwrite(os.path.join(output_dir, f"grid_cell_{cell_id}_{method}.png"), processed)
    
    # חילוץ טקסט
    results = {}
    
    # EasyOCR
    reader = easyocr.Reader(['en'])
    easyocr_results = reader.readtext(cell_image)
    easyocr_text = " ".join([text for _, text, _ in easyocr_results])
    
    # Tesseract
    try:
        pil_img = Image.fromarray(cell_image)
        tesseract_text = pytesseract.image_to_string(pil_img, lang='eng')
    except Exception as e:
        tesseract_text = f"Error: {str(e)}"
    
    # חילוץ מספרים
    easyocr_numbers = extract_numbers_from_text(easyocr_text)
    tesseract_numbers = extract_numbers_from_text(tesseract_text)
    
    # חילוץ מזהים
    easyocr_ids = extract_alphanumeric_from_text(easyocr_text)
    tesseract_ids = extract_alphanumeric_from_text(tesseract_text)
    
    results = {
        "coords": coords,
        "easyocr": {
            "text": easyocr_text,
            "numbers": easyocr_numbers,
            "ids": easyocr_ids,
            "segments": len(easyocr_results),
            "confidence": np.mean([conf for _, _, conf in easyocr_results]) if easyocr_results else 0
        },
        "tesseract": {
            "text": tesseract_text,
            "numbers": tesseract_numbers,
            "ids": tesseract_ids
        }
    }
    
    # חילוץ טקסט גם מהתמונות המעובדות
    processed_results = {}
    for method, processed in processed_images.items():
        try:
            pil_img = Image.fromarray(processed)
            text = pytesseract.image_to_string(pil_img, lang='eng')
            numbers = extract_numbers_from_text(text)
            ids = extract_alphanumeric_from_text(text)
            
            processed_results[method] = {
                "text": text,
                "numbers": numbers,
                "ids": ids
            }
        except Exception as e:
            processed_results[method] = {
                "text": f"Error: {str(e)}",
                "numbers": [],
                "ids": []
            }
    
    results["processed"] = processed_results
    
    return results

def visualize_results(image, grid_cells, results, output_dir):
    """
    מוסיף ויזואליזציה של התוצאות על התמונה המקורית
    """
    # יצירת עותק של התמונה המקורית
    if len(image.shape) == 3:
        visualized = image.copy()
    else:
        visualized = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    # ציור של התאים וכתיבת הטקסט שזוהה
    for cell, result in zip(grid_cells, results):
        cell_id = cell["id"]
        start_row, end_row, start_col, end_col = cell["coords"]
        
        # ציור מלבן סביב התא
        cv2.rectangle(visualized, (start_col, start_row), (end_col, end_row), (0, 255, 0), 2)
        
        # כתיבת מזהה התא
        cv2.putText(visualized, cell_id, (start_col, start_row - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # אם נמצאו מספרים, נוסיף אותם לויזואליזציה
        easyocr_numbers = result["easyocr"]["numbers"]
        if easyocr_numbers:
            number_text = ", ".join(easyocr_numbers[:3])  # מציג רק עד 3 מספרים
            if len(easyocr_numbers) > 3:
                number_text += "..."
            cv2.putText(visualized, f"Numbers: {number_text}", 
                       (start_col, start_row + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
        
        # אם נמצאו מזהים אלפאנומריים, נוסיף אותם לויזואליזציה
        easyocr_ids = result["easyocr"]["ids"]
        if easyocr_ids:
            id_text = ", ".join(easyocr_ids[:2])  # מציג רק עד 2 מזהים
            if len(easyocr_ids) > 2:
                id_text += "..."
            cv2.putText(visualized, f"IDs: {id_text}", 
                       (start_col, start_row + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    
    # שמירת התמונה עם התוצאות
    cv2.imwrite(os.path.join(output_dir, "grid_visualization.png"), visualized)
    
    return visualized

def create_heatmap(image, grid_cells, results, output_dir):
    """
    יוצר מפת חום של אזורים עם מספרים ומזהים
    """
    # יצירת מפת חום ריקה בגודל התמונה המקורית
    if len(image.shape) == 3:
        height, width, _ = image.shape
    else:
        height, width = image.shape
    
    # מפת חום למספרים
    number_heatmap = np.zeros((height, width), dtype=np.uint8)
    
    # מפת חום למזהים
    id_heatmap = np.zeros((height, width), dtype=np.uint8)
    
    # מילוי מפות החום בהתאם לממצאים
    for cell, result in zip(grid_cells, results):
        start_row, end_row, start_col, end_col = cell["coords"]
        
        # ספירת כמות המספרים והמזהים בתא
        number_count = len(result["easyocr"]["numbers"]) + len(result["tesseract"]["numbers"])
        for processed_result in result["processed"].values():
            number_count += len(processed_result["numbers"])
        
        id_count = len(result["easyocr"]["ids"]) + len(result["tesseract"]["ids"])
        for processed_result in result["processed"].values():
            id_count += len(processed_result["ids"])
        
        # נרמול הערכים
        number_intensity = min(255, number_count * 40)  # מקסימום 255
        id_intensity = min(255, id_count * 40)  # מקסימום 255
        
        # מילוי האזור במפת החום המתאימה
        number_heatmap[start_row:end_row, start_col:end_col] = number_intensity
        id_heatmap[start_row:end_row, start_col:end_col] = id_intensity
    
    # המרת מפות החום לתמונות צבעוניות
    number_heatmap_colored = cv2.applyColorMap(number_heatmap, cv2.COLORMAP_JET)
    id_heatmap_colored = cv2.applyColorMap(id_heatmap, cv2.COLORMAP_JET)
    
    # שמירת מפות החום
    cv2.imwrite(os.path.join(output_dir, "number_heatmap.png"), number_heatmap_colored)
    cv2.imwrite(os.path.join(output_dir, "id_heatmap.png"), id_heatmap_colored)
    
    return number_heatmap_colored, id_heatmap_colored

def detect_key_areas(image):
    """
    מנסה לזהות אזורים עם גבולות (מסגרות) שעשויים להכיל טבלאות או מידע חשוב
    """
    # המרה לגווני אפור
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # גילוי קצוות באמצעות canny
    edges = cv2.Canny(gray, 50, 150)
    
    # הרחבת הקצוות כדי ליצור קווים רציפים
    kernel = np.ones((3, 3), np.uint8)
    dilated_edges = cv2.dilate(edges, kernel, iterations=2)
    
    # מציאת קונטורים
    contours, _ = cv2.findContours(dilated_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # סינון קונטורים קטנים
    min_area = 1000  # סף מינימלי לשטח
    filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
    
    # מיון הקונטורים לפי גודל (מהגדול לקטן)
    sorted_contours = sorted(filtered_contours, key=cv2.contourArea, reverse=True)
    
    # לקיחת הקונטורים הגדולים ביותר
    top_contours = sorted_contours[:5] if len(sorted_contours) > 5 else sorted_contours
    
    # יצירת תמונת ויזואליזציה
    if len(image.shape) == 3:
        visualization = image.copy()
    else:
        visualization = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    
    # ציור הקונטורים
    key_areas = []
    for i, contour in enumerate(top_contours):
        x, y, w, h = cv2.boundingRect(contour)
        
        # שמירת האזור
        key_areas.append({
            "id": i,
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "area": w * h
        })
        
        # ציור מלבן סביב האזור
        cv2.rectangle(visualization, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(visualization, f"Area {i}", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    return key_areas, visualization

def main():
    # יצירת תיקייה לתוצאות
    output_dir = "corner_specialized_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # טעינת התמונה
    image_path = "uploads/corner.png"
    image = cv2.imread(image_path)
    if image is None:
        print(f"שגיאה: לא ניתן לטעון את התמונה {image_path}")
        return
    
    print("1. מזהה אזורי מפתח...")
    key_areas, key_areas_visualization = detect_key_areas(image)
    cv2.imwrite(os.path.join(output_dir, "key_areas.png"), key_areas_visualization)
    
    # שמירת נתוני האזורים לקובץ JSON
    with open(os.path.join(output_dir, "key_areas.json"), 'w', encoding='utf-8') as f:
        json.dump(key_areas, f, indent=2, ensure_ascii=False)
    
    print(f"נמצאו {len(key_areas)} אזורי מפתח")
    
    print("2. מחלק את התמונה לרשת...")
    grid_cells = split_image_to_grid(image, rows=4, cols=4)  # חלוקה ל-16 תאים
    
    print("3. מעבד כל תא ברשת...")
    grid_results = []
    for cell in grid_cells:
        print(f"  מעבד תא: {cell['id']}")
        result = process_grid_cell(cell, output_dir)
        grid_results.append(result)
    
    # שמירת תוצאות הרשת לקובץ JSON
    with open(os.path.join(output_dir, "grid_results.json"), 'w', encoding='utf-8') as f:
        # המרת numpy arrays למשהו שניתן להמיר ל-JSON
        serializable_results = []
        for result in grid_results:
            serializable_result = {
                "coords": result["coords"],
                "easyocr": {
                    "text": result["easyocr"]["text"],
                    "numbers": result["easyocr"]["numbers"],
                    "ids": result["easyocr"]["ids"],
                    "segments": result["easyocr"]["segments"],
                    "confidence": float(result["easyocr"]["confidence"])
                },
                "tesseract": {
                    "text": result["tesseract"]["text"],
                    "numbers": result["tesseract"]["numbers"],
                    "ids": result["tesseract"]["ids"]
                },
                "processed": {}
            }
            
            for method, proc_result in result["processed"].items():
                serializable_result["processed"][method] = {
                    "text": proc_result["text"],
                    "numbers": proc_result["numbers"],
                    "ids": proc_result["ids"]
                }
            
            serializable_results.append(serializable_result)
        
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    print("4. יוצר ויזואליזציות...")
    visualized = visualize_results(image, grid_cells, grid_results, output_dir)
    
    print("5. יוצר מפות חום...")
    number_heatmap, id_heatmap = create_heatmap(image, grid_cells, grid_results, output_dir)
    
    print("6. מסכם את התוצאות...")
    # איסוף כל המספרים והמזהים שנמצאו
    all_numbers = set()
    all_ids = set()
    
    for result in grid_results:
        # הוספת מספרים ומזהים מ-EasyOCR
        all_numbers.update(result["easyocr"]["numbers"])
        all_ids.update(result["easyocr"]["ids"])
        
        # הוספת מספרים ומזהים מ-Tesseract
        all_numbers.update(result["tesseract"]["numbers"])
        all_ids.update(result["tesseract"]["ids"])
        
        # הוספת מספרים ומזהים מהתמונות המעובדות
        for proc_result in result["processed"].values():
            all_numbers.update(proc_result["numbers"])
            all_ids.update(proc_result["ids"])
    
    # שמירת הסיכום לקובץ
    summary = {
        "total_numbers_found": len(all_numbers),
        "total_ids_found": len(all_ids),
        "numbers": sorted(list(all_numbers)),
        "ids": sorted(list(all_ids))
    }
    
    with open(os.path.join(output_dir, "summary.json"), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # שמירת המספרים והמזהים לקבצים נפרדים
    with open(os.path.join(output_dir, "numbers.txt"), 'w', encoding='utf-8') as f:
        f.write("\n".join(sorted(all_numbers)))
    
    with open(os.path.join(output_dir, "ids.txt"), 'w', encoding='utf-8') as f:
        f.write("\n".join(sorted(all_ids)))
    
    print(f"\nהעיבוד המתמחה הסתיים. התוצאות נשמרו בתיקייה {output_dir}")
    print(f"נמצאו {len(all_numbers)} מספרים ו-{len(all_ids)} מזהים ייחודיים")

if __name__ == "__main__":
    main() 