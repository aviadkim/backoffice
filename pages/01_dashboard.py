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

if __name__ == "__main__":
    dashboard_page()
