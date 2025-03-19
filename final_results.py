import os
import json
import re

def extract_info_from_mistral(file_path):
    """
    חילוץ מידע מקובץ תוצאות Mistral
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # חילוץ מספרים ומזהים מהתשובה הגולמית
        if 'raw_response' in data:
            raw_response = data['raw_response']
            
            # חילוץ מזהי ISIN מהתשובה הגולמית
            isin_pattern = r'ISIN:\s*([A-Z0-9]{12})'
            isins = re.findall(isin_pattern, raw_response)
            
            # חילוץ מספרים מהתשובה הגולמית
            number_pattern = r'\b\d+[\.,]?\d*\b'
            numbers = re.findall(number_pattern, raw_response)
            
            return {
                "numbers": numbers,
                "isins": isins
            }
        
        return {"numbers": [], "isins": []}
    except Exception as e:
        print(f"שגיאה בעיבוד קובץ {file_path}: {str(e)}")
        return {"numbers": [], "isins": []}

def load_json_file(file_path):
    """
    טעינת קובץ JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"שגיאה בטעינת קובץ {file_path}: {str(e)}")
        return {}

def create_final_summary():
    """
    יצירת סיכום סופי
    """
    mistral_original_result = 'mistral_results/original_result.json'
    mistral_processed_results = 'mistral_results/processed_results.json'
    mistral_section_results = 'mistral_results/section_results.json'
    specialized_summary = 'corner_specialized_results/summary.json'
    
    # אוסף של כל המספרים והמזהים
    all_numbers = set()
    all_identifiers = set()
    
    # הוספת תוצאות מהסקריפט המתמחה
    if os.path.exists(specialized_summary):
        specialized_data = load_json_file(specialized_summary)
        if 'numbers' in specialized_data:
            all_numbers.update(specialized_data['numbers'])
        if 'ids' in specialized_data:
            all_identifiers.update(specialized_data['ids'])
    
    # הוספת תוצאות מ-Mistral
    if os.path.exists(mistral_original_result):
        mistral_data = extract_info_from_mistral(mistral_original_result)
        all_numbers.update(mistral_data['numbers'])
        all_identifiers.update(mistral_data['isins'])
    
    if os.path.exists(mistral_processed_results):
        mistral_processed = load_json_file(mistral_processed_results)
        for method_name, result in mistral_processed.items():
            if 'raw_response' in result:
                mistral_data = extract_info_from_mistral(mistral_processed_results)
                all_numbers.update(mistral_data['numbers'])
                all_identifiers.update(mistral_data['isins'])
    
    if os.path.exists(mistral_section_results):
        mistral_sections = load_json_file(mistral_section_results)
        for section_name, result in mistral_sections.items():
            if 'raw_response' in result:
                mistral_data = extract_info_from_mistral(mistral_section_results)
                all_numbers.update(mistral_data['numbers'])
                all_identifiers.update(mistral_data['isins'])
    
    # מיון ועיבוד הנתונים
    filtered_identifiers = [id for id in all_identifiers if re.match(r'^[A-Z0-9]{12}$', id)]
    
    # יצירת סיכום סופי
    final_summary = {
        "total_numbers_found": len(all_numbers),
        "total_identifiers_found": len(filtered_identifiers),
        "numbers": sorted(list(all_numbers)),
        "identifiers": sorted(filtered_identifiers)
    }
    
    # שמירת הסיכום לקובץ
    with open('final_summary.json', 'w', encoding='utf-8') as f:
        json.dump(final_summary, f, indent=2, ensure_ascii=False)
    
    print(f"נמצאו סך הכל {len(all_numbers)} מספרים ו-{len(filtered_identifiers)} מזהים ייחודיים")
    print(f"המזהים הם: {', '.join(filtered_identifiers)}")

if __name__ == "__main__":
    create_final_summary() 