import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from dotenv import load_dotenv
from utils.pdf_integration import pdf_processor
from utils.securities_pdf_processor import SecuritiesPDFProcessor
from utils.mistral_extractor import MistralExtractor

# הוספת התיקיות הנוכחיות לנתיב החיפוש של Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ייבוא רכיבים מקומיים
from components.header import render_header
from components.sidebar import render_sidebar
from components.metrics import render_metric_cards

# Load environment variables
load_dotenv()

# Check for required environment variables
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    st.error("Please set GOOGLE_APPLICATION_CREDENTIALS in .env file")
    st.stop()

if not os.getenv("GEMINI_API_KEY"):
    st.error("Please set GEMINI_API_KEY in .env file")
    st.stop()

if not os.getenv("MISTRAL_API_KEY"):
    st.error("Please set MISTRAL_API_KEY in .env file")
    st.stop()

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
    
    # אתחול מחלץ Mistral
    try:
        mistral_extractor = MistralExtractor()
    except Exception as e:
        st.error(f"שגיאה באתחול Mistral OCR: {str(e)}")
        return
    
    # הצגת סרגל צד
    sidebar_state = render_sidebar()
    
    # הצגת כותרת
    render_header(
        "FinAnalyzer - ניתוח פיננסי חכם",
        "העלה מסמכים פיננסיים לניתוח מהיר וקבלת תובנות מבוססות AI",
        with_gradient=True
    )
    
    # בחירת סוג OCR
    ocr_type = st.radio(
        "בחר סוג OCR:",
        ["Mistral OCR (מומלץ)", "OCR רגיל"],
        index=0
    )
    use_mistral = ocr_type == "Mistral OCR (מומלץ)"
    
    # העלאת קובץ
    uploaded_file = st.file_uploader("העלה קובץ PDF", type=["pdf"])
    
    if uploaded_file is not None:
        # שמירת הקובץ
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # עיבוד הקובץ
        text, data = process_pdf_file("temp.pdf", use_mistral)
        
        if text and data:
            # הצגת תוצאות
            st.subheader("תוצאות העיבוד")
            
            # הצגת טקסט שחולץ
            with st.expander("טקסט שחולץ"):
                st.text(text)
            
            # הצגת נתונים מובנים
            with st.expander("נתונים מובנים"):
                st.json(data)
            
            # הצגת מטריקות
            render_metric_cards(data)
        else:
            st.error("לא הצלחנו לעבד את הקובץ. אנא נסה שוב.")

import tempfile
import logging

logger = logging.getLogger(__name__)

# Initialize processors
securities_processor = SecuritiesPDFProcessor()

