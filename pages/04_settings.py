import streamlit as st
from components.header import render_header

def settings_page():
    render_header("הגדרות מערכת", "התאמה אישית של המערכת לצרכים שלך")
    
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("הגדרות כלליות")
    
    # הגדרות תצוגה
    st.write("#### הגדרות תצוגה")
    col1, col2 = st.columns(2)
    with col1:
        theme = st.selectbox("ערכת נושא", ["בהיר", "כהה", "אוטומטי"])
    with col2:
        lang = st.selectbox("שפה", ["עברית", "אנגלית"])
    
    # הגדרות AI
    st.write("#### הגדרות בינה מלאכותית")
    api_key = st.text_input("מפתח API של Gemini", type="password", help="נדרש לפונקציונליות של העוזר החכם")
    
    col1, col2 = st.columns(2)
    with col1:
        auto_analyze = st.toggle("ניתוח אוטומטי בהעלאת מסמך", value=True)
    with col2:
        suggestions = st.toggle("הצע תובנות פיננסיות", value=True)
    
    # הגדרות מסמכים
    st.write("#### הגדרות מסמכים")
    ocr_engine = st.selectbox("מנוע OCR", ["Standard", "Advanced (requires API key)"])
    
    # כפתור שמירת ההגדרות
    if st.button("שמור הגדרות", type="primary"):
        st.success("ההגדרות נשמרו בהצלחה")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # מידע מערכת
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("מידע מערכת")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("גרסת מערכת", "1.2.0")
        st.metric("מסמכים בספרייה", "24")
    with col2:
        st.metric("שטח אחסון בשימוש", "45.2MB / 100MB")
        st.metric("תאריך עדכון אחרון", "12/06/2023")
    
    # כפתור מחיקת נתונים
    st.write("#### פעולות מערכת")
    danger_col1, danger_col2 = st.columns([1, 3])
    with danger_col1:
        if st.button("איפוס מערכת", type="secondary", help="יאפס את כל ההגדרות והנתונים"):
            st.warning("פעולה זו תמחק את כל הנתונים והמסמכים במערכת. האם אתה בטוח?")
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    settings_page()
