import streamlit as st

def render_header(title, description=None, with_gradient=True):
    """Render a professional header with optional gradient background."""
    # Load custom CSS
    try:
        with open("assets/css/custom.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # If file doesn't exist, continue without custom CSS
        pass
    
    if with_gradient:
        st.markdown(f"""
        <div class="startup-header">
            <h1>{title}</h1>
            {f"<p>{description}</p>" if description else ""}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.title(title)
        if description:
            st.markdown(description)
