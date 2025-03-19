import os
import json
import requests
import base64
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import re

# טעינת משתני הסביבה
load_dotenv()

# קבלת ה-API key מהסביבה
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("המפתח MISTRAL_API_KEY לא נמצא במשתני הסביבה")

def encode_image_to_base64(image_path):
    """המרת תמונה לקידוד base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def preprocess_image(image_path, output_dir):
    """עיבוד מקדים של התמונה לפני שליחתה ל-API"""
    # קריאת התמונה
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"לא ניתן לקרוא את התמונה: {image_path}")
    
    # המרה לגווני אפור
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # שיפור ניגודיות
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # שמירת התמונה המשופרת
    enhanced_path = os.path.join(output_dir, "enhanced.png")
    cv2.imwrite(enhanced_path, enhanced)
    
    # ניסיון עם סף אדפטיבי
    adaptive = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
    adaptive_path = os.path.join(output_dir, "adaptive.png")
    cv2.imwrite(adaptive_path, adaptive)
    
    # החלקה ושיפור חדות
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
    sharpened_path = os.path.join(output_dir, "sharpened.png")
    cv2.imwrite(sharpened_path, sharpened)
    
    return {
        "original": image_path,
        "enhanced": enhanced_path,
        "adaptive": adaptive_path,
        "sharpened": sharpened_path
    }

def analyze_image_with_mistral(image_path):
    """
    ניתוח תמונה באמצעות Mistral API
    """
    # קידוד התמונה ל-base64
    base64_image = encode_image_to_base64(image_path)
    
    # הכנת ה-payload עבור ה-API
    payload = {
        "model": "pixtral-12b-2409",
        "messages": [
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": "Extract all text visible in the image. Include all numbers, identifiers, and alphanumeric codes. Pay special attention to ISIN numbers or any financial identification codes. Format your response as a JSON with the following structure: { \"extracted_text\": \"complete extracted text\", \"numbers\": [array of numbers], \"identifiers\": [array of potential identifiers], \"tables\": [array of tables if any] }"}, 
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
    }
    
    # הגדרת ה-Headers לבקשה
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {MISTRAL_API_KEY}"
    }
    
    # שליחת הבקשה ל-API
    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers=headers,
        json=payload
    )
    
    # בדיקת התגובה
    if response.status_code != 200:
        raise Exception(f"שגיאה בשליחת הבקשה ל-API: {response.text}")
    
    # החזרת התשובה
    return response.json()

def process_mistral_response(response):
    """עיבוד התשובה מ-Mistral API"""
    # חילוץ הטקסט מהתשובה
    if 'choices' not in response or not response['choices']:
        return {"error": "לא התקבלה תשובה תקינה מה-API"}
    
    content = response['choices'][0]['message']['content']
    
    # ניסיון לחלץ את ה-JSON מהתשובה
    try:
        # חיפוש JSON בתוך הטקסט
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            # אם JSON נמצא בפורמט של קוד
            json_str = json_match.group(1)
        else:
            # אחרת ננסה לחלץ ישירות מהתוכן
            json_str = content
        
        # ניסיון לפרסר את ה-JSON
        result = json.loads(json_str)
    except json.JSONDecodeError:
        # אם לא הצלחנו לפרסר JSON, נחזיר את הטקסט המלא
        result = {
            "extracted_text": content,
            "parsing_error": "לא הצלחנו לפרסר JSON מהתשובה",
            "raw_response": content
        }
    
    return result

def extract_numbers_and_ids_from_text(text):
    """חילוץ מספרים ומזהים מתוך טקסט"""
    # חילוץ מספרים
    number_pattern = r'\b\d+[\.,]?\d*\b'
    numbers = re.findall(number_pattern, text)
    
    # חילוץ מזהים פוטנציאליים (כמו ISIN)
    id_patterns = [
        r'\b[A-Z0-9]{12}\b',  # ISIN format: 12 alphanumeric
        r'\b[A-Z]{2}[A-Z0-9]{9}[0-9]\b',  # ISIN specific format
        r'\bXS[0-9]{10}\b',  # Common ISIN pattern starting with XS
        r'\b[A-Z0-9]{10,11}\b'  # Other ID formats
    ]
    
    identifiers = []
    for pattern in id_patterns:
        identifiers.extend(re.findall(pattern, text))
    
    return {
        "numbers": numbers,
        "identifiers": identifiers
    }

def split_to_sections(image_path, output_dir):
    """
    מחלק את התמונה למספר חלקים כדי לשפר את הזיהוי
    """
    # קריאת התמונה
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"לא ניתן לקרוא את התמונה: {image_path}")
    
    # קבלת הממדים של התמונה
    height, width = image.shape[:2]
    
    # חלוקה לארבעה חלקים
    sections = [
        {"name": "top_left", "region": image[0:height//2, 0:width//2]},
        {"name": "top_right", "region": image[0:height//2, width//2:width]},
        {"name": "bottom_left", "region": image[height//2:height, 0:width//2]},
        {"name": "bottom_right", "region": image[height//2:height, width//2:width]}
    ]
    
    section_paths = {}
    for section in sections:
        # שמירת החלק
        section_path = os.path.join(output_dir, f"section_{section['name']}.png")
        cv2.imwrite(section_path, section["region"])
        section_paths[section["name"]] = section_path
    
    return section_paths

def main():
    # יצירת תיקייה לתוצאות
    output_dir = "mistral_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # נתיב התמונה
    image_path = "uploads/corner.png"
    
    print("1. מעבד את התמונה...")
    processed_images = preprocess_image(image_path, output_dir)
    
    print("2. מחלק את התמונה לחלקים...")
    sections = split_to_sections(image_path, output_dir)
    
    print("3. שולח את התמונה המקורית ל-Mistral API...")
    original_response = analyze_image_with_mistral(image_path)
    original_result = process_mistral_response(original_response)
    
    print("4. שולח את התמונות המעובדות ל-Mistral API...")
    processed_results = {}
    for name, path in processed_images.items():
        if name != "original":  # התמונה המקורית כבר נשלחה
            print(f"  שולח תמונה מעובדת: {name}...")
            response = analyze_image_with_mistral(path)
            processed_results[name] = process_mistral_response(response)
    
    print("5. שולח את חלקי התמונה ל-Mistral API...")
    section_results = {}
    for name, path in sections.items():
        print(f"  שולח חלק: {name}...")
        response = analyze_image_with_mistral(path)
        section_results[name] = process_mistral_response(response)
    
    print("6. מאחד את התוצאות...")
    
    # שמירת התוצאות לקבצי JSON
    with open(os.path.join(output_dir, "original_result.json"), "w", encoding="utf-8") as f:
        json.dump(original_result, f, indent=2, ensure_ascii=False)
    
    with open(os.path.join(output_dir, "processed_results.json"), "w", encoding="utf-8") as f:
        json.dump(processed_results, f, indent=2, ensure_ascii=False)
    
    with open(os.path.join(output_dir, "section_results.json"), "w", encoding="utf-8") as f:
        json.dump(section_results, f, indent=2, ensure_ascii=False)
    
    # חילוץ כל המספרים והמזהים הייחודיים מכל התוצאות
    all_numbers = set()
    all_identifiers = set()
    
    # הוספת ממצאים מהתמונה המקורית
    if "extracted_text" in original_result:
        extracted = extract_numbers_and_ids_from_text(original_result["extracted_text"])
        all_numbers.update(extracted["numbers"])
        all_identifiers.update(extracted["identifiers"])
    if "numbers" in original_result:
        all_numbers.update(original_result["numbers"])
    if "identifiers" in original_result:
        all_identifiers.update(original_result["identifiers"])
    
    # הוספת ממצאים מהתמונות המעובדות
    for result in processed_results.values():
        if "extracted_text" in result:
            extracted = extract_numbers_and_ids_from_text(result["extracted_text"])
            all_numbers.update(extracted["numbers"])
            all_identifiers.update(extracted["identifiers"])
        if "numbers" in result:
            all_numbers.update(result["numbers"])
        if "identifiers" in result:
            all_identifiers.update(result["identifiers"])
    
    # הוספת ממצאים מחלקי התמונה
    for result in section_results.values():
        if "extracted_text" in result:
            extracted = extract_numbers_and_ids_from_text(result["extracted_text"])
            all_numbers.update(extracted["numbers"])
            all_identifiers.update(extracted["identifiers"])
        if "numbers" in result:
            all_numbers.update(result["numbers"])
        if "identifiers" in result:
            all_identifiers.update(result["identifiers"])
    
    # שמירת סיכום התוצאות
    summary = {
        "total_numbers": len(all_numbers),
        "total_identifiers": len(all_identifiers),
        "numbers": sorted(list(all_numbers)),
        "identifiers": sorted(list(all_identifiers))
    }
    
    with open(os.path.join(output_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"העיבוד הסתיים. התוצאות נשמרו בתיקייה {output_dir}")
    print(f"נמצאו {len(all_numbers)} מספרים ו-{len(all_identifiers)} מזהים ייחודיים")

if __name__ == "__main__":
    main() 