def render_upload_tab():
    """הצגת לשונית העלאת מסמכים."""
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("העלאת מסמכים פיננסיים")
    st.write("העלה דפי חשבון, חשבוניות, דוחות פיננסיים או דוחות ניירות ערך לניתוח.")
    
    # File uploader with multi-file support
    uploaded_files = st.file_uploader(
        "העלה קבצים לניתוח",
        type=["pdf", "xlsx", "xls", "csv"],
        accept_multiple_files=True,
        help="ניתן להעלות מספר קבצים במקביל"
    )
    
    if uploaded_files:
        st.success(f"הועלו {len(uploaded_files)} קבצים")
        
        # Process files
        process_col1, process_col2 = st.columns([3, 1])
        
        with process_col1:
            # Document type selection
            doc_type = st.selectbox(
                "סוג מסמכים", 
                ["אוטומטי", "דפי חשבון/עסקאות", "דוחות ניירות ערך"],
                help="בחר את סוג המסמכים שהעלית כדי לקבל ניתוח מדויק יותר"
            )
            
        with process_col2:
            st.markdown('<div style="height: 35px;"></div>', unsafe_allow_html=True)
            if st.button("עבד מסמכים", type="primary"):
                process_uploaded_files(uploaded_files, doc_type)
        
        # Show upload status
        with st.expander("סטטוס העלאה"):
            for file in uploaded_files:
                st.write(f"- {file.name}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    render_sample_section()

def process_uploaded_files(files, doc_type):
    """Process multiple uploaded files."""
    with st.spinner("מעבד מסמכים..."):
        all_results = []
        
        for file in files:
            try:
                # Convert document type
                document_type = None
                if doc_type == "דפי חשבון/עסקאות":
                    document_type = "statement"
                elif doc_type == "דוחות ניירות ערך":
                    document_type = "securities"
                
                # Auto-detect if needed
                if not document_type:
                    document_type = pdf_processor.auto_detect_document_type(
                        file.getvalue(),
                        filename=file.name
                    )
                
                # Process file
                results, result_type = pdf_processor.process_financial_document(
                    file.getvalue(),
                    document_type=document_type
                )
                
                if results:
                    st.success(f"עובד בהצלחה: {file.name}")
                    all_results.extend(results)
                else:
                    st.warning(f"לא נמצאו נתונים ב: {file.name}")
                    
            except Exception as e:
                st.error(f"שגיאה בעיבוד {file.name}: {str(e)}")
        
        # Update session state with results
        if all_results:
            if document_type == "securities":
                if 'securities_data' not in st.session_state:
                    st.session_state.securities_data = []
                st.session_state.securities_data.extend(all_results)
            else:
                if 'transactions' not in st.session_state:
                    st.session_state.transactions = []
                st.session_state.transactions.extend(all_results)
            
            st.success(f"סה\"כ עובדו {len(all_results)} רשומות")

def render_sample_section():
    """Render sample documents section."""
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("או נסה מסמך לדוגמה")
    
    sample_col1, sample_col2, sample_col3 = st.columns(3)
    
    with sample_col1:
        if st.button("דף חשבון לדוגמה"):
            load_sample_document('bank_statement')
    with sample_col2:
        if st.button("כרטיס אשראי לדוגמה"):
            load_sample_document('credit_card')
    with sample_col3:
        if st.button("דוח השקעות לדוגמה"):
            load_sample_document('securities')
    
    st.markdown('</div>', unsafe_allow_html=True)

def handle_processing_results(filename, results, result_type):
    """Handle the results of document processing."""
    if not results:
        st.error(f"שגיאה בעיבוד המסמך {filename}. נסה שוב או העלה קובץ אחר.")
        return
        
    if result_type == 'transactions':
        handle_transaction_results(filename, results)
    elif result_type == 'securities':
        handle_securities_results(filename, results)

def handle_transaction_results(filename, results):
    """Handle processed transaction results."""
    if not results:
        st.warning(f"המסמך {filename} עובד, אך לא נמצאו עסקאות.")
        return
        
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    
    st.session_state.transactions.extend(results)
    
    # Try AI analysis if available
    if 'agent_runner' in st.session_state and st.session_state.agent_runner:
        try:
            analysis = st.session_state.agent_runner.analyze_finances(results)
            if analysis:
                st.session_state.financial_analysis = analysis
        except Exception as e:
            st.warning(f"לא ניתן היה לנתח את העסקאות עם AI: {str(e)}")
    
    st.success(f"המסמך {filename} עובד בהצלחה! נמצאו {len(results)} עסקאות.")

def handle_securities_results(filename, results):
    """Handle processed securities results."""
    if not results:
        st.warning(f"המסמך {filename} עובד, אך לא נמצאו נתוני ניירות ערך.")
        return
        
    if 'securities_data' not in st.session_state:
        st.session_state.securities_data = []
    
    st.session_state.securities_data.extend(results)
    st.success(f"המסמך {filename} עובד בהצלחה! נמצאו {len(results)} ניירות ערך.")
    
    if st.button("עבור לניתוח ניירות ערך"):
        js = """
        <script>
        window.parent.document.querySelector('a[href="/06_securities"]').click();
        </script>
        """
        st.markdown(js, unsafe_allow_html=True)

def render_sample_documents():
    """Render sample document section."""
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("או נסה מסמך לדוגמה")
    
    sample_col1, sample_col2, sample_col3 = st.columns(3)
    
    with sample_col1:
        if st.button("דף חשבון בנק לדוגמה"):
            load_sample_document('bank_statement')
    with sample_col2:
        if st.button("דף כרטיס אשראי לדוגמה"):
            load_sample_document('credit_card')
    with sample_col3:
        if st.button("דוח השקעות לדוגמה"):
            load_sample_document('securities')
    
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

def process_pdf_file(pdf_path, use_mistral=True):
    """
    עיבוד קובץ PDF והחזרת הטקסט והנתונים המובנים.
    
    Args:
        pdf_path (str): נתיב לקובץ PDF
        use_mistral (bool): האם להשתמש ב-Mistral OCR (ברירת מחדל: True)
        
    Returns:
        tuple: (טקסט שחולץ, נתונים מובנים)
    """
    try:
        if use_mistral:
            # שימוש ב-Mistral OCR
            ocr_text = mistral_extractor.process_pdf_file(pdf_path)
            financial_data = mistral_extractor.extract_financial_data(ocr_text, os.path.basename(pdf_path))
            return ocr_text, financial_data
        else:
            # שימוש במעבד PDF הקיים
            text = pdf_processor.extract_text(pdf_path)
            data = SecuritiesPDFProcessor().process_pdf(pdf_path)
            return text, data
    except Exception as e:
        st.error(f"שגיאה בעיבוד הקובץ: {str(e)}")
        return None, None

if __name__ == "__main__":
    main() 