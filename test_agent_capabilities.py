"""
Comprehensive testing suite for FinAnalyzer's Gemini AI integration and agent capabilities.
This script performs detailed tests of the document processing, financial analysis, 
advice generation, and report creation features.
"""

import os
import sys
import json
import time
import pandas as pd
import logging
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
log_filename = f"agent_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agent_tester")

# Create test output directory
TEST_OUTPUT_DIR = "test_outputs"
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

def print_header(message: str) -> None:
    """Print a formatted header for test sections"""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)

def print_result(test_name: str, success: bool, details: str = None) -> None:
    """Print a test result with formatting"""
    if success:
        result = "✅ PASS"
    else:
        result = "❌ FAIL"
    
    print(f"{result} - {test_name}")
    if details:
        print(f"      {details}")

class AgentCapabilityTester:
    """Test class for evaluating agent capabilities"""
    
    def __init__(self):
        """Initialize the tester with API key and required components"""
        print_header("INITIALIZING TEST ENVIRONMENT")
        
        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            logger.error("No Gemini API key found in .env file")
            print("ERROR: Missing Gemini API key. Please add GEMINI_API_KEY to the .env file.")
            sys.exit(1)
            
        print_result("API Key Loading", True, f"Found API key: {self.api_key[:4]}...{self.api_key[-4:]}")
        
        # Import required modules
        try:
            import google.generativeai as genai
            self.genai = genai
            genai.configure(api_key=self.api_key)
            print_result("Gemini API Configuration", True)
        except ImportError as e:
            logger.error(f"Failed to import google-generativeai: {str(e)}")
            print_result("Gemini API Import", False, f"Error: {str(e)}")
            sys.exit(1)
            
        # Initialize test documents
        self.initialize_test_documents()
        
        # Initialize agent components
        self.initialize_agent_components()
    
    def initialize_test_documents(self):
        """Set up test documents for processing"""
        self.test_documents = {
            "bank_statement": """
MONTHLY STATEMENT
Account: 1234-5678
Date: 06/01/2023 - 06/30/2023

TRANSACTIONS:
06/02/2023 Salary Deposit +8,500.00
06/05/2023 Rent Payment -3,200.00
06/10/2023 Grocery Store -450.75
06/15/2023 Internet Bill -89.99
06/17/2023 Restaurant -125.40
06/20/2023 Transfer from Savings +1,000.00
06/22/2023 Gas Station -65.30
06/25/2023 Online Shopping -299.99
06/28/2023 Electricity Bill -210.25

SUMMARY:
Starting Balance: 2,450.00
Total Credits: +9,500.00
Total Debits: -4,441.68
Ending Balance: 7,508.32
            """,
            
            "credit_card": """
CREDIT CARD STATEMENT
Card: XXXX-XXXX-XXXX-1234
Billing Period: 05/15/2023 - 06/15/2023

TRANSACTIONS:
05/17/2023 Supermarket -210.50
05/20/2023 Gas Station -85.75
05/22/2023 Online Subscription -14.99
05/25/2023 Department Store -350.00
05/30/2023 Airline Tickets -1,200.00
06/02/2023 Restaurant -95.60
06/05/2023 Pharmacy -62.30
06/10/2023 Electronics -899.99
06/12/2023 Payment Thank You +2,000.00

SUMMARY:
Previous Balance: 1,450.00
Payments: -2,000.00
Purchases: +2,919.13
Fees and Interest: +35.25
Current Balance: 2,404.38
Minimum Payment Due: 75.00
Due Date: 07/10/2023
            """,
            
            "mixed_expenses": """
Household Budget Tracker - June 2023

Weekly Expenses:
06/03/2023 - Grocery Shopping -325.45
06/03/2023 - Children's Clothing -189.99
06/05/2023 - Restaurant Dinner -152.30
06/07/2023 - Gasoline -78.50
06/10/2023 - Home Repairs -412.75
06/10/2023 - Grocery Shopping -255.60
06/12/2023 - Doctor Visit -150.00
06/14/2023 - School Supplies -95.25
06/17/2023 - Grocery Shopping -301.20
06/18/2023 - Movie Night -65.00
06/19/2023 - Car Maintenance -220.00
06/24/2023 - Grocery Shopping -278.90
06/25/2023 - Birthday Party -175.00
06/27/2023 - Utility Bills -345.65
06/30/2023 - Monthly Gym Fee -80.00

Income:
06/01/2023 - Salary Deposit +5,400.00
06/15/2023 - Freelance Work +850.00
06/30/2023 - Dividends +125.50

Monthly Fixed Expenses:
06/01/2023 - Mortgage Payment -1,950.00
06/01/2023 - Car Loan -425.00
06/05/2023 - Insurance -320.00
06/10/2023 - Internet and Phone -180.00
            """
        }
        
        logger.info(f"Initialized {len(self.test_documents)} test documents")
    
    def initialize_agent_components(self):
        """Initialize the agent components for testing"""
        try:
            # Import from your utility modules
            from utils.model_adapter import GeminiAdapter
            from utils.agent_runner import FinancialAgentRunner
            from utils.financial_agents import extract_transactions_from_text
            
            self.model_adapter = GeminiAdapter(api_key=self.api_key, model_name="gemini-1.5-pro")
            self.agent_runner = FinancialAgentRunner(self.api_key)
            self.extract_func = extract_transactions_from_text
            
            print_result("Agent Components Initialization", True)
            
        except Exception as e:
            logger.error(f"Failed to initialize agent components: {str(e)}")
            print_result("Agent Components Initialization", False, f"Error: {str(e)}")
            sys.exit(1)
    
    def run_all_tests(self):
        """Run all test suites"""
        start_time = time.time()
        print_header("RUNNING COMPREHENSIVE AGENT CAPABILITY TESTS")
        
        # Run individual test suites
        passed = 0
        failed = 0
        
        test_suites = [
            self.test_document_processing,
            self.test_financial_analysis,
            self.test_financial_advice,
            self.test_report_generation,
            self.test_complex_scenarios
        ]
        
        for test_suite in test_suites:
            suite_results = test_suite()
            passed += suite_results.get('passed', 0)
            failed += suite_results.get('failed', 0)
        
        # Print summary
        elapsed_time = time.time() - start_time
        print_header(f"TEST SUMMARY ({elapsed_time:.2f} seconds)")
        print(f"Total tests: {passed + failed}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success rate: {(passed / (passed + failed)) * 100:.1f}%")
        
        return {
            'passed': passed,
            'failed': failed,
            'elapsed_time': elapsed_time
        }
    
    def test_document_processing(self):
        """Test document processing capabilities"""
        print_header("TESTING DOCUMENT PROCESSING")
        passed = 0
        failed = 0
        
        # Test extraction on different document types
        for doc_name, doc_content in self.test_documents.items():
            logger.info(f"Testing document extraction on {doc_name}")
            print(f"\nTesting transaction extraction from {doc_name}...")
            
            try:
                # Direct extraction test
                extraction_start = time.time()
                transactions = self.extract_func(doc_content)
                extraction_time = time.time() - extraction_start
                
                # Validate the extraction results
                if transactions and len(transactions) > 0:
                    # Save results to file
                    with open(f"{TEST_OUTPUT_DIR}/extracted_{doc_name}.json", "w", encoding="utf-8") as f:
                        json.dump(transactions, f, indent=4, ensure_ascii=False)
                    
                    print_result(
                        f"Extract transactions from {doc_name}", 
                        True, 
                        f"Found {len(transactions)} transactions in {extraction_time:.2f}s"
                    )
                    
                    # Validate transaction structure
                    for idx, tx in enumerate(transactions[:3]):  # Check first 3 transactions
                        if all(k in tx for k in ('date', 'description', 'amount', 'category')):
                            print_result(
                                f"Transaction {idx+1} structure validation", 
                                True,
                                f"{tx['date']} - {tx['description']}: {tx['amount']}"
                            )
                            passed += 1
                        else:
                            print_result(
                                f"Transaction {idx+1} structure validation", 
                                False,
                                f"Missing required fields. Found: {list(tx.keys())}"
                            )
                            failed += 1
                else:
                    print_result(
                        f"Extract transactions from {doc_name}", 
                        False, 
                        "No transactions found"
                    )
                    failed += 1
                
                # Agent-based extraction test
                try:
                    agent_start = time.time()
                    agent_transactions = self.agent_runner.process_document(doc_content)
                    agent_time = time.time() - agent_start
                    
                    # Compare results
                    direct_count = len(transactions)
                    agent_count = len(agent_transactions) if agent_transactions else 0
                    
                    with open(f"{TEST_OUTPUT_DIR}/agent_extracted_{doc_name}.json", "w", encoding="utf-8") as f:
                        json.dump(agent_transactions, f, indent=4, ensure_ascii=False)
                    
                    print_result(
                        f"Agent-based extraction from {doc_name}", 
                        agent_count > 0,
                        f"Agent found {agent_count} transactions in {agent_time:.2f}s (vs. {direct_count} direct)"
                    )
                    
                    if agent_count > 0:
                        passed += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"Error in agent extraction: {str(e)}")
                    print_result(
                        f"Agent-based extraction from {doc_name}", 
                        False,
                        f"Error: {str(e)}"
                    )
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Error processing {doc_name}: {str(e)}")
                print_result(
                    f"Extract transactions from {doc_name}", 
                    False,
                    f"Error: {str(e)}"
                )
                failed += 1
        
        return {'passed': passed, 'failed': failed}
    
    def test_financial_analysis(self):
        """Test financial analysis capabilities"""
        print_header("TESTING FINANCIAL ANALYSIS")
        passed = 0
        failed = 0
        
        # Generate a complex transaction dataset
        transactions = self._generate_test_transactions(60)  # 60 days of transactions
        
        with open(f"{TEST_OUTPUT_DIR}/test_transactions.json", "w", encoding="utf-8") as f:
            json.dump(transactions, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Created test dataset with {len(transactions)} transactions")
        print(f"Created test dataset with {len(transactions)} transactions")
        
        try:
            # Test financial analysis
            analysis_start = time.time()
            analysis = self.agent_runner.analyze_finances(transactions)
            analysis_time = time.time() - analysis_start
            
            with open(f"{TEST_OUTPUT_DIR}/financial_analysis.json", "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=4, ensure_ascii=False)
                
            # Verify analysis structure
            required_sections = ["summary", "category_analysis"]
            
            if all(section in analysis for section in required_sections):
                print_result(
                    "Financial analysis structure", 
                    True,
                    f"Analysis completed in {analysis_time:.2f}s, contains all required sections"
                )
                passed += 1
                
                # Verify summary data
                summary = analysis.get("summary", {})
                if all(k in summary for k in ("total_income", "total_expenses", "net_balance")):
                    print_result(
                        "Financial summary data", 
                        True,
                        f"Income: {summary['total_income']}, Expenses: {summary['total_expenses']}, Balance: {summary['net_balance']}"
                    )
                    passed += 1
                else:
                    print_result(
                        "Financial summary data", 
                        False,
                        f"Missing required summary fields. Found: {list(summary.keys())}"
                    )
                    failed += 1
                    
                # Verify category analysis
                categories = analysis.get("category_analysis", {})
                if len(categories) > 0:
                    print_result(
                        "Category analysis", 
                        True,
                        f"Found {len(categories)} categories"
                    )
                    passed += 1
                else:
                    print_result(
                        "Category analysis", 
                        False,
                        "No categories found in analysis"
                    )
                    failed += 1
            else:
                print_result(
                    "Financial analysis structure", 
                    False,
                    f"Missing required sections. Found: {list(analysis.keys())}"
                )
                failed += 1
                
        except Exception as e:
            logger.error(f"Error in financial analysis: {str(e)}")
            print_result(
                "Financial analysis", 
                False,
                f"Error: {str(e)}"
            )
            failed += 1
            
        return {'passed': passed, 'failed': failed}
    
    def test_financial_advice(self):
        """Test financial advice generation capabilities"""
        print_header("TESTING FINANCIAL ADVICE GENERATION")
        passed = 0
        failed = 0
        
        try:
            # Load analysis from previous test if available
            analysis_path = f"{TEST_OUTPUT_DIR}/financial_analysis.json"
            if os.path.exists(analysis_path):
                with open(analysis_path, "r", encoding="utf-8") as f:
                    analysis = json.load(f)
            else:
                # Generate a basic analysis
                transactions = self._generate_test_transactions(30)
                analysis = self.agent_runner.analyze_finances(transactions)
            
            # Get financial advice
            advice_start = time.time()
            advice = self.agent_runner.get_financial_advice(analysis)
            advice_time = time.time() - advice_start
            
            with open(f"{TEST_OUTPUT_DIR}/financial_advice.json", "w", encoding="utf-8") as f:
                json.dump(advice, f, indent=4, ensure_ascii=False)
                
            # Verify advice structure
            if "advice" in advice and "recommendations" in advice:
                print_result(
                    "Financial advice structure", 
                    True,
                    f"Advice generated in {advice_time:.2f}s with correct structure"
                )
                passed += 1
                
                # Verify advice content
                if len(advice["advice"]) > 0 or len(advice["recommendations"]) > 0:
                    print_result(
                        "Financial advice content", 
                        True,
                        f"Found {len(advice['advice'])} advice items and {len(advice['recommendations'])} recommendations"
                    )
                    
                    # Print sample advice
                    if len(advice["advice"]) > 0:
                        print(f"  Sample advice: {advice['advice'][0]}")
                    if len(advice["recommendations"]) > 0:
                        print(f"  Sample recommendation: {advice['recommendations'][0]}")
                        
                    passed += 1
                else:
                    print_result(
                        "Financial advice content", 
                        False,
                        "No advice or recommendations found"
                    )
                    failed += 1
            else:
                print_result(
                    "Financial advice structure", 
                    False,
                    f"Missing required sections. Found: {list(advice.keys())}"
                )
                failed += 1
                
        except Exception as e:
            logger.error(f"Error in financial advice generation: {str(e)}")
            print_result(
                "Financial advice generation", 
                False,
                f"Error: {str(e)}"
            )
            failed += 1
            
        return {'passed': passed, 'failed': failed}
    
    def test_report_generation(self):
        """Test financial report generation capabilities"""
        print_header("TESTING FINANCIAL REPORT GENERATION")
        passed = 0
        failed = 0
        
        try:
            # Load data from previous tests if available
            transactions_path = f"{TEST_OUTPUT_DIR}/test_transactions.json"
            analysis_path = f"{TEST_OUTPUT_DIR}/financial_analysis.json"
            advice_path = f"{TEST_OUTPUT_DIR}/financial_advice.json"
            
            if all(os.path.exists(path) for path in [transactions_path, analysis_path, advice_path]):
                with open(transactions_path, "r", encoding="utf-8") as f:
                    transactions = json.load(f)
                with open(analysis_path, "r", encoding="utf-8") as f:
                    analysis = json.load(f)
                with open(advice_path, "r", encoding="utf-8") as f:
                    advice = json.load(f)
            else:
                # Generate new data
                transactions = self._generate_test_transactions(30)
                analysis = self.agent_runner.analyze_finances(transactions)
                advice = self.agent_runner.get_financial_advice(analysis)
            
            # Generate report
            report_start = time.time()
            report = self.agent_runner.generate_report(transactions, analysis, advice)
            report_time = time.time() - report_start
            
            with open(f"{TEST_OUTPUT_DIR}/financial_report.md", "w", encoding="utf-8") as f:
                f.write(report)
                
            # Verify report
            if report and len(report) > 100:  # Basic length check
                print_result(
                    "Financial report generation", 
                    True,
                    f"Report generated in {report_time:.2f}s with {len(report)} characters"
                )
                
                # Check for key sections in the report
                key_sections = ["סיכום", "קטגוריה", "המלצות"]
                found_sections = sum(1 for section in key_sections if section in report)
                
                print_result(
                    "Financial report content", 
                    found_sections == len(key_sections),
                    f"Found {found_sections}/{len(key_sections)} expected sections"
                )
                
                if found_sections == len(key_sections):
                    passed += 2
                else:
                    passed += 1
                    failed += 1
            else:
                print_result(
                    "Financial report generation", 
                    False,
                    "Generated report is too short or empty"
                )
                failed += 2
                
        except Exception as e:
            logger.error(f"Error in report generation: {str(e)}")
            print_result(
                "Financial report generation", 
                False,
                f"Error: {str(e)}"
            )
            failed += 2
            
        return {'passed': passed, 'failed': failed}
    
    def test_complex_scenarios(self):
        """Test more complex agent scenarios"""
        print_header("TESTING COMPLEX AGENT SCENARIOS")
        passed = 0
        failed = 0
        
        # Test 1: Complex query processing
        complex_queries = [
            "What were my highest expenses last month?",
            "How much did I spend on food compared to housing?",
            "What's my average daily spending?",
            "Where can I save more money based on my spending patterns?"
        ]
        
        # Ensure we have transactions data
        transactions_path = f"{TEST_OUTPUT_DIR}/test_transactions.json"
        if os.path.exists(transactions_path):
            with open(transactions_path, "r", encoding="utf-8") as f:
                transactions = json.load(f)
        else:
            transactions = self._generate_test_transactions(30)
            
        # Process each query
        for idx, query in enumerate(complex_queries):
            try:
                print(f"\nProcessing complex query {idx+1}: '{query}'")
                
                query_start = time.time()
                response = self.agent_runner.process_chat_query(query, transactions)
                query_time = time.time() - query_start
                
                # Save response
                with open(f"{TEST_OUTPUT_DIR}/query_response_{idx+1}.txt", "w", encoding="utf-8") as f:
                    f.write(f"Query: {query}\n\nResponse:\n{response}")
                
                if response and len(response) > 20:  # Basic check for reasonable response
                    print_result(
                        f"Complex query {idx+1}", 
                        True,
                        f"Response generated in {query_time:.2f}s ({len(response)} chars)"
                    )
                    print(f"  First 100 chars: {response[:100]}...")
                    passed += 1
                else:
                    print_result(
                        f"Complex query {idx+1}", 
                        False,
                        f"Response too short or empty: {response}"
                    )
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Error processing query '{query}': {str(e)}")
                print_result(
                    f"Complex query {idx+1}", 
                    False,
                    f"Error: {str(e)}"
                )
                failed += 1
        
        return {'passed': passed, 'failed': failed}
    
    def _generate_test_transactions(self, days: int) -> List[Dict[str, Any]]:
        """Generate a rich dataset of test transactions"""
        import random
        from datetime import datetime, timedelta
        
        categories = {
            "income": ["Salary", "Freelance Work", "Investment Income", "Gift"],
            "housing": ["Rent", "Mortgage", "Property Tax", "Home Insurance", "Utilities", "Home Repairs"],
            "food": ["Grocery", "Restaurant", "Takeout", "Coffee Shop"],
            "transportation": ["Gas", "Public Transit", "Car Payment", "Car Insurance", "Car Maintenance"],
            "entertainment": ["Movies", "Concerts", "Subscriptions", "Books", "Games"],
            "health": ["Doctor Visit", "Pharmacy", "Health Insurance", "Gym"],
            "shopping": ["Clothing", "Electronics", "Furniture", "Online Shopping"],
            "other": ["Travel", "Education", "Charity", "Gifts", "Miscellaneous"]
        }
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        transactions = []
        
        # Generate a salary deposit on 1st and 15th
        current_date = start_date
        while current_date <= end_date:
            if current_date.day == 1 or current_date.day == 15:
                salary = random.randint(4500, 5500)
                transactions.append({
                    "date": current_date.strftime("%m/%d/%Y"),
                    "description": "Salary Deposit",
                    "amount": salary,
                    "category": "הכנסה"
                })
            current_date += timedelta(days=1)
            
        # Generate random expenses and occasional income
        current_date = start_date
        while current_date <= end_date:
            # 3-7 transactions per day
            for _ in range(random.randint(0, 3)):
                # Determine if this is income (10% chance)
                is_income = random.random() < 0.1
                
                if is_income:
                    category = "income"
                    category_hebrew = "הכנסה"
                    amount = random.randint(50, 1000)
                    description = random.choice(categories[category])
                else:
                    category = random.choice(list(set(categories.keys()) - {"income"}))
                    
                    # Map English categories to Hebrew
                    category_mapping = {
                        "housing": "דיור",
                        "food": "מזון",
                        "transportation": "תחבורה",
                        "entertainment": "בידור",
                        "health": "בריאות",
                        "shopping": "קניות",
                        "other": "אחר"
                    }
                    category_hebrew = category_mapping.get(category, "אחר")
                    
                    # Amount depends on category
                    if category == "housing":
                        amount = -random.randint(500, 2000)
                    elif category == "food":
                        amount = -random.randint(20, 300)
                    elif category == "transportation":
                        amount = -random.randint(30, 200)
                    else:
                        amount = -random.randint(10, 500)
                    
                    description = random.choice(categories[category])
                
                transactions.append({
                    "date": current_date.strftime("%m/%d/%Y"),
                    "description": description,
                    "amount": amount,
                    "category": category_hebrew
                })
            
            current_date += timedelta(days=1)
            
        return transactions

if __name__ == "__main__":
    tester = AgentCapabilityTester()
    results = tester.run_all_tests()
    
    # Exit with status code
    if results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
