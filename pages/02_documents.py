import streamlit as st
from utils.ocr_processor import extract_text_from_pdf
from utils.data_storage import DataStorage
from components.header import render_header

def documents_page():
    render_header("ניהול מסמכים", "העלאה, עיבוד וצפייה במסמכים פיננסיים")
    
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("העלאת מסמך חדש")
    
    uploaded_file = st.file_uploader("בחר קובץ PDF או תמונה", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_file:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**שם קובץ:** {uploaded_file.name}")
            st.write(f"**סוג קובץ:** {uploaded_file.type}")
        with col2:
            st.markdown('<div style="height: 35px;"></div>', unsafe_allow_html=True)
            if st.button("עבד מסמך", type="primary"):
                with st.spinner("מעבד את המסמך..."):
                    # הפעלת מנוע OCR
                    try:
                        if uploaded_file.type == "application/pdf":
                            results, result_type = extract_text_from_pdf(uploaded_file)
                            if result_type == "table":
                                st.success("המסמך נקרא בהצלחה כטבלה מובנית")
                                # Convert table to transactions
                                df = results[0]
                                transactions = []
                                for _, row in df.iterrows():
                                    try:
                                        # This would need customization depending on your PDFs
                                        transactions.append({
                                            "date": str(row.get('תאריך', row.get('Date', ''))),
                                            "description": str(row.get('תיאור', row.get('Description', ''))),
                                            "amount": float(row.get('סכום', row.get('Amount', 0))),
                                            "category": "לא מסווג"
                                        })
                                    except:
                                        pass
                                
                                # Store in session state
                                st.session_state.transactions = transactions
                                st.success(f"נמצאו {len(transactions)} עסקאות במסמך")
                            else:
                                st.success("המסמך נקרא בהצלחה באמצעות OCR")
                                text_results = results
                                # Extract transactions from text
                                from utils.ocr_processor import extract_transactions_from_text
                                transactions = extract_transactions_from_text(text_results)
                                if transactions:
                                    st.session_state.transactions = transactions
                                    st.success(f"נמצאו {len(transactions)} עסקאות במסמך")
                                else:
                                    st.warning("לא זוהו עסקאות במסמך. ייתכן שפורמט המסמך אינו נתמך.")
                        else:
                            text = extract_text_from_pdf(uploaded_file)
                            st.success("התמונה נקראה בהצלחה")
                            st.text_area("תוצאת OCR", text, height=200)
                    except Exception as e:
                        st.error(f"שגיאה בעיבוד המסמך: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # רשימת מסמכים קיימים
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("מסמכים קיימים")
    
    # אם אין מסמכים, הצג הודעה ריקה
    if 'documents' not in st.session_state or not st.session_state.get('documents'):
        st.info("עדיין לא הועלו מסמכים. העלה מסמך חדש כדי להתחיל.")
    else:
        # הצג טבלת מסמכים
        st.write("טבלת המסמכים תוצג כאן")
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    documents_page()
