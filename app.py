import streamlit as st
import pandas as pd
import numpy as np
import os
import sys

# הוספת התיקיות הנוכחיות לנתיב החיפוש של Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ייבוא רכיבים מקומיים
from components.header import render_header
from components.sidebar import render_sidebar
from components.metrics import render_metric_cards

# הגדרת תצורת הדף
st.set_page_config(
    page_title="FinAnalyzer - ניתוח פיננסי חכם",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# טעינת סגנון מותאם אישית
def load_custom_css():
    with open("assets/css/custom.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# התחלת היישום
def main():
    # טעינת CSS
    try:
        load_custom_css()
    except FileNotFoundError:
        st.warning("קובץ CSS מותאם אישית לא נמצא. הסגנון הבסיסי יוצג.")
    
    # הצגת סרגל צד
    sidebar_state = render_sidebar()
    
    # הצגת כותרת
    render_header(
        "FinAnalyzer - ניתוח פיננסי חכם",
        "העלה מסמכים פיננסיים לניתוח מהיר וקבלת תובנות מבוססות AI",
        with_gradient=True
    )
    
    # יצירת לשוניות
    tabs = st.tabs(["📤 העלאה", "💰 עסקאות", "📊 ניתוח", "📝 דוחות", "🤖 עוזר חכם"])
    
    with tabs[0]:  # לשונית העלאה
        render_upload_tab()
    
    with tabs[1]:  # לשונית עסקאות
        render_transactions_tab()
    
    with tabs[2]:  # לשונית ניתוח
        render_analysis_tab()
    
    with tabs[3]:  # לשונית דוחות - NEW!
        render_reports_tab()
    
    with tabs[4]:  # לשונית עוזר AI (now at index 4)
        render_assistant_tab(api_key=sidebar_state["api_key"])

def render_upload_tab():
    """הצגת לשונית העלאת מסמכים."""
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("העלאת מסמכים פיננסיים")
    st.write("העלה דפי חשבון, חשבוניות או דוחות פיננסיים לניתוח.")
    
    uploaded_file = st.file_uploader("בחר קובץ PDF או Excel", type=["pdf", "xlsx", "xls"])
    
    if uploaded_file:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**קובץ:** {uploaded_file.name}")
        with col2:
            st.markdown('<div style="height: 35px;"></div>', unsafe_allow_html=True)
            if st.button("עבד מסמך", type="primary"):
                # כאן תהיה הלוגיקה לעיבוד המסמך
                st.success(f"המסמך {uploaded_file.name} עובד בהצלחה!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # אפשרויות לדוגמה
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("או נסה מסמך לדוגמה")
    sample_col1, sample_col2, sample_col3 = st.columns(3)
    
    with sample_col1:
        st.button("דף חשבון בנק לדוגמה")
    with sample_col2:
        st.button("דף כרטיס אשראי לדוגמה")
    with sample_col3:
        st.button("דוח השקעות לדוגמה")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_transactions_tab():
    """הצגת לשונית עסקאות."""
    # בדיקה אם יש עסקאות
    if 'transactions' in st.session_state and len(st.session_state.get('transactions', [])) > 0:
        # מידע סיכומי
        summary = {
            "total_income": 5432.10,
            "total_expenses": -3245.67,
            "balance": 2186.43,
            "num_transactions": 24
        }
        
        # הצגת מטריקות
        render_metric_cards([
            {"label": "סך הכנסות", "value": f"₪{summary['total_income']:,.2f}", "color_class": "metric-income"},
            {"label": "סך הוצאות", "value": f"₪{abs(summary['total_expenses']):,.2f}", "color_class": "metric-expense"},
            {"label": "מאזן", "value": f"₪{summary['balance']:,.2f}", "color_class": "metric-balance"},
            {"label": "מספר עסקאות", "value": summary['num_transactions']}
        ])
        
        # טבלת עסקאות
        st.markdown('<div class="startup-card">', unsafe_allow_html=True)
        st.subheader("עסקאות")
        
        # יצירת נתוני דוגמה
        transactions_data = [
            {"date": "2023-03-01", "description": "משכורת חודשית", "amount": 8500, "category": "הכנסה"},
            {"date": "2023-03-03", "description": "רכישה בסופרמרקט", "amount": -450.20, "category": "מזון"},
            {"date": "2023-03-05", "description": "תשלום שכירות", "amount": -3200, "category": "דיור"},
            {"date": "2023-03-10", "description": "תדלוק רכב", "amount": -250, "category": "תחבורה"},
            {"date": "2023-03-15", "description": "חשבון חשמל", "amount": -320, "category": "חשבונות"},
            {"date": "2023-03-20", "description": "הפקדה", "amount": 1000, "category": "הכנסה"}
        ]
        transactions_df = pd.DataFrame(transactions_data)
        
        # אפשרויות סינון
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            search = st.text_input("חיפוש עסקאות", placeholder="הזן מילות מפתח...")
        with filter_col2:
            categories = ['הכל'] + sorted(transactions_df['category'].unique().tolist())
            category_filter = st.selectbox("סינון לפי קטגוריה", categories)
        
        # הצגת הטבלה
        st.dataframe(transactions_df, use_container_width=True)
        
        # אפשרויות הורדה
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="הורד כקובץ CSV",
                data=transactions_df.to_csv(index=False),
                file_name="transactions.csv",
                mime="text/csv"
            )
        with col2:
            st.download_button(
                label="הורד כקובץ Excel",
                data=transactions_df.to_csv(index=False),  # בפועל יש ליצור קובץ Excel
                file_name="transactions.xlsx",
                mime="application/vnd.ms-excel"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # הצגת מצב ריק
        st.markdown("""
        <div style="text-align:center; padding:50px 0;">
            <img src="https://cdn.pixabay.com/photo/2020/07/25/11/29/folder-5436777_960_720.png" width="150">
            <h3 style="margin-top:15px; font-weight:600; color:#4B5563;">אין עסקאות עדיין</h3>
            <p style="color:#6B7280;">העלה מסמך בלשונית ההעלאה כדי להתחיל</p>
        </div>
        """, unsafe_allow_html=True)

def render_analysis_tab():
    """הצגת לשונית ניתוח."""
    # בדיקה אם יש נתונים לניתוח
    if 'transactions' in st.session_state and len(st.session_state.get('transactions', [])) > 0:
        st.markdown('<div class="startup-card">', unsafe_allow_html=True)
        st.subheader("סקירה פיננסית")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("<h3 style='font-size: 1.2rem;'>הכנסות מול הוצאות</h3>", unsafe_allow_html=True)
            chart_data = pd.DataFrame({
                "קטגוריה": ["הכנסות", "הוצאות"],
                "סכום": [8500, 4220.2]
            })
            st.bar_chart(chart_data, x="קטגוריה", y="סכום")
        
        with chart_col2:
            st.markdown("<h3 style='font-size: 1.2rem;'>פילוח לפי קטגוריה</h3>", unsafe_allow_html=True)
            category_data = pd.DataFrame({
                "קטגוריה": ["מזון", "דיור", "תחבורה", "חשבונות"],
                "סכום": [450.2, 3200, 250, 320]
            })
            st.bar_chart(category_data, x="קטגוריה", y="סכום")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # מגמת הוצאות
        st.markdown('<div class="startup-card">', unsafe_allow_html=True)
        st.subheader("מגמת הוצאות לאורך זמן")
        
        months = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני"]
        spending = [3800, 4200, 4220, 3900, 4100, 4300]
        trend_data = pd.DataFrame({
            "חודש": months,
            "הוצאות": spending
        })
        st.line_chart(trend_data, x="חודש", y="הוצאות")
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # הצגת הודעת חסר
        st.info("העלה ועבד מסמך כדי לראות ניתוח")

def render_assistant_tab(api_key=None):
    """הצגת לשונית העוזר החכם."""
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("עוזר פיננסי חכם")
    st.write("שאל שאלות לגבי הנתונים הפיננסיים שלך וקבל תובנות מיידיות.")
    
    # Initialize the chatbot if not already done
    if 'chatbot' not in st.session_state and api_key:
        from utils.chatbot import GeminiChatbot
        st.session_state.chatbot = GeminiChatbot(api_key=api_key)
    
    user_query = st.text_input("שאל שאלה", placeholder="לדוגמה: מה הייתה ההוצאה הגדולה ביותר שלי?")
    
    if api_key:
        if user_query:
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
            
            # Process new question
            if user_query and user_query.strip():
                transactions = st.session_state.get('transactions', [])
                if not transactions:
                    response = "נא להעלות ולעבד מסמך תחילה כדי שאוכל לענות על שאלות לגבי הנתונים הפיננסיים שלך."
                else:
                    with st.spinner("מנתח..."):
                        # Process with Gemini chatbot
                        response = st.session_state.chatbot.process_query(user_query, transactions)
                
                st.session_state.chat_history.append({"user": user_query, "bot": response})
            
            # Display chat history
            st.markdown('<div style="max-height: 400px; overflow-y: auto;">', unsafe_allow_html=True)
            for chat in st.session_state.chat_history:
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>אתה:</strong> {chat['user']}
                </div>
                <div class="chat-message bot-message">
                    <strong>עוזר:</strong> {chat['bot']}
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("נא להזין מפתח API של Gemini בסרגל הצד כדי להפעיל את העוזר החכם")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_reports_tab():
    """הצגת לשונית דוחות."""
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("דוחות פיננסיים")
    
    if 'transactions' not in st.session_state or not st.session_state.transactions:
        st.info("אין נתונים פיננסיים זמינים. נא להעלות ולעבד מסמכים תחילה.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Simple interface to launch the full reports page
    st.write("צור דוחות פיננסיים מקיפים בהתבסס על הנתונים הפיננסיים שלך.")
    
    report_options = st.selectbox(
        "בחר סוג דוח",
        ["סיכום חודשי", "ניתוח קטגוריות", "ניתוח מגמות", "דוח פיננסי מקיף"]
    )
    
    if st.button("צור דוח", type="primary"):
        # Redirect to full reports page
        import webbrowser
        webbrowser.open_new_tab("/reports")
    
    # Alternatively, show a sample or previously generated report
    if 'current_report' in st.session_state:
        with st.expander("תצוגה מקדימה של הדוח האחרון"):
            st.markdown(st.session_state.current_report)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()