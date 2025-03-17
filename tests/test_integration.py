import unittest
import os
import tempfile
from pathlib import Path
import pandas as pd
from utils.pdf_integration import PDFProcessingIntegration
from utils.securities_pdf_processor import SecuritiesPDFProcessor
from examples.create_sample_pdf import create_sample_securities_pdf

class TestPDFIntegration(unittest.TestCase):
    """Test complete PDF processing integration."""

    def setUp(self):
        # Create sample PDF for testing
        self.samples_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "samples")
        os.makedirs(self.samples_dir, exist_ok=True)
        create_sample_securities_pdf()
        self.sample_pdf = os.path.join(self.samples_dir, "sample_securities.pdf")
        self.pdf_processor = PDFProcessingIntegration()

    def test_pdf_processor_initialization(self):
        """Test PDF processor initialization."""
        self.assertIsNotNone(self.pdf_processor)
        self.assertIsNotNone(self.pdf_processor.securities_processor)

    def test_process_securities_pdf(self):
        """Test processing a securities PDF."""
        with open(self.sample_pdf, 'rb') as f:
            content = f.read()
            
        # Test auto-detection
        doc_type = self.pdf_processor.auto_detect_document_type(content, "securities_report.pdf")
        self.assertEqual(doc_type, "securities")
        
        # Test processing
        results, result_type = self.pdf_processor.process_financial_document(content, "securities")
        self.assertEqual(result_type, "securities")
        self.assertTrue(len(results) > 0)
        
        # Verify data structure
        first_security = results[0]
        required_fields = ['security_name', 'isin', 'quantity', 'price', 'market_value']
        for field in required_fields:
            self.assertIn(field, first_security)

    def test_securities_extraction(self):
        """Test securities data extraction."""
        processor = SecuritiesPDFProcessor()
        results = processor.process_pdf(self.sample_pdf, "test_bank")
        
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]['security_name'], "Apple Inc.")
        self.assertEqual(results[0]['isin'], "US0378331005")

    def tearDown(self):
        # Cleanup sample files
        try:
            os.unlink(self.sample_pdf)
        except:
            pass

def run_tests():
    """Run all tests and return results."""
    import sys
    import io
    output = io.StringIO()
    runner = unittest.TextTestRunner(stream=output)
    result = runner.run(unittest.makeSuite(TestPDFIntegration))
    return result.wasSuccessful(), output.getvalue()

if __name__ == '__main__':
    unittest.main()
