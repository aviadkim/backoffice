import streamlit as st
import tempfile
import os
from utils.pdf_integration import pdf_processor
from utils.samples import load_sample_document

def render_upload_tab():
    """Render the document upload tab interface."""
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("העלאת מסמכים פיננסיים")
    st.write("העלה דפי חשבון, חשבוניות, דוחות פיננסיים או דוחות ניירות ערך לניתוח.")
    
    uploaded_file = st.file_uploader("בחר קובץ PDF או Excel", type=["pdf", "xlsx", "xls", "csv"])
    
    if uploaded_file:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**קובץ:** {uploaded_file.name}")
            doc_type = st.selectbox(
                "סוג מסמך", 
                ["אוטומטי", "דף חשבון/עסקאות", "דוח ניירות ערך"],
                help="בחר את סוג המסמך שהעלית כדי לקבל ניתוח מדויק יותר"
            )
        
        with col2:
            st.markdown('<div style="height: 35px;"></div>', unsafe_allow_html=True)
            if st.button("עבד מסמך", type="primary"):
                process_uploaded_file(uploaded_file, doc_type)

    st.markdown('</div>', unsafe_allow_html=True)
    render_sample_documents()

def process_uploaded_file(uploaded_file, doc_type):
    """Process the uploaded file and update session state."""
    with st.spinner("מעבד מסמך..."):
        # Convert document type selection
        document_type = {
            "דף חשבון/עסקאות": "statement",
            "דוח ניירות ערך": "securities"
        }.get(doc_type)
        
        # Auto-detect if needed
        if doc_type == "אוטומטי":
            document_type = pdf_processor.auto_detect_document_type(
                uploaded_file.getvalue(),
                filename=uploaded_file.name
            )
        
        # Process document
        results, result_type = pdf_processor.process_financial_document(
            uploaded_file.getvalue(),
            document_type=document_type
        )
        
        handle_processing_results(uploaded_file.name, results, result_type)

def handle_processing_results(filename, results, result_type):
    """Handle the results of document processing."""
    if result_type == 'transactions':
        handle_transaction_results(filename, results)
    elif result_type == 'securities':
        handle_securities_results(filename, results)
    else:
        handle_processing_error(filename)

def handle_transaction_results(filename, results):
    """Handle transaction processing results."""
    if results:
        if 'transactions' not in st.session_state:
            st.session_state.transactions = []
        st.session_state.transactions.extend(results)
        
        try_ai_analysis(results)
        st.success(f"המסמך {filename} עובד בהצלחה! נמצאו {len(results)} עסקאות.")
    else:
        st.warning(f"המסמך {filename} עובד, אך לא נמצאו עסקאות.")

def handle_securities_results(filename, results):
    """Handle securities processing results."""
    if results:
        if 'securities_data' not in st.session_state:
            st.session_state.securities_data = []
        st.session_state.securities_data.extend(results)
        
        st.success(f"המסמך {filename} עובד בהצלחה! נמצאו {len(results)} ניירות ערך.")
        if st.button("עבור לניתוח ניירות ערך"):
            st.info("גש ללשונית 'ניירות ערך' לניתוח מפורט")
    else:
        st.warning(f"המסמך {filename} עובד, אך לא נמצאו נתוני ניירות ערך.")

def handle_processing_error(filename):
    """Handle document processing errors."""
    st.error(f"שגיאה בעיבוד המסמך {filename}. נסה שוב או העלה קובץ אחר.")

def try_ai_analysis(results):
    """Try to analyze results with AI agent if available."""
    if 'agent_runner' in st.session_state and st.session_state.agent_runner:
        try:
            analysis = st.session_state.agent_runner.analyze_finances(results)
            if analysis:
                st.session_state.financial_analysis = analysis
        except Exception as e:
            st.warning(f"לא ניתן היה לנתח את העסקאות עם AI: {str(e)}")

def render_sample_documents():
    """Render the sample documents section."""
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
