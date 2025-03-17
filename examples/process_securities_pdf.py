import logging
import sys
from pathlib import Path
import os
# Add parent directory to path to find pdf_processor module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf_processor import SecuritiesPDFProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_statement(pdf_path: str, bank_name: str = None) -> None:
    """
    Process a securities statement PDF and display the results.
    
    Args:
        pdf_path: Path to the PDF file
        bank_name: Optional bank name to specify format
    """
    try:
        # Initialize processor
        processor = SecuritiesPDFProcessor()
        
        # Validate file exists
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Process the PDF
        logger.info(f"Processing PDF: {pdf_path}")
        results = processor.process_pdf(pdf_path, bank_name)
        
        # Display results
        if not results:
            logger.warning("No securities data found in PDF")
            return
            
        logger.info(f"Found {len(results)} securities:")
        for security in results:
            print("\nSecurity:")
            print(f"  Name: {security.get('security_name', 'N/A')}")
            print(f"  ISIN: {security.get('isin', 'N/A')}")
            print(f"  Quantity: {security.get('quantity', 'N/A')}")
            print(f"  Price: {security.get('price', 'N/A')}")
            print(f"  Market Value: {security.get('market_value', 'N/A')}")
            print(f"  Bank: {security.get('bank', 'N/A')}")
            
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Get the samples directory path
    samples_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "samples")
    default_pdf = os.path.join(samples_dir, "sample_securities.pdf")
    
    # Use command line args or defaults
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else default_pdf
    bank_name = sys.argv[2] if len(sys.argv) > 2 else "demo"
    
    if not os.path.exists(samples_dir):
        os.makedirs(samples_dir)
        logger.info(f"Created samples directory: {samples_dir}")
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        logger.info(f"Please place a sample PDF file at: {default_pdf}")
        logger.info("Usage: python process_securities_pdf.py [pdf_path] [bank_name]")
        sys.exit(1)
    
    process_statement(pdf_path, bank_name)
