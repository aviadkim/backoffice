# כלי עיבוד תמונה וזיהוי טקסט

אוסף סקריפטים לעיבוד תמונות וחילוץ טקסט באמצעות טכניקות OCR שונות.

## הקבצים העיקריים

- `process_corner.py` - סקריפט בסיסי לעיבוד תמונה באמצעות מספר שיטות עיבוד תמונה בסיסיות וזיהוי טקסט עם EasyOCR.
- `process_corner_advanced.py` - סקריפט מתקדם המשלב שיטות עיבוד מתקדמות כמו סגמנטציה של אזורי טקסט ושילוב של EasyOCR ו-Tesseract OCR.
- `process_corner_specialized.py` - סקריפט מתמחה בזיהוי מספרים ומזהים ייחודיים כמו ISIN, כולל יצירת מפות חום וזיהוי אזורים בתמונה.
- `process_with_mistral.py` - סקריפט המשתמש ב-Mistral API לזיהוי טקסט ומידע בתמונה.
- `final_results.py` - סקריפט לאיחוד התוצאות מכל השיטות השונות.

## דרישות טכניות

הסקריפטים דורשים את החבילות הבאות:

```
opencv-python
numpy
easyocr
pytesseract
python-dotenv
requests
pillow
matplotlib
```

## שימוש

1. התקן את החבילות הנדרשות:
   ```
   pip install opencv-python numpy easyocr pytesseract python-dotenv requests pillow matplotlib
   ```

2. עבור השימוש ב-Mistral API, יש להגדיר משתנה סביבה `MISTRAL_API_KEY` עם מפתח ה-API שלך.

3. הרצת סקריפט בסיסי:
   ```
   python utils/image_processing/process_corner.py
   ```

4. הרצת סקריפט מתקדם:
   ```
   python utils/image_processing/process_corner_advanced.py
   ```

5. הרצת סקריפט מתמחה:
   ```
   python utils/image_processing/process_corner_specialized.py
   ```

6. הרצת סקריפט Mistral API:
   ```
   python utils/image_processing/process_with_mistral.py
   ```

7. איחוד התוצאות:
   ```
   python utils/image_processing/final_results.py
   ```

התוצאות יישמרו בתיקיות המתאימות בפרויקט.

## שימושים עיקריים

- זיהוי טקסט בתמונות של מסמכים פיננסיים
- חילוץ מספרי ISIN ומזהים אחרים ממסמכים
- זיהוי מספרים ונתונים מספריים בתמונות
- עיבוד מקדים של תמונות לשיפור יכולת הזיהוי של הטקסט

## מידע נוסף

הסקריפטים תומכים במגוון טכניקות עיבוד תמונה, כולל:
- התאמת ניגודיות
- סף אדפטיבי
- סף Otsu
- מורפולוגיה (הרחבה, שחיקה)
- סגמנטציה של אזורי טקסט
- זיהוי אזורים מבוסס קונטורים
- חלוקת התמונה לרשת של תאים קטנים
- יצירת מפות חום לזיהוי אזורים עם מידע רלוונטי 