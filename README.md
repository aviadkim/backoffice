# FinAnalyzer - ניתוח פיננסי חכם

![FinAnalyzer Logo](assets/images/logo.svg)

## סקירה כללית
מערכת FinAnalyzer היא פלטפורמה מבוססת Streamlit לניתוח מסמכים פיננסיים באמצעות OCR ובינה מלאכותית. המערכת מאפשרת העלאת מסמכים פיננסיים (דפי חשבון, כרטיסי אשראי, דוחות), הפקת תובנות וקבלת המלצות מותאמות אישית.

## יכולות
- 📊 ניתוח אוטומטי של מסמכים פיננסיים
- 🔍 זיהוי טקסט באמצעות OCR מתקדם
- 💰 עיבוד עסקאות וסיווג לקטגוריות
- 📈 הצגה ויזואלית של דוחות והוצאות
- 🤖 עוזר פיננסי חכם מבוסס AI של Gemini

## התקנה

### דרישות מקדימות
- Python 3.8+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) עם תמיכה בעברית
- מפתח API של Gemini (לפונקציות AI)

### צעדים להתקנה

1. שיבוט המאגר:
```bash
git clone https://github.com/YOUR_USERNAME/finanalyzer.git
cd finanalyzer
```

2. יצירת סביבה וירטואלית:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. התקנת התלויות:
```bash
pip install -r requirements.txt
```

4. הפעלת האפליקציה:
```bash
streamlit run app.py
```

## מבנה הפרויקט
- `.streamlit/`: הגדרות Streamlit
- `assets/`: קבצים סטטיים (תמונות, CSS)
- `components/`: רכיבי UI לשימוש חוזר
- `pages/`: דפי האפליקציה
- `utils/`: פונקציות שירות
- `models/`: מודלים ומבני נתונים

## תרומה לפרויקט
תרומות לפרויקט מתקבלות בברכה! אנא צרו pull request או פתחו issue כדי לדון בשינויים מוצעים.

## רישיון
[MIT License](LICENSE)

## קרדיטים
- נבנה עם [Streamlit](https://streamlit.io/)
- OCR מופעל באמצעות [Tesseract](https://github.com/tesseract-ocr/tesseract)
- יכולות AI מופעלות על ידי [Google Gemini](https://ai.google.dev/)