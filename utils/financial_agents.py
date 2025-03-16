from agents import Agent, function_tool
from utils.model_adapter import GeminiAdapter
import os
from dotenv import load_dotenv
import json
import pandas as pd
import logging

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

# Get API key from environment or use parameter
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_gemini_model(api_key=None):
    """Get the Gemini model adapter."""
    api_key = api_key or GEMINI_API_KEY
    if not api_key:
        raise ValueError("Gemini API key is required")
    return GeminiAdapter(api_key)

# Define tool functions for the agents
@function_tool
def extract_transactions_from_text(text: str) -> list:
    """
    Extract financial transactions from document text.
    
    Args:
        text: The text content of a financial document
        
    Returns:
        A list of transaction objects with date, description, amount, and category
    """
    # This is a placeholder that would call your existing extraction logic
    # For now, we'll return a simplified implementation
    import re
    
    transactions = []
    
    # Simple pattern matching for dates and amounts
    date_pattern = r'\d{1,2}[/\.-]\d{1,2}[/\.-]\d{2,4}'
    amount_pattern = r'[-+]?[\d,]+\.\d{2}'
    
    lines = text.split('\n')
    for line in lines:
        if not line.strip():
            continue
            
        amount_match = re.search(amount_pattern, line)
        if amount_match:
            # Extract amount
            amount_str = amount_match.group(0).replace(',', '')
            amount = float(amount_str)
            
            # Look for date
            date_match = re.search(date_pattern, line)
            date_str = date_match.group(0) if date_match else ""
            
            # Extract description
            description = line
            if date_match:
                description = description.replace(date_match.group(0), '')
            if amount_match:
                description = description.replace(amount_match.group(0), '')
                
            description = description.strip()
            
            # Basic category detection
            category = "לא מסווג"
            if amount > 0:
                category = "הכנסה"
            elif "שכירות" in description or "דירה" in description:
                category = "דיור"
            elif "מזון" in description or "סופר" in description or "מסעדה" in description:
                category = "מזון"
            
            transactions.append({
                "date": date_str,
                "description": description,
                "amount": amount,
                "category": category
            })
    
    return transactions

@function_tool
def analyze_spending_patterns(transactions: list) -> dict:
    """
    Analyze spending patterns from a list of transactions.
    
    Args:
        transactions: List of transaction objects
        
    Returns:
        Analysis results including totals by category, trends, and insights
    """
    try:
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(transactions)
        
        # Calculate basic metrics
        total_income = df[df['amount'] > 0]['amount'].sum()
        total_expenses = df[df['amount'] < 0]['amount'].sum()
        
        # Group by category
        category_totals = df.groupby('category')['amount'].sum().to_dict()
        
        # Find largest expense and income
        largest_expense = df[df['amount'] < 0].nlargest(1, key=lambda x: abs(x['amount'])).to_dict('records')
        largest_income = df[df['amount'] > 0].nlargest(1, 'amount').to_dict('records')
        
        return {
            "summary": {
                "total_income": float(total_income),
                "total_expenses": float(total_expenses),
                "net_balance": float(total_income + total_expenses)
            },
            "category_analysis": category_totals,
            "largest_transactions": {
                "expense": largest_expense[0] if largest_expense else None,
                "income": largest_income[0] if largest_income else None
            }
        }
    except Exception as e:
        logger.error(f"Error analyzing spending patterns: {str(e)}")
        return {"error": str(e)}

@function_tool
def generate_financial_advice(spending_analysis: dict) -> dict:
    """
    Generate financial advice based on spending analysis.
    
    Args:
        spending_analysis: Analysis of spending patterns
        
    Returns:
        Personalized financial advice and recommendations
    """
    # This would normally use the AI to generate advice,
    # but for now we'll use rule-based recommendations
    advice = []
    recommendations = []
    
    summary = spending_analysis.get("summary", {})
    categories = spending_analysis.get("category_analysis", {})
    
    # Check if expenses exceed income
    if summary.get("net_balance", 0) < 0:
        advice.append("ההוצאות שלך גבוהות מההכנסות. כדאי לשקול צמצום הוצאות.")
        
    # Check category-specific issues
    housing_expense = abs(categories.get("דיור", 0))
    total_expenses = abs(summary.get("total_expenses", 0))
    
    if housing_expense / total_expenses > 0.4:
        advice.append("הוצאות הדיור שלך מהוות יותר מ-40% מסך ההוצאות, שזה גבוה מהמומלץ.")
        recommendations.append("שקול אפשרויות דיור חסכוניות יותר או הגדלת הכנסה.")
    
    # Add general recommendations
    recommendations.append("הקצה 20% מההכנסה לחיסכון או השקעות.")
    recommendations.append("בדוק אם יש דרכים לצמצם הוצאות חודשיות קבועות.")
    
    return {
        "advice": advice,
        "recommendations": recommendations
    }

