import streamlit as st

def load_sample_document(sample_type):
    """Load sample document data into session state."""
    
    if sample_type == 'bank_statement':
        transactions = [
            {"date": "2023-03-01", "description": "משכורת חודשית", "amount": 8500, "category": "הכנסה"},
            {"date": "2023-03-03", "description": "רכישה בסופרמרקט", "amount": -450.20, "category": "מזון"},
            {"date": "2023-03-05", "description": "תשלום שכירות", "amount": -3200, "category": "דיור"},
            {"date": "2023-03-10", "description": "תדלוק רכב", "amount": -250, "category": "תחבורה"},
            {"date": "2023-03-15", "description": "חשבון חשמל", "amount": -320, "category": "חשבונות"},
            {"date": "2023-03-20", "description": "הפקדה", "amount": 1000, "category": "הכנסה"}
        ]
        _add_to_session_state('transactions', transactions)
        st.success("נטענו נתוני דף חשבון בנק לדוגמה")
        
    elif sample_type == 'credit_card':
        transactions = [
            {"date": "2023-03-02", "description": "קניות באינטרנט", "amount": -320.50, "category": "קניות"},
            {"date": "2023-03-05", "description": "מסעדה", "amount": -180.00, "category": "מזון"},
            {"date": "2023-03-07", "description": "תחנת דלק", "amount": -200.00, "category": "תחבורה"},
            {"date": "2023-03-12", "description": "חנות בגדים", "amount": -450.00, "category": "ביגוד"},
            {"date": "2023-03-15", "description": "סופרמרקט", "amount": -380.20, "category": "מזון"},
            {"date": "2023-03-18", "description": "בית קפה", "amount": -45.00, "category": "בילויים"}
        ]
        _add_to_session_state('transactions', transactions)
        st.success("נטענו נתוני דף כרטיס אשראי לדוגמה")
        
    elif sample_type == 'securities':
        securities = [
            {
                "security_name": "Apple Inc.", 
                "isin": "US0378331005",
                "price": 150.82,
                "quantity": 50,
                "bank": "Bank A",
                "market_value": 7541.00
            },
            # ... more sample securities data ...
        ]
        _add_to_session_state('securities_data', securities)
        st.success("נטענו נתוני דוח השקעות לדוגמה")
        st.info("תוכל לראות את ניתוח ניירות הערך בלשונית 'ניירות ערך'")

def _add_to_session_state(key, data):
    """Add data to session state, initializing if needed."""
    if key not in st.session_state:
        st.session_state[key] = []
    st.session_state[key].extend(data)
