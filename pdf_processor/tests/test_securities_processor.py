import unittest
from unittest.mock import patch, Mock
import pandas as pd
from ..securities_processor import SecuritiesPDFProcessor

class TestSecuritiesPDFProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = SecuritiesPDFProcessor()

    def test_generate_placeholder_isin(self):
        """Test ISIN generation is consistent and valid format"""
        security_name = "Test Security"
        isin = self.processor._generate_placeholder_isin(security_name)
        
        self.assertEqual(len(isin), 12)
        self.assertTrue(isin.startswith('XX'))
        self.assertTrue(isin[2:].isalnum())
        
        # Test consistency
        isin2 = self.processor._generate_placeholder_isin(security_name)
        self.assertEqual(isin, isin2)

    @patch('pdfplumber.open')
    @patch('utils.ocr_processor.extract_text_from_pdf')
    def test_process_pdf(self, mock_extract, mock_pdfplumber):
        """Test PDF processing with mocked dependencies"""
        # Mock OCR results
        mock_extract.return_value = (["Sample text with ISIN: US1234567890"], "text")
        
        # Test basic processing
        result = self.processor.process_pdf("test.pdf", "test_bank")
        self.assertTrue(isinstance(result, list))

if __name__ == '__main__':
    unittest.main()
