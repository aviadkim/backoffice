import streamlit as st

def render_sidebar():
    """Render a professional sidebar with navigation and configuration."""
    with st.sidebar:
        render_logo()
        
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        
        # Main navigation
        st.markdown("### ניווט")
        selected_page = st.radio(
            "עבור אל",
            ["לוח בקרה", "מסמכים", "ניתוח", "הגדרות"],
            label_visibility="collapsed"
        )
        
        st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
        
        # API Configuration section
        st.markdown("### הגדרות API")
        api_key = st.text_input("מפתח Gemini API", type="password", help="הזן את מפתח ה-API של Gemini כדי להפעיל תכונות AI")
        
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        
        # Options section
        st.markdown("### אפשרויות")
        auto_categorize = st.toggle("סיווג אוטומטי של עסקאות", value=True)
        dark_mode = st.toggle("מצב כהה", value=False)
        
        st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
        
        # Account section at bottom
        render_account_info()
        
        return {
            "selected_page": selected_page,
            "api_key": api_key,
            "auto_categorize": auto_categorize,
            "dark_mode": dark_mode
        }

def render_logo():
    """Render the app logo and name."""
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <div style="margin-right: 10px; background-color: #4F46E5; width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
            <span style="color: white; font-weight: bold; font-size: 20px;">F</span>
        </div>
        <div>
            <div style="font-weight: 600; font-size: 1.25rem; color: #111827;">FinAnalyzer</div>
            <div style="font-size: 0.75rem; color: #6B7280;">ניתוח פיננסי חכם</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_account_info():
    """Render account information at bottom of sidebar."""
    st.markdown("""
    <div style="display: flex; align-items: center;">
        <div style="width: 30px; height: 30px; border-radius: 15px; background-color: #E5E7EB; display: flex; align-items: center; justify-content: center; margin-right: 10px;">
            <span style="color: #4B5563;">A</span>
        </div>
        <div>
            <div style="font-weight: 500; font-size: 0.875rem;">חשבון חינמי</div>
            <div style="font-size: 0.75rem; color: #6B7280;">שדרג לתכונות נוספות</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.button("שדרג לגרסה המקצועית", type="primary")
