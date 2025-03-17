import unittest
import os
import sys
from pathlib import Path
import pandas as pd
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestPDFProcessing(unittest.TestCase):
    """Test suite for PDF processing functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Create test environment and sample files"""
        logger.info("Setting up test environment...")
        
        # Create samples directory if it doesn't exist
        cls.samples_dir = Path(__file__).parent.parent / "samples"
        cls.samples_dir.mkdir(exist_ok=True)
        
        # Create sample files
        cls._create_sample_files()
        
        # Initialize processors
        from utils.pdf_integration import PDFProcessingIntegration
        cls.processor = PDFProcessingIntegration()
    
    def test_01_pdf_creation(self):
        """Test if sample PDF files were created correctly"""
        logger.info("Testing PDF creation...")
        self.assertTrue(os.path.exists(self.sample_securities_pdf))
        self.assertTrue(os.path.exists(self.sample_statement_pdf))
        self.assertTrue(os.path.getsize(self.sample_securities_pdf) > 0)
        self.assertTrue(os.path.getsize(self.sample_statement_pdf) > 0)
    
    def test_02_text_extraction(self):
        """Test basic text extraction"""
        logger.info("Testing text extraction...")
        from utils.ocr_processor import extract_text_from_pdf
        
        text, result_type = extract_text_from_pdf(self.sample_statement_pdf)
        self.assertIsNotNone(text)
        self.assertTrue(len(text) > 0)
        logger.info(f"Extracted text length: {len(text)}")
        logger.info(f"First 100 chars: {str(text)[:100]}")
    
    def test_03_securities_processing(self):
        """Test securities PDF processing"""
        logger.info("Testing securities processing...")
        
        with open(self.sample_securities_pdf, 'rb') as f:
            content = f.read()
            
        doc_type = self.processor.auto_detect_document_type(content, "securities_test.pdf")
        self.assertEqual(doc_type, "securities")
        
        results, result_type = self.processor.process_financial_document(content, "securities")
        self.assertEqual(result_type, "securities")
        self.assertTrue(len(results) > 0)
        
        logger.info(f"Found {len(results)} securities")
        if results:
            logger.info(f"First security: {results[0]}")
    
    def test_04_statement_processing(self):
        """Test bank statement processing"""
        logger.info("Testing statement processing...")
        
        with open(self.sample_statement_pdf, 'rb') as f:
            content = f.read()
            
        doc_type = self.processor.auto_detect_document_type(content, "statement_test.pdf")
        self.assertEqual(doc_type, "statement")
        
        results, result_type = self.processor.process_financial_document(content, "statement")
        self.assertEqual(result_type, "transactions")
        
        logger.info(f"Found {len(results)} transactions")
        if results:
            logger.info(f"First transaction: {results[0]}")
    
    @classmethod
    def _create_sample_files(cls):
        """Create sample PDF files for testing"""
        from fpdf import FPDF
        
        # Create securities PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Securities Holdings Report", ln=1, align="C")
        pdf.cell(200, 10, txt="ISIN: US0378331005", ln=1, align="L")
        pdf.cell(200, 10, txt="Apple Inc. - 100 shares @ $150.25", ln=1, align="L")
        cls.sample_securities_pdf = str(cls.samples_dir / "test_securities.pdf")
        pdf.output(cls.sample_securities_pdf)
        
        # Create statement PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Bank Statement", ln=1, align="C")
        pdf.cell(200, 10, txt="03/15/2024 Payment -120.50", ln=1, align="L")
        pdf.cell(200, 10, txt="03/16/2024 Deposit +1500.00", ln=1, align="L")
        cls.sample_statement_pdf = str(cls.samples_dir / "test_statement.pdf")
        pdf.output(cls.sample_statement_pdf)
        
        logger.info(f"Created test files in {cls.samples_dir}")

def run_tests():
    """Run all tests with detailed logging"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPDFProcessing)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    print(f"\n=== Starting PDF Processing Tests at {datetime.now()} ===\n")
    success = run_tests()
    if not success:
        sys.exit(1)
