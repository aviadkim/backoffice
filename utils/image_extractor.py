import os
import re
import json
import logging
import cv2
import numpy as np
import pytesseract
from PIL import Image
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/image_extractor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# הגדרת נתיב ל-Tesseract אם צריך
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ImageExtractor:
    """
    מחלקה לחילוץ טקסט מקבצי תמונה באמצעות OCR.
    """
    
    def __init__(self, tesseract_path=None):
        """
        אתחול המחלץ.
        
        Args:
            tesseract_path (str, optional): נתיב לקובץ ההרצה של Tesseract OCR.
        """
        # אם סופק נתיב, מגדירים אותו
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # בדיקה שניתן להשתמש ב-Tesseract
        try:
            pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {pytesseract.get_tesseract_version()}")
        except Exception as e:
            logger.warning(f"Tesseract might not be properly installed: {str(e)}")
            logger.warning("Will attempt to use it anyway, but it might fail")
    
    def extract_from_image(self, image_path, language='eng+heb'):
        """
        חילוץ טקסט מתמונה.
        
        Args:
            image_path (str): נתיב לקובץ התמונה.
            language (str, optional): השפות לזיהוי. ברירת מחדל היא אנגלית + עברית.
            
        Returns:
            dict: תוצאת החילוץ הכוללת טקסט וחילוצי מידע פיננסי.
        """
        try:
            logger.info(f"Extracting content from image: {image_path}")
            
            # וידוא שהקובץ קיים
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # טעינת התמונה
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            # טרום-עיבוד התמונה לשיפור זיהוי הטקסט
            preprocessed = self._preprocess_image(image)
            
            # חילוץ הטקסט באמצעות Tesseract
            extracted_text = pytesseract.image_to_string(preprocessed, lang=language)
            logger.info(f"Extracted {len(extracted_text)} characters from the image")
            
            # חילוץ מבנה טבלאי באמצעות Tesseract
            tables_data = self._extract_tables_from_image(image)
            
            # חילוץ האחזקות מהטקסט והטבלאות
            holdings = self._extract_holdings(extracted_text, tables_data)
            
            # יצירת מבנה התוצאה
            result = {
                "metadata": {
                    "filename": os.path.basename(image_path),
                    "processed_date": datetime.now().isoformat(),
                    "processor": "tesseract_ocr"
                },
                "text": extracted_text,
                "tables": tables_data,
                "financial_data": {
                    "holdings": holdings,
                    "summary": {
                        "total_holdings": len(holdings),
                        "total_value": sum(holding.get("value", 0) or 0 for holding in holdings)
                    }
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting content from image: {str(e)}", exc_info=True)
            raise
    
    def _preprocess_image(self, image):
        """
        טרום-עיבוד התמונה לשיפור זיהוי הטקסט.
        
        Args:
            image (numpy.ndarray): תמונת OpenCV.
            
        Returns:
            numpy.ndarray: התמונה המעובדת.
        """
        try:
            # המרה לסקאלת אפור
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # הגדלת הניגודיות
            # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            # gray = clahe.apply(gray)
            
            # הסרת רעש
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # הגדלת סף בינארי
            # _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return blur
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}", exc_info=True)
            # אם יש שגיאה, החזר את התמונה המקורית
            return image
    
    def _extract_tables_from_image(self, image):
        """
        חילוץ טבלאות מהתמונה.
        
        Args:
            image (numpy.ndarray): תמונת OpenCV.
            
        Returns:
            list: רשימה של טבלאות שזוהו.
        """
        try:
            # שימוש ב-Tesseract's TSV או הוצאת DATA
            result = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # ארגון הנתונים לפי שורות וטבלאות משוערות
            tables = []
            rows = {}
            
            # קיבוץ הטקסט לפי שורות
            for i in range(len(result["text"])):
                text = result["text"][i].strip()
                if not text:
                    continue
                
                # השתמש בקואורדינטה Y לקיבוץ לפי שורות (עם שוליים קטנים)
                y_key = result["top"][i] // 10 * 10  # עיגול ל-10 פיקסלים הקרובים
                
                if y_key not in rows:
                    rows[y_key] = []
                
                rows[y_key].append({
                    "text": text,
                    "left": result["left"][i],
                    "conf": result["conf"][i]
                })
            
            # מיון השורות לפי מיקום אנכי
            sorted_rows = [rows[y_key] for y_key in sorted(rows.keys())]
            
            # אם יש מספיק שורות, הנח שזו טבלה פוטנציאלית
            if len(sorted_rows) >= 3:
                # מיון תאים בכל שורה לפי מיקום אופקי
                ordered_rows = []
                for row in sorted_rows:
                    ordered_rows.append([cell["text"] for cell in sorted(row, key=lambda x: x["left"])])
                
                # השתמש בשורה הראשונה כהנחה שהיא כותרת
                table = {
                    "headers": ordered_rows[0] if len(ordered_rows) > 0 else [],
                    "data": ordered_rows[1:] if len(ordered_rows) > 1 else [],
                    "type": "general"
                }
                
                tables.append(table)
            
            return tables
            
        except Exception as e:
            logger.error(f"Error extracting tables from image: {str(e)}", exc_info=True)
            return []
    
    def _extract_holdings(self, text, tables):
        """
        חילוץ נתוני אחזקות מהטקסט והטבלאות.
        
        Args:
            text (str): הטקסט שחולץ.
            tables (list): טבלאות שחולצו.
            
        Returns:
            list: רשימת אחזקות שזוהו.
        """
        holdings = []
        
        # קודם, חפש בטבלאות
        for table in tables:
            if self._is_holdings_table(table):
                table_holdings = self._extract_holdings_from_table(table)
                holdings.extend(table_holdings)
        
        # אם לא נמצאו אחזקות בטבלאות, נסה למצוא בטקסט
        if not holdings:
            text_holdings = self._extract_holdings_from_text(text)
            holdings.extend(text_holdings)
        
        return holdings
    
    def _is_holdings_table(self, table):
        """
        בדיקה אם הטבלה מכילה אחזקות.
        
        Args:
            table (dict): טבלה שחולצה.
            
        Returns:
            bool: האם הטבלה מכילה אחזקות.
        """
        # מילות מפתח שעשויות להצביע על טבלת אחזקות
        keywords = [
            "isin", "security", "name", "quantity", "price", "value", "currency",
            "נייר", "ני\"ע", "כמות", "שער", "שווי", "מטבע"
        ]
        
        # בדיקה בכותרות
        if table["headers"]:
            headers_text = " ".join([str(h).lower() for h in table["headers"]])
            for keyword in keywords:
                if keyword.lower() in headers_text:
                    return True
        
        # בדיקה בשורה הראשונה של הנתונים
        if table["data"] and len(table["data"]) > 0:
            first_row = " ".join([str(cell).lower() for cell in table["data"][0]])
            # חיפוש תבנית ISIN
            if any(isinstance(cell, str) and len(cell) == 12 and cell[:2].isalpha() and cell[2:].isalnum() 
                  for cell in table["data"][0] if cell):
                return True
        
        return False
    
    def _extract_holdings_from_table(self, table):
        """
        חילוץ אחזקות מטבלה.
        
        Args:
            table (dict): טבלה שחולצה.
            
        Returns:
            list: רשימת אחזקות שחולצו.
        """
        holdings = []
        
        if not table["data"]:
            return holdings
        
        # זיהוי משמעות העמודות
        headers = table["headers"]
        isin_col = -1
        name_col = -1
        quantity_col = -1
        price_col = -1
        value_col = -1
        currency_col = -1
        
        # מיפוי עמודות לפי כותרות
        for i, header in enumerate(headers):
            if not header:
                continue
                
            header_lower = str(header).lower()
            
            if "isin" in header_lower:
                isin_col = i
            elif any(keyword in header_lower for keyword in ["name", "security", "שם", "נייר", "ני\"ע"]):
                name_col = i
            elif any(keyword in header_lower for keyword in ["quantity", "amount", "כמות", "יחידות"]):
                quantity_col = i
            elif any(keyword in header_lower for keyword in ["price", "מחיר", "שער"]):
                price_col = i
            elif any(keyword in header_lower for keyword in ["value", "שווי"]):
                value_col = i
            elif any(keyword in header_lower for keyword in ["currency", "מטבע"]):
                currency_col = i
        
        # אם לא ניתן לקבוע משמעות מהכותרות, ננסה להסיק מהנתונים
        if isin_col == -1 and name_col == -1:
            # בדיקת השורה הראשונה להסקת משמעות העמודות
            for i, cell in enumerate(table["data"][0]):
                if not cell:
                    continue
                    
                cell_str = str(cell)
                
                # בדיקת תבנית ISIN (2 אותיות + 10 תווים אלפאנומריים)
                if len(cell_str) == 12 and cell_str[:2].isalpha() and cell_str[2:].isalnum():
                    isin_col = i
                # אם זה טקסט ארוך, זה יכול להיות שם
                elif len(cell_str) > 5 and not cell_str.replace('.', '').isdigit():
                    name_col = i
                # חיפוש עמודות מספריות למחיר, כמות, ערך
                elif cell_str.replace('.', '').replace(',', '').isdigit():
                    if price_col == -1:
                        price_col = i
                    elif quantity_col == -1:
                        quantity_col = i
                    elif value_col == -1:
                        value_col = i
        
        # עיבוד כל שורה
        for row in table["data"]:
            if not row or len(row) < max(filter(lambda x: x >= 0, [isin_col, name_col, quantity_col, price_col, value_col, currency_col]), default=-1) + 1:
                continue  # דילוג על שורות שאין בהן מספיק עמודות
            
            # חילוץ ערכים
            isin = row[isin_col] if isin_col >= 0 and isin_col < len(row) else None
            name = row[name_col] if name_col >= 0 and name_col < len(row) else None
            quantity = self._parse_number(row[quantity_col]) if quantity_col >= 0 and quantity_col < len(row) else None
            price = self._parse_number(row[price_col]) if price_col >= 0 and price_col < len(row) else None
            value = self._parse_number(row[value_col]) if value_col >= 0 and value_col < len(row) else None
            currency = row[currency_col] if currency_col >= 0 and currency_col < len(row) else self._detect_currency_in_row(row)
            
            # אם יש לפחות ISIN או שם, יצירת אחזקה
            if isin or name:
                holding = {
                    "isin": isin,
                    "name": name or "Unknown Security",
                    "quantity": quantity,
                    "price": price,
                    "value": value,
                    "currency": currency
                }
                holdings.append(holding)
        
        return holdings
    
    def _extract_holdings_from_text(self, text):
        """
        חילוץ נתוני אחזקות מטקסט באמצעות ביטויים רגולריים.
        
        Args:
            text (str): הטקסט שחולץ.
            
        Returns:
            list: רשימת אחזקות שזוהו.
        """
        holdings = []
        
        try:
            # חיפוש קודי ISIN
            isin_pattern = r'([A-Z]{2}[A-Z0-9]{9}\d)'
            isin_matches = re.finditer(isin_pattern, text)
            
            for match in isin_matches:
                isin = match.group(1)
                
                # קבלת הקשר סביב ה-ISIN
                context_start = max(0, match.start() - 500)
                context_end = min(len(text), match.end() + 500)
                context = text[context_start:context_end]
                
                # חילוץ פרטים
                holding = {
                    "isin": isin,
                    "name": self._extract_security_name(context) or "Unknown Security",
                    "price": self._extract_price(context),
                    "quantity": self._extract_quantity(context),
                    "value": self._extract_value(context),
                    "currency": self._extract_currency(context)
                }
                
                holdings.append(holding)
            
            # במקרה שלא נמצאו קודי ISIN, ננסה לחפש מידע מבוסס-שם קרן
            fund_patterns = [
                r'(קרן|פיקדון|תיק השקעות|נייר ערך)\s+[^.\n]+',
                r'([^.\n]{3,50})\s+(קרן|פיקדון|השקעה|נייר)'
            ]
            
            for pattern in fund_patterns:
                fund_matches = re.finditer(pattern, text, re.MULTILINE)
                for match in fund_matches:
                    fund_text = match.group(0)
                    
                    # קבלת הקשר רחב יותר
                    context_start = max(0, match.start() - 300)
                    context_end = min(len(text), match.end() + 300)
                    context = text[context_start:context_end]
                    
                    # חילוץ פרטים
                    fund_name = fund_text.strip()
                    
                    holding = {
                        "isin": None,
                        "name": fund_name,
                        "price": self._extract_price(context),
                        "quantity": self._extract_quantity(context),
                        "value": self._extract_value(context),
                        "currency": self._extract_currency(context)
                    }
                    
                    # הוספה רק אם יש לפחות מחיר, כמות או ערך
                    if holding["price"] is not None or holding["quantity"] is not None or holding["value"] is not None:
                        holdings.append(holding)
            
            return holdings
            
        except Exception as e:
            logger.error(f"Error extracting holdings from text: {str(e)}", exc_info=True)
            return []
    
    def _parse_number(self, value):
        """פירוש מספר מפורמטים שונים."""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # הסרת תווים שאינם מספריים למעט נקודה עשרונית וסימן מינוס
            clean_value = re.sub(r'[^\d.\-,]', '', value)
            # החלפת פסיק בנקודה עבור נקודה עשרונית אם נדרש
            clean_value = clean_value.replace(',', '.')
            
            try:
                return float(clean_value)
            except ValueError:
                return None
        
        return None
    
    def _detect_currency_in_row(self, row):
        """זיהוי מטבע מערכי שורה."""
        row_text = ' '.join(str(cell) for cell in row if cell)
        
        currency_patterns = {
            "ILS": r'₪|ש"ח|שקל|NIS',
            "USD": r'\$|דולר|USD',
            "EUR": r'€|אירו|EUR'
        }
        
        for currency, pattern in currency_patterns.items():
            if re.search(pattern, row_text, re.IGNORECASE):
                return currency
        
        return "ILS"  # ברירת מחדל לשקל
    
    def _extract_security_name(self, context):
        """חילוץ שם נייר ערך מהקשר."""
        patterns = [
            r'שם נייר[:\s]+([^\n]+)',
            r'שם המכשיר[:\s]+([^\n]+)',
            r'שם המנפיק[:\s]+([^\n]+)',
            r'נייר ערך[:\s]+([^\n]+)',
            r'קרן[:\s]+([^\n]+)',
            r'מכשיר[:\s]+([^\n]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_price(self, context):
        """חילוץ מחיר מהקשר."""
        patterns = [
            r'מחיר[:\s]+([\d,.]+)',
            r'שער[:\s]+([\d,.]+)',
            r'שווי ליחידה[:\s]+([\d,.]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        return None
    
    def _extract_quantity(self, context):
        """חילוץ כמות מהקשר."""
        patterns = [
            r'כמות[:\s]+([\d,.]+)',
            r'יתרה[:\s]+([\d,.]+)',
            r'מספר יחידות[:\s]+([\d,.]+)',
            r'יחידות[:\s]+([\d,.]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        return None
    
    def _extract_value(self, context):
        """חילוץ ערך מהקשר."""
        patterns = [
            r'שווי[:\s]+([\d,.]+)',
            r'שווי שוק[:\s]+([\d,.]+)',
            r'שווי כולל[:\s]+([\d,.]+)',
            r'סה"כ שווי[:\s]+([\d,.]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        return None
    
    def _extract_currency(self, context):
        """חילוץ מטבע מהקשר."""
        patterns = {
            "ILS": r'₪|ש"ח|שקל|NIS',
            "USD": r'\$|דולר|USD',
            "EUR": r'€|אירו|EUR'
        }
        for currency, pattern in patterns.items():
            if re.search(pattern, context, re.IGNORECASE):
                return currency
        return "ILS"  # ברירת מחדל לשקל
    
    def save_extracted_content(self, content, output_dir="extracted_data"):
        """
        שמירת תוכן שחולץ לקבצי JSON.
        
        Args:
            content (dict): תוכן שחולץ.
            output_dir (str): תיקייה לשמירת הקבצים.
        """
        try:
            # יצירת תיקיית פלט אם לא קיימת
            os.makedirs(output_dir, exist_ok=True)
            
            # יצירת חותמת זמן לשמות קבצים ייחודיים
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # וידוא שיש שם קובץ תקין
            if 'metadata' in content and 'filename' in content['metadata']:
                base_filename = os.path.splitext(content['metadata']['filename'])[0]
            else:
                base_filename = f"document_{timestamp}"
                logger.warning(f"No filename found in content, using generated name: {base_filename}")
            
            # שמירת תוכן מלא
            output_file = os.path.join(output_dir, f"{base_filename}_ocr_{timestamp}_full.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved full content to {output_file}")
            
            # שמירת טבלאות בנפרד
            if "tables" in content and content["tables"]:
                tables_file = os.path.join(output_dir, f"{base_filename}_ocr_{timestamp}_tables.json")
                with open(tables_file, 'w', encoding='utf-8') as f:
                    json.dump(content["tables"], f, ensure_ascii=False, indent=2)
                logger.info(f"Saved tables to {tables_file}")
            
            # שמירת טקסט בנפרד
            if "text" in content and content["text"]:
                text_file = os.path.join(output_dir, f"{base_filename}_ocr_{timestamp}_text.txt")
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(content["text"])
                logger.info(f"Saved text to {text_file}")
            
            logger.info(f"Saved all extracted content to {output_dir}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error saving extracted content: {str(e)}", exc_info=True)
            raise
    
    def test_image_file(self, file_path, output_to_console=True):
        """
        בדיקת חילוץ על קובץ תמונה קיים והדפסת תוצאות.
        
        Args:
            file_path (str): נתיב לקובץ התמונה.
            output_to_console (bool): האם להדפיס תוצאות למסוף.
        """
        try:
            logger.info(f"Testing extraction on image: {file_path}")
            
            # חילוץ תוכן
            result = self.extract_from_image(file_path)
            
            # שמירת התוכן שחולץ
            self.save_extracted_content(result)
            
            # הדפסת סיכום התוצאות
            if output_to_console:
                print(f"\n{'='*50}")
                print(f"OCR TEST RESULTS FOR: {os.path.basename(file_path)}")
                print(f"{'='*50}")
                print(f"Total text length: {len(result['text'])}")
                print(f"Total tables: {len(result['tables'])}")
                print(f"Total holdings: {len(result['financial_data']['holdings'])}")
                
                # הדפסת אחזקות לדוגמה אם זמינות
                if result['financial_data']['holdings']:
                    print("\nSample holdings:")
                    for i, holding in enumerate(result['financial_data']['holdings'][:5]):
                        print(f"  {i+1}. Name: {holding.get('name')}, "
                              f"Quantity: {holding.get('quantity')}, "
                              f"Value: {holding.get('value')} {holding.get('currency')}")
                
                # אם לא נמצאו אחזקות
                if len(result['financial_data']['holdings']) == 0:
                    print("\nNo holdings found in the image")
                    
                    # הדפסת 500 התווים הראשונים של הטקסט לצורכי ניפוי שגיאות
                    print("\nFirst 500 chars of extracted text:")
                    print(result['text'][:500])
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing image file: {str(e)}", exc_info=True)
            if output_to_console:
                print(f"ERROR: {str(e)}")
            raise 