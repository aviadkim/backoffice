import streamlit as st
from components.metrics import display_metrics, render_metric_cards

def dashboard_page():
    st.title("Dashboard")
    
    # Display metrics using new card system
    metrics = [
        {"label": "מסמכים שעובדו", "value": "150", "color_class": "success"},
        {"label": "אחוז הצלחה", "value": "95%", "color_class": "info"},
        {"label": "משתמשים פעילים", "value": "45", "color_class": "warning"},
        {"label": "זמן עיבוד ממוצע", "value": "2.5s", "color_class": "info"}
    ]
    render_metric_cards(metrics)

def render_assistant_tab():
    """הצגת לשונית העוזר החכם."""
    st.markdown('<div class="startup-card">', unsafe_allow_html=True)
    st.subheader("עוזר פיננסי חכם")
    st.write("שאל שאלות לגבי הנתונים הפיננסיים שלך וקבל תובנות מיידיות.")
    
    # Check if agent runner is available
    if 'agent_runner' not in st.session_state or not st.session_state.agent_runner:
        api_key = st.session_state.get('gemini_api_key')
        if api_key:
            try:
                from utils.agent_runner import FinancialAgentRunner
                st.session_state.agent_runner = FinancialAgentRunner(api_key)
            except Exception as e:
                st.error(f"שגיאה בהתחברות למערכת הסוכנים: {str(e)}")
    
    user_query = st.text_input("שאל שאלה", placeholder="לדוגמה: מה הייתה ההוצאה הגדולה ביותר שלי?")
    
    if 'agent_runner' in st.session_state and st.session_state.agent_runner:
        if user_query:
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
            
            # Process query with agent
            if user_query and user_query.strip():
                transactions = st.session_state.get('transactions', [])
                
                with st.spinner("מעבד את השאלה..."):
                    response = st.session_state.agent_runner.process_chat_query(user_query, transactions)
                
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

if __name__ == "__main__":
    dashboard_page()
