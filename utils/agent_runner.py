from utils.gimini_agents import Runner, Agent, function_tool
from utils.financial_agents import (
    create_main_agent,
    create_document_processing_agent,
    create_financial_analysis_agent,
    create_financial_advisor_agent,
    create_report_generation_agent,
    create_securities_analysis_agent
)
import logging
import os
from dotenv import load_dotenv
import json
import time
import random

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class FinancialAgentRunner:
    """Runs financial agents to process documents and provide insights."""
    
    def __init__(self, api_key=None, max_retries=3, retry_delay=2):
        """
        Initialize the agent runner.
        
        Args:
            api_key: API key for Gemini
            max_retries: Maximum number of retries for API calls
            retry_delay: Base delay between retries (seconds)
        """
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("API key is required")
            
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._results_cache = {}  # Simple cache for results
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute a function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
        """
        # Create cache key if caching is enabled
        cache_enabled = kwargs.pop('cache_enabled', True)
        if cache_enabled:
            # Create a simple cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Check cache
            if cache_key in self._results_cache:
                logger.info(f"Using cached result for {func.__name__}")
                return self._results_cache[cache_key]
        
        # Execute with retries
        retries = 0
        last_exception = None
        
        while retries <= self.max_retries:
            try:
                result = func(*args, **kwargs)
                
                # Cache the result if successful
                if cache_enabled:
                    self._results_cache[cache_key] = result
                
                return result
            
            except Exception as e:
                last_exception = e
                retries += 1
                
                if retries <= self.max_retries:
                    # Calculate backoff delay with jitter
                    delay = self.retry_delay * (2 ** (retries - 1)) + random.uniform(0, 1)
                    logger.warning(f"API call failed, retrying in {delay:.2f} seconds. Error: {str(e)}")
                    time.sleep(delay)
                else:
                    logger.error(f"Failed after {self.max_retries} retries: {str(e)}", exc_info=True)
        
        # If we get here, all retries failed
        raise last_exception
    
    def process_document(self, document_text, cache_enabled=True):
        """
        Process a document to extract transactions.
        
        Args:
            document_text: Text content of the document
            cache_enabled: Whether to cache results
            
        Returns:
            List of transaction dictionaries
        """
        agent = create_document_processing_agent(self.api_key)
        
        # Run with retry logic
        def _run_document_processing():
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
        
        return self._retry_with_backoff(_run_document_processing, cache_enabled=cache_enabled)
    
    def analyze_finances(self, transactions, cache_enabled=True):
        """
        Analyze financial transactions and provide insights.
        
        Args:
            transactions: List of transaction dictionaries
            cache_enabled: Whether to cache results
            
        Returns:
            Analysis dictionary
        """
        agent = create_financial_analysis_agent(self.api_key)
        
        # Run with retry logic
        def _run_financial_analysis():
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
        
        return self._retry_with_backoff(_run_financial_analysis, cache_enabled=cache_enabled)
    
    def get_financial_advice(self, analysis, cache_enabled=True):
        """
        Generate financial advice based on analysis.
        
        Args:
            analysis: Financial analysis dictionary
            cache_enabled: Whether to cache results
            
        Returns:
            Advice dictionary
        """
        agent = create_financial_advisor_agent(self.api_key)
        
        # Run with retry logic
        def _run_advice_generation():
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
        
        return self._retry_with_backoff(_run_advice_generation, cache_enabled=cache_enabled)
    
    def generate_report(self, transactions, analysis, advice, cache_enabled=False):
        """
        Generate a comprehensive financial report.
        
        Args:
            transactions: List of transaction dictionaries
            analysis: Financial analysis dictionary
            advice: Financial advice dictionary
            cache_enabled: Whether to cache results
            
        Returns:
            Report string
        """
        agent = create_report_generation_agent(self.api_key)
        
        # Run with retry logic
        def _run_report_generation():
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
        
        return self._retry_with_backoff(_run_report_generation, cache_enabled=cache_enabled)
    
    def process_chat_query(self, query, transactions=None, cache_enabled=False):
        """
        Process a user query using the main agent.
        
        Args:
            query: User query string
            transactions: Optional transactions context
            cache_enabled: Whether to cache results
            
        Returns:
            Response string
        """
        agent = create_main_agent(self.api_key)
        
        # Context for the agent
        context = ""
        if transactions:
            context = f"Context: The user has {len(transactions)} transactions in the system. "
        
        # Run with retry logic
        def _run_chat_query():
            result = Runner.run_sync(
                starting_agent=agent,
                input=f"{context}User query: {query}"
            )
            
            # Return the last response
            if hasattr(result, 'final_output'):
                return result.final_output
            return "Sorry, I couldn't process your request."
        
        return self._retry_with_backoff(_run_chat_query, cache_enabled=cache_enabled)
    
    def analyze_securities(self, securities_transactions, report_date=None, cache_enabled=True):
        """
        Analyze securities by ISIN across different accounts.
        
        Args:
            securities_transactions: List of securities dictionaries
            report_date: Optional report date
            cache_enabled: Whether to cache results
            
        Returns:
            Securities analysis dictionary
        """
        agent = create_securities_analysis_agent(self.api_key)
        
        # Prepare the input for the agent
        input_data = {
            "transactions": securities_transactions,
            "report_date": report_date or "current"
        }
        
        # Run with retry logic
        def _run_securities_analysis():
            result = Runner.run_sync(
                starting_agent=agent,
                input=f"Please analyze these securities transactions by ISIN: {json.dumps(input_data)}"
            )
            
            # Extract analysis from result
            securities_analysis = {}
            if hasattr(result, 'agent_outputs') and result.agent_outputs:
                for output in result.agent_outputs:
                    if output.get('tool') == 'analyze_securities_by_isin' and isinstance(output.get('tool_result'), dict):
                        securities_analysis = output.get('tool_result')
                        break
            
            return securities_analysis
        
        return self._retry_with_backoff(_run_securities_analysis, cache_enabled=cache_enabled)
    
    def analyze_performance(self, historical_data, grouping="monthly", cache_enabled=True):
        """
        Analyze securities performance over time.
        
        Args:
            historical_data: Historical securities data
            grouping: Time grouping (monthly, quarterly, etc.)
            cache_enabled: Whether to cache results
            
        Returns:
            Performance analysis dictionary
        """
        agent = create_securities_analysis_agent(self.api_key)
        
        # Prepare the input for the agent
        input_data = {
            "historical_data": historical_data,
            "grouping": grouping
        }
        
        # Run with retry logic
        def _run_performance_analysis():
            result = Runner.run_sync(
                starting_agent=agent,
                input=f"Please analyze the performance over time of these securities: {json.dumps(input_data)}"
            )
            
            # Extract analysis from result
            performance_analysis = {}
            if hasattr(result, 'agent_outputs') and result.agent_outputs:
                for output in result.agent_outputs:
                    if output.get('tool') == 'analyze_performance_over_time' and isinstance(output.get('tool_result'), dict):
                        performance_analysis = output.get('tool_result')
                        break
            
            return performance_analysis
        
        return self._retry_with_backoff(_run_performance_analysis, cache_enabled=cache_enabled)
    
    def generate_securities_report(self, securities_analysis, performance_analysis=None, cache_enabled=False):
        """
        Generate a consolidated securities report.
        
        Args:
            securities_analysis: Securities analysis dictionary
            performance_analysis: Optional performance analysis
            cache_enabled: Whether to cache results
            
        Returns:
            Report string
        """
        agent = create_securities_analysis_agent(self.api_key)
        
        # Prepare the input for the agent
        input_data = {
            "securities_analysis": securities_analysis
        }
        if performance_analysis:
            input_data["performance_analysis"] = performance_analysis
        
        # Run with retry logic
        def _run_report_generation():
            result = Runner.run_sync(
                starting_agent=agent,
                input=f"Please generate a consolidated securities report: {json.dumps(input_data)}"
            )
            
            # Extract report from result
            report = ""
            if hasattr(result, 'agent_outputs') and result.agent_outputs:
                for output in result.agent_outputs:
                    if output.get('tool') == 'generate_consolidated_report' and isinstance(output.get('tool_result'), str):
                        report = output.get('tool_result')
                        break
            
            return report
        
        return self._retry_with_backoff(_run_report_generation, cache_enabled=cache_enabled)
    
    def clear_cache(self):
        """Clear the results cache."""
        self._results_cache = {}
        logger.info("Cache cleared")