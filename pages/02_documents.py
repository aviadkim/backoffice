import streamlit as st
from utils.ocr_processor import extract_text_from_pdf, extract_transactions_from_text
from utils.data_storage import DataStorage
from components.header import render_header

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
            if st.button("עבד מסמך", type="primary"):
                with st.spinner("מעבד את המסמך..."):
                    # Save uploaded file to temp location
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # הפעלת מנוע OCR
                    try:
                        if uploaded_file.name.lower().endswith(".pdf"):
                            from utils.ocr_processor import extract_text_from_pdf, extract_transactions_from_text
                            
                            # Process PDF
                            results, result_type = extract_text_from_pdf(tmp_path)
                            
                            if result_type == "table":
                                st.success("המסמך נקרא בהצלחה כטבלה מובנית")
                                # Convert table to transactions
                                transactions = []
                                for table in results:
                                    for _, row in table.iterrows():
                                        try:
                                            # Try to extract values - column names may vary
                                            date = ""
                                            description = ""
                                            amount = 0
                                            
                                            # Look for date column
                                            for col in row.index:
                                                if any(term in col.lower() for term in ['date', 'תאריך']):
                                                    date = str(row[col])
                                                elif any(term in col.lower() for term in ['desc', 'תיאור', 'פרטים']):
                                                    description = str(row[col])
                                                elif any(term in col.lower() for term in ['amount', 'סכום']):
                                                    try:
                                                        amount = float(str(row[col]).replace(',', ''))
                                                    except:
                                                        pass
                                            
                                            if date and (description or amount != 0):
                                                transactions.append({
                                                    "date": date,
                                                    "description": description,
                                                    "amount": amount,
                                                    "category": "לא מסווג"
                                                })
                                        except Exception as e:
                                            st.error(f"שגיאה בעיבוד שורה: {str(e)}")
                                
                                # Store in session state
                                if transactions:
                                    if 'transactions' not in st.session_state:
                                        st.session_state.transactions = []
                                    st.session_state.transactions.extend(transactions)
                                    st.success(f"נמצאו {len(transactions)} עסקאות במסמך")
                                else:
                                    st.warning("לא זוהו עסקאות במסמך")
                            else:
                                st.success("המסמך נקרא בהצלחה באמצעות OCR")
                                text_results = results
                                
                                # Show extracted text in expander
                                with st.expander("טקסט שחולץ"):
                                    st.text("\n\n".join(text_results))
                                
                                # Extract transactions from text
                                transactions = extract_transactions_from_text(text_results)
                                
                                # Store in session state
                                if transactions:
                                    if 'transactions' not in st.session_state:
                                        st.session_state.transactions = []
                                    st.session_state.transactions.extend(transactions)
                                    st.success(f"נמצאו {len(transactions)} עסקאות במסמך")
                                else:
                                    st.warning("לא זוהו עסקאות במסמך. ייתכן שפורמט המסמך אינו נתמך.")
                        elif uploaded_file.name.lower().endswith((".xlsx", ".xls")):
                            # Add Excel processing logic
                            st.info("עיבוד קבצי Excel יתווסף בקרוב")
                        else:
                            st.error("סוג הקובץ אינו נתמך. אנא העלה קובץ PDF או Excel.")
                    except Exception as e:
                        st.error(f"שגיאה בעיבוד המסמך: {str(e)}")
                    
                    # Clean up temp file
                    import os
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
