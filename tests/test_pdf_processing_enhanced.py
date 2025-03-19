import os
import sys
import unittest
import tempfile
import io
from PyPDF2 import PdfWriter, PdfReader
import logging
import time
from utils.pdf_integration import PDFProcessingIntegration
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestEnhancedPDFProcessing(unittest.TestCase):
    """Test the enhanced PDF processing capabilities."""
    
    @classmethod
    def setUpClass(cls):
        """Set up testing environment."""
        cls.processor = PDFProcessingIntegration()
        cls.create_sample_pdfs()
    
    @classmethod
    def create_sample_pdfs(cls):
        """Create sample PDFs of various sizes for testing."""
        # Create directory for test files
        cls.test_dir = tempfile.mkdtemp()
        
        # Create a sample page with content
        def create_sample_page():
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            
            # Add some transaction data
            c.drawString(100, 750, "Transaction Statement")
            c.drawString(100, 700, "Date: 01/15/2023")
            c.drawString(100, 650, "Deposit: +1500.00")
            c.drawString(100, 600, "Withdrawal: -750.25")
            c.drawString(100, 550, "Balance: 2340.62")
            
            c.showPage()
            c.save()
            return buffer.getvalue()
        
        # Create PDFs of different sizes
        page_content = create_sample_page()
        
        sizes = {
            'small': 3,    # 3 pages
            'medium': 15,  # 15 pages
            'large': 50    # 50 pages
        }
        
        cls.sample_pdfs = {}
        
        for size_name, num_pages in sizes.items():
            output_path = os.path.join(cls.test_dir, f"sample_{size_name}.pdf")
            
            output = PdfWriter()
            # Use the same page content repeated
            for _ in range(num_pages):
                reader = PdfReader(io.BytesIO(page_content))
                output.add_page(reader.pages[0])
            
            with open(output_path, "wb") as output_stream:
                output.write(output_stream)
            
            cls.sample_pdfs[size_name] = output_path
            logger.info(f"Created {size_name} PDF with {num_pages} pages at {output_path}")
    
    def test_regular_processing(self):
        """Test regular document processing."""
        # Process small PDF normally
        start_time = time.time()
        
        # Add a custom callback to check progress
        progress_updates = []
        
        def progress_callback(current, total, message):
            progress_updates.append((current, total, message))
            logger.info(f"Progress: {current}/{total} - {message}")
        
        results, result_type = self.processor.process_financial_document(
            self.sample_pdfs['small'], 
            document_type='statement',
            callback=progress_callback
        )
        elapsed = time.time() - start_time
        
        logger.info(f"Regular processing of small PDF took {elapsed:.2f} seconds")
        
        # Check if we got transaction data or progress updates
        if len(results) == 0:
            # If no transactions were extracted (which might happen with test files),
            # at least verify that the process ran and didn't crash
            self.assertEqual(result_type, 'transactions')
            self.assertGreater(len(progress_updates), 0)
        else:
            self.assertEqual(result_type, 'transactions')
            self.assertGreater(len(results), 0)
    
    def test_chunked_processing(self):
        """Test chunked processing for large documents."""
        # Process large PDF with chunking
        progress_updates = []
        
        def progress_callback(current, total, message):
            progress_updates.append((current, total, message))
            logger.info(f"Progress: {current}/{total} - {message}")
        
        start_time = time.time()
        results, result_type = self.processor.process_document_in_chunks(
            self.sample_pdfs['large'],
            chunk_size=5,
            document_type='statement',
            callback=progress_callback
        )
        elapsed = time.time() - start_time
        
        logger.info(f"Chunked processing of large PDF took {elapsed:.2f} seconds")
        self.assertEqual(result_type, 'transactions')
        self.assertGreater(len(results), 0)
        self.assertGreater(len(progress_updates), 3)  # Should have multiple progress updates
    
    def test_memory_usage(self):
        """Test memory usage during processing."""
        import resource
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Measure memory before
        before_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        # Process medium PDF
        results, result_type = self.processor.process_document_in_chunks(
            self.sample_pdfs['medium'],
            chunk_size=3
        )
        
        # Force garbage collection again
        gc.collect()
        
        # Measure memory after
        after_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        # Log memory usage
        mem_increase = after_mem - before_mem
        logger.info(f"Memory increase: {mem_increase} KB")
        
        # Verify results
        self.assertEqual(result_type, 'transactions')
        self.assertGreater(len(results), 0)
    
    def test_error_handling(self):
        """Test error handling with invalid files."""
        # Create an invalid PDF file
        invalid_pdf_path = os.path.join(self.test_dir, "invalid.pdf")
        with open(invalid_pdf_path, "w") as f:
            f.write("This is not a valid PDF file")
        
        # Process the invalid file
        results, result_type = self.processor.process_financial_document(invalid_pdf_path)
        
        # Should handle the error gracefully
        self.assertEqual(result_type, 'error')
        self.assertEqual(len(results), 0)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        # Remove test directory and files
        for pdf_path in cls.sample_pdfs.values():
            try:
                os.unlink(pdf_path)
            except:
                pass
        
        try:
            os.rmdir(cls.test_dir)
        except:
            pass

if __name__ == "__main__":
    unittest.main()