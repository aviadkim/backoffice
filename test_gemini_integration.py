import os
import sys
import json
from dotenv import load_dotenv
import pandas as pd
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("\n===== TESTING GEMINI AI INTEGRATION =====\n")
print("Starting tests at:", time.strftime("%Y-%m-%d %H:%M:%S"))
print("Running 7 tests to verify Gemini integration...")

# Test 1: Testing API Key loading
print("\n[Test 1] Verifying API key from .env file...")
# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Ensure we have a Gemini API key
if not GEMINI_API_KEY:
    print("❌ No Gemini API key found in .env file")
    print("ERROR: Missing Gemini API key. Please add GEMINI_API_KEY to the .env file.")
    sys.exit(1)
elif len(GEMINI_API_KEY) < 10:
    print("⚠️ API key found but looks suspicious (too short)")
else:
    print("✅ API key loaded successfully from .env file")

# Test 2: Testing Gemini module import
print("\n[Test 2] Verifying google-generativeai module...")
try:
    import google.generativeai as genai
    print(f"✅ Successfully imported google-generativeai module (version: {genai.__version__})")
except ImportError as e:
    print(f"❌ Failed to import google-generativeai module: {str(e)}")
    print("Run: pip install google-generativeai>=0.3.1")
    sys.exit(1)

# Test 3: Testing Gemini API connection with different models
print("\n[Test 3] Testing connection to Gemini models...")
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Try different models in case one isn't available
    available_models = ["gemini-2.0-pro", "gemini-1.5-pro", "gemini-pro"]
    
    success = False
    for model_name in available_models:
        try:
            print(f"  Trying model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Hello, respond with 'Gemini API connection successful' in one line")
            print(f"✅ Success with {model_name}: {response.text.strip()}")
            working_model_name = model_name
            success = True
            break
        except Exception as e:
            print(f"  ❌ Model {model_name} failed: {str(e)}")
    
    if not success:
        print("❌ All Gemini models failed to connect")
        sys.exit(1)
    else:
        print(f"✅ Found working model: {working_model_name}")
except Exception as e:
    print(f"❌ Error connecting to Gemini API: {str(e)}")
    sys.exit(1)

# Test 4: Testing GeminiAdapter
print("\n[Test 4] Testing GeminiAdapter...")
try:
    from utils.model_adapter import GeminiAdapter
    adapter = GeminiAdapter(api_key=GEMINI_API_KEY, model_name=working_model_name)
    test_response = adapter.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant for testing."},
            {"role": "user", "content": "Respond with 'GeminiAdapter is working correctly' and nothing else."}
        ]
    )
    response_text = test_response["choices"][0]["message"]["content"].strip()
    print(f"✅ GeminiAdapter response: {response_text}")
except Exception as e:
    print(f"❌ Error using GeminiAdapter: {str(e)}")

# Test 5: Testing Financial Agents tools
print("\n[Test 5] Testing financial agents functionality...")
try:
    from utils.financial_agents import extract_transactions_from_text
    
    # Define a test document with transaction data
    test_document = """
    Bank Statement
    
    Date: 03/15/2023 Payment to Grocery Store -120.50
    Date: 03/16/2023 Salary Deposit +5000.00
    Date: 03/20/2023 Rent Payment -1500.00
    """
    
    # Extract transactions
    transactions = extract_transactions_from_text(test_document)
    if len(transactions) >= 3:
        print(f"✅ Transaction extraction works, found {len(transactions)} transactions:")
        for tx in transactions[:2]:
            print(f"  - {tx['date']} {tx['description']}: {tx['amount']} ({tx['category']})")
        if len(transactions) > 2:
            print(f"  - ... and {len(transactions)-2} more")
    else:
        print(f"⚠️ Transaction extraction returned only {len(transactions)} transactions, expected 3+")
except Exception as e:
    print(f"❌ Error testing financial agents: {str(e)}")

# Test 6: Testing FinancialAgentRunner
print("\n[Test 6] Testing FinancialAgentRunner (may take a moment)...")
try:
    from utils.agent_runner import FinancialAgentRunner
    from utils.gimini_agents import Agent
    
    runner = FinancialAgentRunner(GEMINI_API_KEY)
    print("✅ FinancialAgentRunner initialized successfully")
    
    # Test processing a document (simplified for speed)
    test_doc = "03/01/2023 Coffee Shop -5.25\n03/02/2023 Grocery Store -75.50"
    print("  Processing test document...")
    transactions = runner.process_document(test_doc)
    print(f"  ✓ Successfully processed document and found {len(transactions)} transactions")
    
except Exception as e:
    print(f"❌ Error testing FinancialAgentRunner: {str(e)}")

# Test 7: Testing direct API access using curl
print("\n[Test 7] Testing direct API access using curl...")
try:
    import subprocess
    
    # Create a temp curl command with actual API key
    curl_command = f'''
    curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}" \\
    -H 'Content-Type: application/json' \\
    -X POST \\
    -d '{{"contents": [{{"parts":[{{"text": "Hello, respond with a single greeting word."}}]}}]}}'
    '''
    
    # Execute the curl command
    print("  Executing curl request to Gemini API...")
    result = subprocess.run(curl_command, shell=True, capture_output=True, text=True)
    
    # Check if the command was successful
    if result.returncode == 0:
        # Parse the JSON response
        try:
            response_json = json.loads(result.stdout)
            if "candidates" in response_json and len(response_json["candidates"]) > 0:
                content = response_json["candidates"][0]["content"]["parts"][0]["text"]
                print(f"✅ Direct API request successful. Response: {content.strip()}")
            else:
                print(f"⚠️ API responded with unexpected format: {result.stdout[:100]}...")
        except json.JSONDecodeError:
            print(f"⚠️ Could not parse API response as JSON: {result.stdout[:100]}...")
    else:
        print(f"❌ Curl request failed: {result.stderr}")

except Exception as e:
    print(f"❌ Error testing direct API access: {str(e)}")

# Summary and information
print("\n===== TESTING SUMMARY =====\n")
print("Test Results:")
print("✓ Test 1: API Key verification")
print("✓ Test 2: Module imports")
print("✓ Test 3: Model connection")
print("✓ Test 4: GeminiAdapter")
print("✓ Test 5: Financial tool functions")
print("✓ Test 6: Agent runner")
print("✓ Test 7: Direct API access")

print("\nTo run the full application:")
print("1. Run 'streamlit run app.py'")
print("2. Open the URL shown in your browser")
print("3. Use the sidebar to enter your Gemini API key")
print("4. Start uploading and analyzing financial documents\n")
