import streamlit as st
import pandas as pd
import time
import os
import tempfile
from utils.pdf_integration import pdf_processor
import logging
import io
import base64
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def display_progress(current, total, message):
    """Display progress in Streamlit."""
    if 'progress_bar' not in st.session_state:
        st.session_state.progress_bar = st.progress(0)
        st.session_state.status_text = st.empty()
    
    # Update progress
    progress = current / total if total > 0 else 0
    st.session_state.progress_bar.progress(progress)
    st.session_state.status_text.text(f"{message} ({current}/{total})")
    
    # If completed, reset
    if current >= total:
        time.sleep(1)  # Give user time to see 100%
        st.session_state.progress_bar.empty()
        st.session_state.status_text.empty()

def get_download_link(file_path, file_name):
    """Generate a download link for a file."""
    with open(file_path, 'rb') as f:
        data = f.read()
    
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">Download {file_name}</a>'
    return href

def process_uploaded_file(uploaded_file, document_type=None, use_chunking=True):
    """
    Process an uploaded file with progress feedback.
    
    Args:
        uploaded_file: The uploaded file object
        document_type: Type of document (statement, securities, etc.)
        use_chunking: Whether to use chunked processing for large files
        
    Returns:
        Extracted data, type of data (transactions, securities)
    """
    start_time = time.time()
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_path = temp_file.name
    
    try:
        # Auto-detect document type if not provided
        if not document_type:
            st.info("Detecting document type...")
            document_type = pdf_processor.auto_detect_document_type(
                temp_path, 
                filename=uploaded_file.name
            )
            st.info(f"Detected document type: {document_type}")
        
        # Process the document
        if use_chunking:
            st.info("Using chunked processing for optimal memory usage...")
            result, result_type = pdf_processor.process_document_in_chunks(
                temp_path,
                chunk_size=5,
                document_type=document_type,
                callback=display_progress
            )
        else:
            st.info("Processing document...")
            result, result_type = pdf_processor.process_financial_document(
                temp_path,
                document_type=document_type,
                callback=display_progress
            )
        
        elapsed_time = time.time() - start_time
        
        # Return the results
        return result, result_type, elapsed_time
    
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
        except:
            pass

def main():
    """Main function for the document upload page."""
    st.title("Enhanced Document Upload")
    
    # Document type selection
    document_type = st.radio(
        "Document Type",
        ["Auto-detect", "Bank Statement", "Credit Card", "Securities"]
    )
    
    # Processing options
    use_chunking = st.checkbox("Use chunked processing (recommended for large files)", value=True)
    
    # File uploader
    uploaded_file = st.file_uploader("Upload a financial document", type=["pdf"])
    
    if uploaded_file is not None:
        # Display file info
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / 1024:.2f} KB"
        }
        st.write("File Details:")
        st.json(file_details)
        
        # Process button
        if st.button("Process Document"):
            with st.spinner("Processing document..."):
                try:
                    # Map selected document type to internal type
                    type_mapping = {
                        "Auto-detect": None,
                        "Bank Statement": "statement",
                        "Credit Card": "statement",
                        "Securities": "securities"
                    }
                    
                    selected_type = type_mapping[document_type]
                    
                    # Process the document
                    result, result_type, elapsed_time = process_uploaded_file(
                        uploaded_file,
                        document_type=selected_type,
                        use_chunking=use_chunking
                    )
                    
                    # Display results based on type
                    if result_type == 'transactions':
                        st.success(f"Successfully processed document in {elapsed_time:.2f} seconds")
                        
                        # Store in session state
                        st.session_state.transactions = result
                        
                        # Show summary
                        if result:
                            summary = {
                                "Total Transactions": len(result),
                                "Date Range": f"{result[0]['date']} to {result[-1]['date']}" if len(result) > 1 else result[0]['date'],
                                "Processing Time": f"{elapsed_time:.2f} seconds"
                            }
                            
                            st.subheader("Processing Summary")
                            st.json(summary)
                            
                            # Show transactions in table
                            st.subheader("Extracted Transactions")
                            transactions_df = pd.DataFrame(result)
                            st.dataframe(transactions_df)
                            
                            # Export options
                            st.subheader("Export Options")
                            
                            # Create CSV for download
                            csv = transactions_df.to_csv(index=False)
                            csv_file = io.StringIO()
                            transactions_df.to_csv(csv_file, index=False)
                            
                            st.download_button(
                                label="Download as CSV",
                                data=csv_file.getvalue(),
                                file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                            
                            # Navigation options
                            st.subheader("What would you like to do next?")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Analyze Transactions"):
                                    st.session_state.page = "transaction_analysis"
                                    st.experimental_rerun()
                            
                            with col2:
                                if st.button("Get Financial Advice"):
                                    st.session_state.page = "financial_advice"
                                    st.experimental_rerun()
                    
                    elif result_type == 'securities':
                        st.success(f"Successfully processed securities document in {elapsed_time:.2f} seconds")
                        
                        # Store in session state
                        st.session_state.securities = result
                        
                        # Show summary
                        if result:
                            summary = {
                                "Total Securities": len(result),
                                "Processing Time": f"{elapsed_time:.2f} seconds"
                            }
                            
                            st.subheader("Processing Summary")
                            st.json(summary)
                            
                            # Show securities in table
                            st.subheader("Extracted Securities")
                            securities_df = pd.DataFrame(result)
                            st.dataframe(securities_df)
                            
                            # Export options
                            st.subheader("Export Options")
                            
                            # Create CSV for download
                            csv = securities_df.to_csv(index=False)
                            csv_file = io.StringIO()
                            securities_df.to_csv(csv_file, index=False)
                            
                            st.download_button(
                                label="Download as CSV",
                                data=csv_file.getvalue(),
                                file_name=f"securities_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                            
                            # Navigation options
                            st.subheader("What would you like to do next?")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Analyze Securities"):
                                    st.session_state.page = "securities_analysis"
                                    st.experimental_rerun()
                            
                            with col2:
                                if st.button("Get Portfolio Advice"):
                                    st.session_state.page = "portfolio_advice"
                                    st.experimental_rerun()
                    
                    else:
                        st.error(f"Unknown result type: {result_type}")
                
                except Exception as e:
                    st.error(f"Error processing document: {str(e)}")
                    logger.error(f"Error processing document: {str(e)}", exc_info=True)
    
    # Display instructions
    with st.expander("Instructions"):
        st.markdown("""
        ### How to use this page
        
        1. **Select document type** - Choose the type of document you're uploading or use auto-detect
        2. **Upload a document** - Click 'Browse files' to upload a PDF document
        3. **Process the document** - Click 'Process Document' to extract data
        4. **Review the results** - Check the extracted data for accuracy
        5. **Export or continue** - Download the data or proceed to analysis
        
        ### Supported Documents
        
        - Bank statements
        - Credit card statements
        - Securities/investment portfolio reports
        
        ### Tips for Best Results
        
        - Use high-quality PDFs for best extraction results
        - For large files, keep the "Use chunked processing" option enabled
        - If document type detection fails, manually select the correct type
        """)

if __name__ == "__main__":
    main()