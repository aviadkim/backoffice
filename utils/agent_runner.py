from agents import Runner
from utils.financial_agents import (
    create_main_agent,
    create_document_processing_agent,
    create_financial_analysis_agent,
    create_financial_advisor_agent,
    create_report_generation_agent
)
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class FinancialAgentRunner:
    """Runs financial agents to process documents and provide insights."""
    
    def __init__(self, api_key=None):
        """Initialize the agent runner."""
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("API key is required")
    
    def process_document(self, document_text):
        """Process a document to extract transactions."""
        agent = create_document_processing_agent(self.api_key)
        
        result = Runner.run_sync(
            starting_agent=agent,
            input=f"Please extract all financial transactions from this document:\n\n{document_text}"
        )
        
        # Extract transactions from result
        transactions = []
        if hasattr(result, 'agent_outputs') and result.agent_outputs:
            for output in result.agent_outputs:
                if output.get('tool_result') and isinstance(output.get('tool_result'), list):
                    transactions = output.get('tool_result')
                    break
        
        return transactions
    
    def analyze_finances(self, transactions):
        """Analyze financial transactions and provide insights."""
        agent = create_financial_analysis_agent(self.api_key)
        
        result = Runner.run_sync(
            starting_agent=agent,
            input=f"Please analyze these financial transactions:\n\n{transactions}"
        )
        
        # Extract analysis from result
        analysis = {}
        if hasattr(result, 'agent_outputs') and result.agent_outputs:
            for output in result.agent_outputs:
                if output.get('tool_result') and isinstance(output.get('tool_result'), dict):
                    analysis = output.get('tool_result')
                    break
        
        return analysis
    
    def get_financial_advice(self, analysis):
        """Generate financial advice based on analysis."""
        agent = create_financial_advisor_agent(self.api_key)
        
        result = Runner.run_sync(
            starting_agent=agent,
            input=f"Please provide financial advice based on this analysis:\n\n{analysis}"
        )
        
        # Extract advice from result
        advice = {}
        if hasattr(result, 'agent_outputs') and result.agent_outputs:
            for output in result.agent_outputs:
                if output.get('tool_result') and isinstance(output.get('tool_result'), dict):
                    advice = output.get('tool_result')
                    break
        
        return advice
    
    def generate_report(self, transactions, analysis, advice):
        """Generate a comprehensive financial report."""
        agent = create_report_generation_agent(self.api_key)
        
        result = Runner.run_sync(
            starting_agent=agent,
            input="Please generate a comprehensive financial report using the provided data."
        )
        
        # Extract report from result
        report = ""
        if hasattr(result, 'agent_outputs') and result.agent_outputs:
            for output in result.agent_outputs:
                if output.get('tool_result') and isinstance(output.get('tool_result'), str):
                    report = output.get('tool_result')
                    break
        
        return report
    
    def process_chat_query(self, query, transactions=None):
        """Process a user query using the main agent."""
        agent = create_main_agent(self.api_key)
        
        context = ""
        if transactions:
            context = f"Context: The user has {len(transactions)} transactions in the system. "
        
        result = Runner.run_sync(
            starting_agent=agent,
            input=f"{context}User query: {query}"
        )
        
        # Return the last response
        if hasattr(result, 'final_output'):
            return result.final_output
        return "Sorry, I couldn't process your request."
