import google.generativeai as genai
import json
import logging

logger = logging.getLogger(__name__)

class GeminiAdapter:
    """Adapter to make Gemini models compatible with OpenAI's Agents SDK."""
    
    def __init__(self, api_key, model_name="gemini-pro"):
        """Initialize the Gemini adapter."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.history = []
    
    def create(self, messages, tools=None, **kwargs):
        """
        Implement the interface expected by Agents SDK.
        
        Args:
            messages: List of message objects with 'role' and 'content' keys
            tools: Optional tools spec to be converted to Gemini's function calling format
            
        Returns:
            A response object compatible with Agents SDK expectations
        """
        try:
            # Convert messages to the prompt
            prompt = self._convert_messages_to_prompt(messages)
            
            # Handle function/tool calling if provided
            if tools:
                # Convert OpenAI tool format to Gemini function format
                gemini_tools = self._convert_tools_to_gemini_format(tools)
                response = self.model.generate_content(
                    prompt,
                    generation_config={"temperature": kwargs.get("temperature", 0.7)},
                    tools=gemini_tools
                )
            else:
                # Regular prompt without tools
                response = self.model.generate_content(
                    prompt,
                    generation_config={"temperature": kwargs.get("temperature", 0.7)}
                )
            
            # Convert Gemini response to OpenAI format
            return self._format_gemini_response(response, tools)
            
        except Exception as e:
            logger.error(f"Error using Gemini model: {str(e)}")
            # Return a compatible error format
            return {
                "choices": [{
                    "message": {
                        "content": f"Error: {str(e)}",
                        "role": "assistant"
                    }
                }]
            }
    
    def _convert_messages_to_prompt(self, messages):
        """Convert OpenAI-style messages to Gemini prompt."""
        prompt = ""
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                # System messages become part of the prompt
                prompt += f"Instructions: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
        
        if not prompt.endswith("Assistant: "):
            prompt += "Assistant: "
        
        return prompt
    
    def _convert_tools_to_gemini_format(self, tools):
        """Convert OpenAI tool format to Gemini function format."""
        gemini_tools = []
        
        for tool in tools:
            if tool.get("type") == "function" and "function" in tool:
                function_spec = tool["function"]
                
                gemini_tool = {
                    "name": function_spec.get("name", ""),
                    "description": function_spec.get("description", ""),
                    "parameters": {
                        "type": "object",
                        "properties": function_spec.get("parameters", {}).get("properties", {}),
                        "required": function_spec.get("parameters", {}).get("required", [])
                    }
                }
                gemini_tools.append(gemini_tool)
        
        return gemini_tools if gemini_tools else None
    
    def _format_gemini_response(self, gemini_response, tools=None):
        """Format Gemini response to match OpenAI's response format."""
        try:
            # Extract the text from Gemini response
            if hasattr(gemini_response, "text"):
                content = gemini_response.text
            else:
                content = str(gemini_response)
            
            # Check if there's a function call in the response
            function_call = None
            if tools and hasattr(gemini_response, "parts"):
                for part in gemini_response.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        function_call = {
                            "name": part.function_call.name,
                            "arguments": part.function_call.args
                        }
            
            # Create the response object
            response_message = {
                "content": content,
                "role": "assistant"
            }
            
            # Add function_call if present
            if function_call:
                response_message["function_call"] = function_call
            
            return {
                "choices": [{
                    "message": response_message
                }]
            }
            
        except Exception as e:
            logger.error(f"Error formatting Gemini response: {str(e)}")
            return {
                "choices": [{
                    "message": {
                        "content": "Error processing response.",
                        "role": "assistant"
                    }
                }]
            }
