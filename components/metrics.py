import streamlit as st

def render_metric_cards(metrics_data):
    """Render a set of metric cards in a responsive grid."""
    
    # Start the metrics container div
    st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
    
    # Render each metric card
    for metric in metrics_data:
        color_class = metric.get("color_class", "")
        st.markdown(f"""
        <div class="metric-card {color_class}">
            <h3>{metric['label']}</h3>
            <div class="value">{metric['value']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Close the container div
    st.markdown('</div>', unsafe_allow_html=True)

def display_metrics():
    """Display key metrics in the dashboard using the new card system"""
    metrics = [
        {"label": "מסמכים שעובדו", "value": "150", "color_class": "success"},
        {"label": "אחוז הצלחה", "value": "95%", "color_class": "info"},
        {"label": "משתמשים פעילים", "value": "45", "color_class": "warning"}
    ]
    render_metric_cards(metrics)
