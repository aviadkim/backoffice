import google.cloud.aiplatform as aiplatform
import os
import google.generativeai as genai

class GeminiChatbot:
    def __init__(self, api_key=None):
        """Initialize Gemini chatbot"""
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.chat = self.model.start_chat(history=[])
            self.initialized = True
        else:
            self.initialized = False
    
    def process_query(self, query: str, transactions=None):
        """Process user query using Gemini"""
        if not self.initialized:
            return "אנא הגדר מפתח API בהגדרות כדי להשתמש בעוזר החכם."
        
        context = ""
        if transactions:
            # Build financial context from transactions
            total_income = sum(t['amount'] for t in transactions if t['amount'] > 0)
            total_expenses = sum(t['amount'] for t in transactions if t['amount'] < 0)
            
            context = f"""
            מידע פיננסי:
            - סך הכל הכנסות: ₪{total_income:,.2f}
            - סך הכל הוצאות: ₪{abs(total_expenses):,.2f}
            - מאזן: ₪{(total_income + total_expenses):,.2f}
            
            פירוט עסקאות:
            """
            
            for t in transactions[:10]:  # Limit to 10 transactions for context size
                context += f"- {t['date']}: {t['description']} - ₪{t['amount']:,.2f} ({t['category']})\n"
        
        prompt = f"{context}\n\nשאלה: {query}\n\nתשובה בעברית:"
        
        try:
            response = self.chat.send_message(prompt)
            return response.text
        except Exception as e:
            return f"שגיאה בתקשורת עם Gemini: {str(e)}"
