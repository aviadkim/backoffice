import os
import sys
import unittest
import tempfile
import io
import logging
import json
import time
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from utils.pdf_integration import PDFProcessingIntegration
from utils.agent_runner import FinancialAgentRunner
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_full_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class FullSystemTest:
    """
    Comprehensive test of the entire FinAnalyzer system.
    Tests PDF processing, agent functionality, and end-to-end workflows.
    """
    
    def __init__(self):
        self.pdf_processor = PDFProcessingIntegration()
        
        # Initialize agent runner if API key is available
        self.agent_runner = None
        if GEMINI_API_KEY:
            self.agent_runner = FinancialAgentRunner(api_key=GEMINI_API_KEY)
        else:
            logger.warning("No Gemini API key found. Agent tests will be skipped.")
        
        # Create test directory
        self.test_dir = tempfile.mkdtemp()
        logger.info(f"Created test directory: {self.test_dir}")
        
        # Create sample files
        self.create_sample_files()
    
    def create_sample_files(self):
        """Create sample files for testing."""
        self.sample_files = {}
        
        # Create a bank statement PDF
        bank_statement_path = os.path.join(self.test_dir, "bank_statement.pdf")
        self._create_bank_statement_pdf(bank_statement_path)
        self.sample_files['bank_statement'] = bank_statement_path
        
        # Create a securities PDF
        securities_path = os.path.join(self.test_dir, "securities.pdf")
        self._create_securities_pdf(securities_path)
        self.sample_files['securities'] = securities_path
        
        # Create a large PDF (30 pages)
        large_pdf_path = os.path.join(self.test_dir, "large_document.pdf")
        self._create_large_pdf(large_pdf_path, 30)
        self.sample_files['large_document'] = large_pdf_path
    
    def _create_bank_statement_pdf(self, output_path):
        """Create a sample bank statement PDF."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(output_path, pagesize=letter)
        
        # Title
        c.setFont('Helvetica-Bold', 18)
        c.drawString(100, 750, "Bank Statement")
        c.setFont('Helvetica', 12)
        c.drawString(100, 730, "Account: 1234-5678")
        c.drawString(100, 710, "Date: 01/01/2023 - 01/31/2023")
        
        # Transactions
        c.setFont('Helvetica-Bold', 14)
        c.drawString(100, 670, "Transactions:")
        
        transactions = [
            ("01/05/2023", "Salary Deposit", "+8,500.00"),
            ("01/10/2023", "Rent Payment", "-3,200.00"),
            ("01/15/2023", "Grocery Store", "-450.75"),
            ("01/20/2023", "Electricity Bill", "-210.25"),
            ("01/25/2023", "Internet Bill", "-89.99"),
            ("01/28/2023", "Restaurant", "-125.40")
        ]
        
        y_position = 650
        for date, desc, amount in transactions:
            c.setFont('Helvetica', 12)
            c.drawString(100, y_position, date)
            c.drawString(200, y_position, desc)
            c.drawString(400, y_position, amount)
            y_position -= 20
        
        # Summary
        c.setFont('Helvetica-Bold', 14)
        c.drawString(100, 500, "Summary:")
        c.setFont('Helvetica', 12)
        c.drawString(100, 480, "Starting Balance: 2,450.00")
        c.drawString(100, 460, "Total Credits: +8,500.00")
        c.drawString(100, 440, "Total Debits: -4,076.39")
        c.drawString(100, 420, "Ending Balance: 6,873.61")
        
        c.save()
        logger.info(f"Created sample bank statement PDF: {output_path}")
    
    def _create_securities_pdf(self, output_path):
        """Create a sample securities portfolio PDF."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(output_path, pagesize=letter)
        
        # Title
        c.setFont('Helvetica-Bold', 18)
        c.drawString(100, 750, "Securities Portfolio")
        c.setFont('Helvetica', 12)
        c.drawString(100, 730, "Account: 5678-1234")
        c.drawString(100, 710, "Date: 01/31/2023")
        
        # Securities
        c.setFont('Helvetica-Bold', 14)
        c.drawString(100, 670, "Holdings:")
        
        securities = [
            ("Apple Inc.", "US0378331005", "100", "150.25", "15,025.00"),
            ("Microsoft Corp", "US5949181045", "50", "280.50", "14,025.00"),
            ("Amazon.com Inc", "US0231351067", "30", "125.75", "3,772.50"),
            ("Tesla Inc", "US88160R1014", "75", "225.30", "16,897.50")
        ]
        
        # Column headers
        c.setFont('Helvetica-Bold', 12)
        c.drawString(100, 650, "Security Name")
        c.drawString(225, 650, "ISIN")
        c.drawString(350, 650, "Quantity")
        c.drawString(400, 650, "Price")
        c.drawString(450, 650, "Market Value")
        
        # Data rows
        y_position = 630
        for name, isin, qty, price, value in securities:
            c.setFont('Helvetica', 12)
            c.drawString(100, y_position, name)
            c.drawString(225, y_position, isin)
            c.drawString(350, y_position, qty)
            c.drawString(400, y_position, price)
            c.drawString(450, y_position, value)
            y_position -= 20
        
        # Summary
        c.setFont('Helvetica-Bold', 14)
        c.drawString(100, 500, "Summary:")
        c.setFont('Helvetica', 12)
        c.drawString(100, 480, "Total Market Value: $49,720.00")
        c.drawString(100, 460, "Number of Securities: 4")
        
        c.save()
        logger.info(f"Created sample securities PDF: {output_path}")
    
    def _create_large_pdf(self, output_path, num_pages):
        """Create a large PDF with multiple pages."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a temporary file for the first page
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Create the first page template
        c = canvas.Canvas(temp_path, pagesize=letter)
        c.setFont('Helvetica-Bold', 18)
        c.drawString(100, 750, "Bank Statement - Page 1")
        c.setFont('Helvetica', 12)
        c.drawString(100, 730, "Account: 1234-5678")
        c.drawString(100, 710, "Date: 01/01/2023 - 01/31/2023")
        
        # Add some transactions
        c.setFont('Helvetica-Bold', 14)
        c.drawString(100, 670, "Transactions:")
        
        transactions = [
            ("01/05/2023", "Salary Deposit", "+8,500.00"),
            ("01/10/2023", "Rent Payment", "-3,200.00"),
            ("01/15/2023", "Grocery Store", "-450.75"),
            ("01/20/2023", "Electricity Bill", "-210.25"),
            ("01/25/2023", "Internet Bill", "-89.99"),
            ("01/28/2023", "Restaurant", "-125.40")
        ]
        
        y_position = 650
        for date, desc, amount in transactions:
            c.setFont('Helvetica', 12)
            c.drawString(100, y_position, date)
            c.drawString(200, y_position, desc)
            c.drawString(400, y_position, amount)
            y_position -= 20
            
        c.save()
        
        # Read the first page
        with open(temp_path, 'rb') as f:
            first_page_content = f.read()
            
        # Clean up
        os.unlink(temp_path)
        
        # Create multi-page PDF
        pdf_writer = PdfWriter()
        
        # Add pages
        for page_num in range(num_pages):
            # For each page, modify the page number and add to the document
            page_content = first_page_content.replace(b"Page 1", f"Page {page_num+1}".encode())
            
            page_reader = PdfReader(io.BytesIO(page_content))
            pdf_writer.add_page(page_reader.pages[0])
        
        # Write the output
        with open(output_path, 'wb') as f:
            pdf_writer.write(f)
            
        logger.info(f"Created large PDF with {num_pages} pages: {output_path}")
    
    def run_pdf_processing_tests(self):
        """Run tests for PDF processing."""
        logger.info("=== Starting PDF Processing Tests ===")
        
        # Track results
        results = {
            'bank_statement': {'status': 'Not Run', 'details': ''},
            'securities': {'status': 'Not Run', 'details': ''},
            'large_document': {'status': 'Not Run', 'details': ''},
            'chunked_processing': {'status': 'Not Run', 'details': ''}
        }
        
        # Test bank statement processing
        try:
            logger.info("Processing bank statement PDF...")
            start_time = time.time()
            
            transactions, result_type = self.pdf_processor.process_financial_document(
                self.sample_files['bank_statement'],
                document_type='statement'
            )
            
            elapsed = time.time() - start_time
            
            if result_type == 'transactions' and len(transactions) > 0:
                results['bank_statement'] = {
                    'status': 'Success',
                    'details': f"Extracted {len(transactions)} transactions in {elapsed:.2f} seconds"
                }
            else:
                results['bank_statement'] = {
                    'status': 'Failure',
                    'details': f"Failed to extract transactions, result_type={result_type}"
                }
            
            logger.info(f"Bank statement processing result: {results['bank_statement']['status']}")
            
        except Exception as e:
            results['bank_statement'] = {'status': 'Error', 'details': str(e)}
            logger.error(f"Error processing bank statement: {str(e)}", exc_info=True)
        
        # Test securities PDF processing
        try:
            logger.info("Processing securities PDF...")
            start_time = time.time()
            
            securities, result_type = self.pdf_processor.process_financial_document(
                self.sample_files['securities'],
                document_type='securities'
            )
            
            elapsed = time.time() - start_time
            
            if result_type == 'securities' and len(securities) > 0:
                results['securities'] = {
                    'status': 'Success',
                    'details': f"Extracted {len(securities)} securities in {elapsed:.2f} seconds"
                }
            else:
                results['securities'] = {
                    'status': 'Failure',
                    'details': f"Failed to extract securities, result_type={result_type}"
                }
            
            logger.info(f"Securities processing result: {results['securities']['status']}")
            
        except Exception as e:
            results['securities'] = {'status': 'Error', 'details': str(e)}
            logger.error(f"Error processing securities: {str(e)}", exc_info=True)
        
        # Test large document processing
        try:
            logger.info("Processing large document (standard method)...")
            start_time = time.time()
            
            transactions, result_type = self.pdf_processor.process_financial_document(
                self.sample_files['large_document'],
                document_type='statement'
            )
            
            elapsed = time.time() - start_time
            
            if result_type == 'transactions':
                results['large_document'] = {
                    'status': 'Success',
                    'details': f"Processed {len(transactions)} items in {elapsed:.2f} seconds"
                }
            else:
                results['large_document'] = {
                    'status': 'Failure',
                    'details': f"Failed to process large document, result_type={result_type}"
                }
            
            logger.info(f"Large document processing result: {results['large_document']['status']}")
            
        except Exception as e:
            results['large_document'] = {'status': 'Error', 'details': str(e)}
            logger.error(f"Error processing large document: {str(e)}", exc_info=True)
        
        # Test chunked processing
        try:
            logger.info("Processing large document with chunking...")
            progress_updates = []
            
            def progress_callback(current, total, message):
                progress_updates.append((current, total, message))
                logger.info(f"Progress: {current}/{total} - {message}")
            
            start_time = time.time()
            
            transactions, result_type = self.pdf_processor.process_document_in_chunks(
                self.sample_files['large_document'],
                chunk_size=5,
                document_type='statement',
                callback=progress_callback
            )
            
            elapsed = time.time() - start_time
            
            if result_type == 'transactions':
                results['chunked_processing'] = {
                    'status': 'Success',
                    'details': f"Processed {len(transactions)} items in {elapsed:.2f} seconds with {len(progress_updates)} progress updates"
                }
            else:
                results['chunked_processing'] = {
                    'status': 'Failure',
                    'details': f"Failed to process with chunking, result_type={result_type}"
                }
            
            logger.info(f"Chunked processing result: {results['chunked_processing']['status']}")
            
        except Exception as e:
            results['chunked_processing'] = {'status': 'Error', 'details': str(e)}
            logger.error(f"Error in chunked processing: {str(e)}", exc_info=True)
        
        return results
    
    def run_agent_tests(self):
        """Run tests for AI agent functionality."""
        logger.info("=== Starting Agent Tests ===")
        
        if not self.agent_runner:
            logger.warning("No agent runner available. Skipping agent tests.")
            return {'status': 'Skipped', 'details': 'No Gemini API key provided'}
        
        # Track results
        results = {
            'document_processing': {'status': 'Not Run', 'details': ''},
            'financial_analysis': {'status': 'Not Run', 'details': ''},
            'financial_advice': {'status': 'Not Run', 'details': ''},
            'report_generation': {'status': 'Not Run', 'details': ''},
            'chat_query': {'status': 'Not Run', 'details': ''}
        }
        
        # Sample data for testing
        sample_transactions = [
            {"date": "01/05/2023", "description": "Salary Deposit", "amount": 8500.0, "category": "הכנסה"},
            {"date": "01/10/2023", "description": "Rent Payment", "amount": -3200.0, "category": "דיור"},
            {"date": "01/15/2023", "description": "Grocery Store", "amount": -450.75, "category": "מזון"},
            {"date": "01/20/2023", "description": "Electricity Bill", "amount": -210.25, "category": "חשבונות"},
            {"date": "01/25/2023", "description": "Internet Bill", "amount": -89.99, "category": "חשבונות"},
            {"date": "01/28/2023", "description": "Restaurant", "amount": -125.40, "category": "מזון"}
        ]
        
        # Test document processing agent
        try:
            logger.info("Testing document processing agent...")
            
            # Sample document text
            document_text = """
            Bank Statement
            Account: 1234-5678
            
            Transactions:
            01/05/2023 Salary Deposit +8,500.00
            01/10/2023 Rent Payment -3,200.00
            01/15/2023 Grocery Store -450.75
            01/20/2023 Electricity Bill -210.25
            01/25/2023 Internet Bill -89.99
            01/28/2023 Restaurant -125.40
            """
            
            start_time = time.time()
            transactions = self.agent_runner.process_document(document_text)
            elapsed = time.time() - start_time
            
            if transactions and len(transactions) > 0:
                results['document_processing'] = {
                    'status': 'Success',
                    'details': f"Extracted {len(transactions)} transactions in {elapsed:.2f} seconds"
                }
            else:
                results['document_processing'] = {
                    'status': 'Failure',
                    'details': "Failed to extract transactions"
                }
            
            logger.info(f"Document processing agent result: {results['document_processing']['status']}")
            
        except Exception as e:
            results['document_processing'] = {'status': 'Error', 'details': str(e)}
            logger.error(f"Error in document processing agent: {str(e)}", exc_info=True)
        
        # Test financial analysis agent
        try:
            logger.info("Testing financial analysis agent...")
            
            start_time = time.time()
            analysis = self.agent_runner.analyze_finances(sample_transactions)
            elapsed = time.time() - start_time
            
            if analysis and isinstance(analysis, dict) and 'summary' in analysis:
                results['financial_analysis'] = {
                    'status': 'Success',
                    'details': f"Generated analysis in {elapsed:.2f} seconds with keys: {', '.join(analysis.keys())}"
                }
            else:
                results['financial_analysis'] = {
                    'status': 'Failure',
                    'details': f"Failed to generate proper analysis: {analysis}"
                }
            
            logger.info(f"Financial analysis agent result: {results['financial_analysis']['status']}")
            
        except Exception as e:
            results['financial_analysis'] = {'status': 'Error', 'details': str(e)}
            logger.error(f"Error in financial analysis agent: {str(e)}", exc_info=True)
        
        # If analysis was successful, test advice agent
        if results['financial_analysis']['status'] == 'Success' and 'analysis' in locals():
            try:
                logger.info("Testing financial advice agent...")
                
                start_time = time.time()
                advice = self.agent_runner.get_financial_advice(analysis)
                elapsed = time.time() - start_time
                
                if advice and isinstance(advice, dict) and ('advice' in advice or 'recommendations' in advice):
                    results['financial_advice'] = {
                        'status': 'Success',
                        'details': f"Generated advice in {elapsed:.2f} seconds with keys: {', '.join(advice.keys())}"
                    }
                else:
                    results['financial_advice'] = {
                        'status': 'Failure',
                        'details': f"Failed to generate proper advice: {advice}"
                    }
                
                logger.info(f"Financial advice agent result: {results['financial_advice']['status']}")
                
            except Exception as e:
                results['financial_advice'] = {'status': 'Error', 'details': str(e)}
                logger.error(f"Error in financial advice agent: {str(e)}", exc_info=True)
        
            # If advice was successful, test report generation
            if results['financial_advice']['status'] == 'Success' and 'advice' in locals():
                try:
                    logger.info("Testing report generation agent...")
                    
                    start_time = time.time()
                    report = self.agent_runner.generate_report(sample_transactions, analysis, advice)
                    elapsed = time.time() - start_time
                    
                    if report and isinstance(report, str) and len(report) > 100:
                        results['report_generation'] = {
                            'status': 'Success',
                            'details': f"Generated report in {elapsed:.2f} seconds with {len(report)} characters"
                        }
                    else:
                        results['report_generation'] = {
                            'status': 'Failure',
                            'details': f"Failed to generate proper report (length: {len(report) if report else 0})"
                        }
                    
                    logger.info(f"Report generation agent result: {results['report_generation']['status']}")
                    
                except Exception as e:
                    results['report_generation'] = {'status': 'Error', 'details': str(e)}
                    logger.error(f"Error in report generation agent: {str(e)}", exc_info=True)
        
        # Test chat query handling
        try:
            logger.info("Testing chat query handling...")
            
            query = "What were my largest expenses last month?"
            
            start_time = time.time()
            response = self.agent_runner.process_chat_query(query, sample_transactions)
            elapsed = time.time() - start_time
            
            if response and isinstance(response, str) and len(response) > 20:
                results['chat_query'] = {
                    'status': 'Success',
                    'details': f"Generated response in {elapsed:.2f} seconds with {len(response)} characters"
                }
            else:
                results['chat_query'] = {
                    'status': 'Failure',
                    'details': f"Failed to generate proper response: {response}"
                }
            
            logger.info(f"Chat query handling result: {results['chat_query']['status']}")
            
        except Exception as e:
            results['chat_query'] = {'status': 'Error', 'details': str(e)}
            logger.error(f"Error in chat query handling: {str(e)}", exc_info=True)
        
        return results
    
    def run_end_to_end_tests(self):
        """Run end-to-end workflow tests."""
        logger.info("=== Starting End-to-End Tests ===")
        
        # Skip if no agent runner is available
        if not self.agent_runner:
            logger.warning("No agent runner available. Skipping end-to-end tests.")
            return {'status': 'Skipped', 'details': 'No Gemini API key provided'}
        
        results = {
            'bank_statement_workflow': {'status': 'Not Run', 'details': ''},
            'securities_workflow': {'status': 'Not Run', 'details': ''}
        }
        
        # Bank statement end-to-end workflow
        try:
            logger.info("Testing bank statement end-to-end workflow...")
            start_time = time.time()
            
            # 1. Process the PDF
            logger.info("Step 1: Process bank statement PDF")
            transactions, result_type = self.pdf_processor.process_financial_document(
                self.sample_files['bank_statement'],
                document_type='statement'
            )
            
            if result_type != 'transactions' or not transactions:
                raise Exception(f"Failed to extract transactions, result_type={result_type}")
            
            logger.info(f"Extracted {len(transactions)} transactions")
            
            # 2. Analyze the transactions
            logger.info("Step 2: Analyze transactions")
            analysis = self.agent_runner.analyze_finances(transactions)
            
            if not analysis or not isinstance(analysis, dict) or 'summary' not in analysis:
                raise Exception("Failed to generate analysis")
            
            logger.info(f"Generated analysis with keys: {', '.join(analysis.keys())}")
            
            # 3. Get financial advice
            logger.info("Step 3: Get financial advice")
            advice = self.agent_runner.get_financial_advice(analysis)
            
            if not advice or not isinstance(advice, dict):
                raise Exception("Failed to generate advice")
            
            logger.info(f"Generated advice with keys: {', '.join(advice.keys())}")
            
            # 4. Generate a report
            logger.info("Step 4: Generate report")
            report = self.agent_runner.generate_report(transactions, analysis, advice)
            
            if not report or not isinstance(report, str) or len(report) < 100:
                raise Exception(f"Failed to generate proper report (length: {len(report) if report else 0})")
            
            logger.info(f"Generated report with {len(report)} characters")
            
            # 5. Test a chat query
            logger.info("Step 5: Test chat query")
            query = "What can I do to save more money?"
            response = self.agent_runner.process_chat_query(query, transactions)
            
            if not response or not isinstance(response, str) or len(response) < 20:
                raise Exception(f"Failed to generate proper chat response: {response}")
            
            logger.info(f"Generated chat response with {len(response)} characters")
            
            elapsed = time.time() - start_time
            results['bank_statement_workflow'] = {
                'status': 'Success',
                'details': f"Completed end-to-end workflow in {elapsed:.2f} seconds"
            }
            
        except Exception as e:
            results['bank_statement_workflow'] = {'status': 'Error', 'details': str(e)}
            logger.error(f"Error in bank statement workflow: {str(e)}", exc_info=True)
        
        # Securities end-to-end workflow
        try:
            logger.info("Testing securities end-to-end workflow...")
            start_time = time.time()
            
            # 1. Process the securities PDF
            logger.info("Step 1: Process securities PDF")
            securities, result_type = self.pdf_processor.process_financial_document(
                self.sample_files['securities'],
                document_type='securities'
            )
            
            if result_type != 'securities' or not securities:
                raise Exception(f"Failed to extract securities, result_type={result_type}")
            
            logger.info(f"Extracted {len(securities)} securities")
            
            # 2. Analyze the securities
            logger.info("Step 2: Analyze securities")
            analysis = self.agent_runner.analyze_securities(securities)
            
            if not analysis or not isinstance(analysis, dict):
                raise Exception("Failed to generate securities analysis")
            
            logger.info(f"Generated securities analysis with keys: {', '.join(analysis.keys())}")
            
            # 3. Generate a securities report
            logger.info("Step 3: Generate securities report")
            report = self.agent_runner.generate_securities_report(analysis)
            
            if not report or not isinstance(report, str) or len(report) < 100:
                raise Exception(f"Failed to generate proper securities report (length: {len(report) if report else 0})")
            
            logger.info(f"Generated securities report with {len(report)} characters")
            
            elapsed = time.time() - start_time
            results['securities_workflow'] = {
                'status': 'Success',
                'details': f"Completed end-to-end workflow in {elapsed:.2f} seconds"
            }
            
        except Exception as e:
            results['securities_workflow'] = {'status': 'Error', 'details': str(e)}
            logger.error(f"Error in securities workflow: {str(e)}", exc_info=True)
        
        return results
    
    def run_all_tests(self):
        """Run all tests and return results."""
        logger.info("====== Starting Full System Test ======")
        start_time = time.time()
        
        # Run all test categories
        pdf_results = self.run_pdf_processing_tests()
        agent_results = self.run_agent_tests()
        e2e_results = self.run_end_to_end_tests()
        
        # Combine results
        all_results = {
            "pdf_processing_tests": pdf_results,
            "agent_tests": agent_results,
            "end_to_end_tests": e2e_results
        }
        
        # Calculate summary statistics
        total_tests = sum(len(results) for results in [pdf_results, 
                                                     agent_results if isinstance(agent_results, dict) else {}, 
                                                     e2e_results if isinstance(e2e_results, dict) else {}])
        
        success_count = sum(1 for result_set in [pdf_results, 
                                                agent_results if isinstance(agent_results, dict) else {}, 
                                                e2e_results if isinstance(e2e_results, dict) else {}]
                           for result in result_set.values() if result.get('status') == 'Success')
        
        error_count = sum(1 for result_set in [pdf_results, 
                                              agent_results if isinstance(agent_results, dict) else {}, 
                                              e2e_results if isinstance(e2e_results, dict) else {}]
                         for result in result_set.values() if result.get('status') == 'Error')
        
        failure_count = sum(1 for result_set in [pdf_results, 
                                                agent_results if isinstance(agent_results, dict) else {}, 
                                                e2e_results if isinstance(e2e_results, dict) else {}]
                           for result in result_set.values() if result.get('status') == 'Failure')
        
        skipped_count = sum(1 for result_set in [pdf_results, 
                                                agent_results if isinstance(agent_results, dict) else {}, 
                                                e2e_results if isinstance(e2e_results, dict) else {}]
                           for result in result_set.values() if result.get('status') == 'Skipped')
        
        elapsed = time.time() - start_time
        
        # Overall summary
        summary = {
            "total_tests": total_tests,
            "success_count": success_count,
            "error_count": error_count,
            "failure_count": failure_count,
            "skipped_count": skipped_count,
            "success_rate": f"{(success_count / total_tests) * 100:.1f}%" if total_tests > 0 else "0%",
            "total_runtime": f"{elapsed:.2f} seconds"
        }
        
        logger.info("====== Full System Test Complete ======")
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Successes: {success_count}")
        logger.info(f"Errors: {error_count}")
        logger.info(f"Failures: {failure_count}")
        logger.info(f"Skipped: {skipped_count}")
        logger.info(f"Success rate: {summary['success_rate']}")
        logger.info(f"Total runtime: {summary['total_runtime']}")
        
        # Save results to file
        results_file = os.path.join(self.test_dir, "test_results.json")
        with open(results_file, 'w') as f:
            json.dump({
                "summary": summary,
                "results": all_results
            }, f, indent=2)
        
        logger.info(f"Results saved to {results_file}")
        
        return {
            "summary": summary,
            "results": all_results,
            "results_file": results_file
        }
    
    def cleanup(self):
        """Clean up test resources."""
        logger.info("Cleaning up test resources...")
        
        # Remove sample files
        for file_path in self.sample_files.values():
            try:
                os.unlink(file_path)
                logger.info(f"Removed sample file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to remove file {file_path}: {e}")
        
        # Remove test directory if empty
        try:
            os.rmdir(self.test_dir)
            logger.info(f"Removed test directory: {self.test_dir}")
        except Exception as e:
            logger.warning(f"Failed to remove test directory {self.test_dir}: {e}")


def main():
    """Run the full system test."""
    logger.info("Starting FinAnalyzer full system test")
    
    test = FullSystemTest()
    try:
        results = test.run_all_tests()
        
        # Print summary to console
        print("\n=== Test Results Summary ===")
        print(f"Total tests: {results['summary']['total_tests']}")
        print(f"Successes: {results['summary']['success_count']}")
        print(f"Errors: {results['summary']['error_count']}")
        print(f"Failures: {results['summary']['failure_count']}")
        print(f"Skipped: {results['summary']['skipped_count']}")
        print(f"Success rate: {results['summary']['success_rate']}")
        print(f"Total runtime: {results['summary']['total_runtime']}")
        print(f"Detailed results saved to: {results['results_file']}")
        
        return results
    finally:
        # Always clean up, even if tests fail
        test.cleanup()


if __name__ == "__main__":
    main()