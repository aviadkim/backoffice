import streamlit as st
from utils.ocr_processor import extract_text_from_pdf, extract_transactions_from_text
from utils.data_storage import DataStorage
from components.header import render_header
from utils.agent_runner import FinancialAgentRunner
import tempfile
import os

def documents_page():
    render_header("ניהול מסמכים", "העלאה, עיבוד וצפייה במסמכים פיננסיים")
    
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("העלאת מסמך חדש")
    
    uploaded_file = st.file_uploader("בחר קובץ PDF או תמונה", type=["pdf", "png", "jpg", "jpeg", "xlsx", "xls"])
    if uploaded_file:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**שם קובץ:** {uploaded_file.name}")
            st.write(f"**סוג קובץ:** {uploaded_file.type}")
        with col2:
            st.markdown('<div style="height: 35px;"></div>', unsafe_allow_html=True)
            
            if 'agent_runner' not in st.session_state:
                try:
                    # Get API key from sidebar or environment
                    api_key = st.session_state.get('gemini_api_key')
                    st.session_state.agent_runner = FinancialAgentRunner(api_key)
                except Exception as e:
                    st.error(f"שגיאה בהתחברות למערכת הסוכנים: {str(e)}")
                    st.session_state.agent_runner = None

            if st.button("עבד מסמך", type="primary"):
                with st.spinner("מעבד את המסמך..."):
                    # Save uploaded file to temp location
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    try:
                        # Process using OCR
                        from utils.ocr_processor import extract_text_from_pdf
                        results, result_type = extract_text_from_pdf(tmp_path)
                        
                        if result_type == "text":
                            # Extracted as text
                            text_results = "\n\n".join(results)
                            
                            # Show extracted text in expander
                            with st.expander("טקסט שחולץ"):
                                st.text(text_results)
                            
                            # Process with AI agent if available
                            if st.session_state.agent_runner:
                                with st.spinner("מעבד עם AI..."):
                                    transactions = st.session_state.agent_runner.process_document(text_results)
                                    
                                    if transactions:
                                        if 'transactions' not in st.session_state:
                                            st.session_state.transactions = []
                                        st.session_state.transactions.extend(transactions)
                                        
                                        # Also do financial analysis
                                        analysis = st.session_state.agent_runner.analyze_finances(transactions)
                                        if analysis:
                                            st.session_state.financial_analysis = analysis
                                        
                                        st.success(f"נמצאו {len(transactions)} עסקאות במסמך")
                                    else:
                                        st.warning("לא זוהו עסקאות במסמך")
                            else:
                                # Fallback to regular extraction
                                from utils.ocr_processor import extract_transactions_from_text
                                transactions = extract_transactions_from_text(results)
                                # Add to session state as before
                        # Handle other result types (table etc.)
                        
                    except Exception as e:
                        st.error(f"שגיאה בעיבוד המסמך: {str(e)}")
                    
                    # Clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # רשימת מסמכים קיימים
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("עסקאות שזוהו")
    
    # אם אין עסקאות, הצג הודעה ריקה
    if 'transactions' not in st.session_state or not st.session_state.get('transactions'):
        st.info("עדיין לא נמצאו עסקאות. העלה מסמך חדש כדי להתחיל.")
    else:
        # הצג טבלת עסקאות
        import pandas as pd
        transactions_df = pd.DataFrame(st.session_state.transactions)
        st.dataframe(transactions_df, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("נקה עסקאות", type="secondary"):
                st.session_state.transactions = []
                st.experimental_rerun()
        with col2:
            st.download_button(
                "ייצא עסקאות (CSV)",
                data=transactions_df.to_csv(index=False),
                file_name="transactions.csv",
                mime="text/csv"
            )
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    documents_page()
