import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Create a simple model instance
model = genai.GenerativeModel("gemini-1.5-pro")

# Create a simple function declaration
tools = [{
    "function_declarations": [{
        "name": "extract_transactions_from_text",
        "description": "Extract financial transactions from document text.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"}
            },
            "required": ["text"]
        }
    }]
}]

# Simple test prompt
prompt = """
Instructions: Extract all transactions from the following document.

User: 
MONTHLY STATEMENT
Account: 1234-5678
Date: 06/01/2023 - 06/30/2023

TRANSACTIONS:
06/02/2023 Salary Deposit +8,500.00
06/05/2023 Rent Payment -3,200.00
06/10/2023 Grocery Store -450.75
"""

print("Sending request to Gemini...")
try:
    response = model.generate_content(
        prompt,
        tools=tools
    )
    print("Response received:")
    print(f"Response type: {type(response)}")

    # Try to access standard properties
    if hasattr(response, "text"):
        print(f"Response text: {response.text}")
    else:
        print("No text attribute found")

    # Try to find function calls
    if hasattr(response, "candidates"):
        print("Found candidates attribute")
        for i, candidate in enumerate(response.candidates):
            print(f"Examining candidate {i}:")
            if hasattr(candidate, "content"):
                print("  Has content attribute")
                if hasattr(candidate.content, "parts"):
                    print("  Has parts attribute")
                    for j, part in enumerate(candidate.content.parts):
                        print(f"  Examining part {j}")
                        if hasattr(part, "function_call"):
                            print("    Found function call!")
                            print(f"    Function name: {part.function_call.name}")
                            print(f"    Function args: {part.function_call.args}")
                        else:
                            print("    No function call in this part")
            else:
                print("  No content attribute")
    else:
        print("No candidates attribute found")
except Exception as e:
    print(f"Error: {str(e)}")
    print(f"Error type: {type(e)}")
    # Try to get more details about the error
    if hasattr(e, "dict"):
        print(f"Error attributes: {e.dict}")
