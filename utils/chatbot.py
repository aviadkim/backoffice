import google.cloud.aiplatform as aiplatform
import os
import google.generativeai as genai
import json
import logging

logger = logging.getLogger(__name__)

class GeminiChatbot:
    """Chatbot powered by Google's Gemini model."""
    
    def __init__(self, api_key=None):
        """Initialize Gemini chatbot"""
        self.initialized = False
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-pro')
                self.chat = self.model.start_chat(history=[])
                self.initialized = True
            except Exception as e:
                logger.error(f"Error initializing Gemini: {e}")
    
    def process_query(self, query, context=None):
        """Process a user query and return a response."""
        if not self.initialized:
            return "Chatbot is not initialized. Please provide a valid API key."
        
        try:
            # Prepare context if provided
            prompt = query
            if context:
                context_str = json.dumps(context, indent=2, ensure_ascii=False)
                prompt = f"Consider the following financial data:\n\n{context_str}\n\nUser query: {query}"
            
            # Generate response
            response = self.chat.send_message(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
