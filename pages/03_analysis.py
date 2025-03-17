import streamlit as st
import pandas as pd
from utils.analysis import analyze_document, generate_report
from components.header import render_header
from components.metrics import render_metric_cards

def analysis_page():
    render_header("ניתוח פיננסי", "ניתוח נתונים פיננסיים וחיזוי מגמות")
    
    # בחירת מסמך לניתוח
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("בחר מסמך לניתוח")
    
    # רשימה לדוגמה של מסמכים
    documents = [
        "דף חשבון - מאי 2023",
        "דו״ח הוצאות - רבעון 1",
        "כרטיס אשראי - יוני 2023"
    ]
    selected_doc = st.selectbox("בחר מסמך", documents)
    
    if st.button("נתח מסמך", type="primary"):
        with st.spinner("מבצע ניתוח..."):
            # כאן תהיה הלוגיקה של הניתוח
            st.success(f"הניתוח של '{selected_doc}' הושלם בהצלחה")
            
            # הצגת מדדים עיקריים
            metrics = [
                {"label": "סך הכנסות", "value": "₪9,845.50", "color_class": "metric-income"},
                {"label": "סך הוצאות", "value": "₪6,230.75", "color_class": "metric-expense"},
                {"label": "חיסכון חודשי", "value": "₪3,614.75", "color_class": "metric-balance"},
                {"label": "שינוי מהחודש הקודם", "value": "+12.5%", "color_class": "success"}
            ]
            render_metric_cards(metrics)
            
            # הצגת גרפים
            st.subheader("ניתוח קטגוריות הוצאה")
            chart_data = pd.DataFrame({
                "קטגוריה": ["מזון", "דיור", "רכב", "בילויים", "חיסכון", "אחר"],
                "סכום": [1240, 3200, 780, 450, 800, 215]
            })
            st.bar_chart(chart_data, x="קטגוריה", y="סכום")
            
            # המלצות
            st.subheader("המלצות מבוססות AI")
            st.info("על פי הניתוח, ישנה עלייה של 15% בהוצאות על בילויים לעומת החודש הקודם. שקול לקבוע תקציב חודשי לקטגוריה זו.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # היסטוריית ניתוחים
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("היסטוריית ניתוחים")
    
    history = pd.DataFrame({
        "תאריך": ["2023-06-15", "2023-05-12", "2023-04-10"],
        "שם מסמך": ["כרטיס אשראי - יוני 2023", "דף חשבון - מאי 2023", "דו״ח הוצאות - רבעון 1"],
        "סטטוס": ["הושלם", "הושלם", "הושלם"]
    })
    
    st.dataframe(history, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    analysis_page()