@function_tool
def generate_financial_report(transactions: list, analysis: dict, advice: dict) -> str:
    """
    Generate a comprehensive financial report.
    
    Args:
        transactions: List of financial transactions
        analysis: Spending pattern analysis
        advice: Financial advice and recommendations
        
    Returns:
        A formatted report as a string
    """
    summary = analysis.get("summary", {})
    category_analysis = analysis.get("category_analysis", {})
    
    report = "# דוח פיננסי\n\n"
    
    # Summary section
    report += "## סיכום\n"
    report += f"- סך הכנסות: ₪{summary.get('total_income', 0):,.2f}\n"
    report += f"- סך הוצאות: ₪{abs(summary.get('total_expenses', 0)):,.2f}\n"
    report += f"- מאזן נטו: ₪{summary.get('net_balance', 0):,.2f}\n\n"
    
    # Category breakdown
    report += "## פילוח הוצאות לפי קטגוריה\n"
    for category, amount in category_analysis.items():
        if amount < 0:  # Only show expenses
            report += f"- {category}: ₪{abs(amount):,.2f}\n"
    report += "\n"
    
    # Advice section
    report += "## המלצות פיננסיות\n"
    for advice_item in advice.get("advice", []):
        report += f"- {advice_item}\n"
    report += "\n"
    
    # Recommendations
    report += "## צעדים מומלצים\n"
    for rec in advice.get("recommendations", []):
        report += f"- {rec}\n"
    
    return report

# Define the agents
def create_document_processing_agent(api_key=None):
    """Create a document processing agent."""
    return Agent(
        name="מעבד מסמכים פיננסיים",
        instructions="""
        אתה סוכן המתמחה בעיבוד מסמכים פיננסיים.
        תפקידך הוא לחלץ עסקאות ומידע פיננסי ממסמכים כמו דפי חשבון ודוחות פיננסיים.
        אתה צריך לזהות תאריכים, סכומים, תיאורים וקטגוריות בצורה מדויקת.
        """,
        model=get_gemini_model(api_key),
        tools=[extract_transactions_from_text]
    )

def create_financial_analysis_agent(api_key=None):
    """Create a financial analysis agent."""
    return Agent(
        name="מנתח פיננסי",
        instructions="""
        אתה סוכן המתמחה בניתוח נתונים פיננסיים.
        תפקידך הוא לנתח דפוסי הוצאות, לזהות מגמות, ולספק תובנות על התנהגות פיננסית.
        אתה צריך להבחין בין הכנסות והוצאות ולחשב סטטיסטיקות חשובות.
        """,
        model=get_gemini_model(api_key),
        tools=[analyze_spending_patterns]
    )

def create_financial_advisor_agent(api_key=None):
    """Create a financial advisor agent."""
    return Agent(
        name="יועץ פיננסי",
        instructions="""
        אתה סוכן המתמחה בייעוץ פיננסי.
        תפקידך הוא לספק עצות פיננסיות מותאמות אישית בהתבסס על ניתוח ההוצאות.
        אתה צריך להציע המלצות קונקרטיות לחיסכון, השקעות, וניהול תקציב.
        """,
        model=get_gemini_model(api_key),
        tools=[generate_financial_advice]
    )

def create_report_generation_agent(api_key=None):
    """Create a report generation agent."""
    return Agent(
        name="מחולל דוחות",
        instructions="""
        אתה סוכן המתמחה ביצירת דוחות פיננסיים.
        תפקידך הוא לקחת נתונים פיננסיים, ניתוח ועצות, ולארגן אותם בדוח מבני ברור.
        הדוחות שלך צריכים להיות מדויקים, קריאים ובעלי ערך למשתמש.
        """,
        model=get_gemini_model(api_key),
        tools=[generate_financial_report]
    )

def create_main_agent(api_key=None):
    """Create the main orchestration agent."""
    return Agent(
        name="עוזר פיננסי ראשי",
        instructions="""
        אתה העוזר הפיננסי הראשי שמתאם את כל הפעילות הפיננסית.
        תפקידך הוא להבין את צרכי המשתמש ולהפנות אותם לסוכן המתאים.
        לעיבוד מסמכים - הפנה למעבד המסמכים.
        לניתוח פיננסי - הפנה למנתח הפיננסי.
        לעצות השקעה וחיסכון - הפנה ליועץ הפיננסי.
        ליצירת דוחות - הפנה למחולל הדוחות.
        """,
        model=get_gemini_model(api_key),
        handoffs=[
            create_document_processing_agent(api_key),
            create_financial_analysis_agent(api_key),
            create_financial_advisor_agent(api_key),
            create_report_generation_agent(api_key)
        ]
    )
