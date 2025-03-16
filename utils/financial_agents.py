from utils.gimini_agents import Agent, function_tool
import os
from dotenv import load_dotenv
import json
import pandas as pd
import logging
import google.generativeai as genai

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

# Get API key from environment or use parameter
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_gemini_model(api_key=None):
    """Get the Gemini model."""
    api_key = api_key or GEMINI_API_KEY
    if not api_key:
        raise ValueError("Gemini API key is required")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-pro")

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

@function_tool
def analyze_securities_by_isin(transactions: list, report_date: str = None) -> dict:
    """
    Analyze securities holdings by ISIN across different banks/accounts.
    
    Args:
        transactions: List of securities transactions with ISIN details
        report_date: Optional date to filter transactions
        
    Returns:
        Consolidated analysis of securities by ISIN
    """
    # Group securities by ISIN
    isin_groups = {}
    
    for tx in transactions:
        isin = tx.get('isin')
        if not isin:
            continue
            
        if isin not in isin_groups:
            isin_groups[isin] = {
                'security_name': tx.get('security_name', 'Unknown'),
                'holdings': [],
                'total_value': 0,
                'price_discrepancies': False,
                'banks': set()
            }
        
        isin_groups[isin]['holdings'].append(tx)
        isin_groups[isin]['total_value'] += tx.get('market_value', 0)
        isin_groups[isin]['banks'].add(tx.get('bank', 'Unknown'))
        
    # Check for price discrepancies
    for isin, data in isin_groups.items():
        prices = [h.get('price', 0) for h in data['holdings']]
        if len(prices) > 1 and max(prices) - min(prices) > 0.01:  # Allow for small rounding differences
            data['price_discrepancies'] = True
            data['min_price'] = min(prices)
            data['max_price'] = max(prices)
            data['price_difference_pct'] = (max(prices) - min(prices)) / min(prices) * 100 if min(prices) > 0 else 0
    
    # Convert sets to lists for JSON serialization
    for isin, data in isin_groups.items():
        data['banks'] = list(data['banks'])
    
    return {
        'report_date': report_date,
        'total_isins': len(isin_groups),
        'total_portfolio_value': sum(data['total_value'] for data in isin_groups.values()),
        'securities': isin_groups
    }

@function_tool
def analyze_performance_over_time(historical_data: list, grouping: str = "monthly") -> dict:
    """
    Analyze performance of securities over time.
    
    Args:
        historical_data: List of historical holdings data with dates
        grouping: Time period for grouping ("weekly", "monthly", "quarterly", "ytd")
        
    Returns:
        Performance analysis with time-based comparisons
    """
    # Group by time period and calculate performance metrics
    # Implementation would depend on the structure of your historical_data
    
    # Sample structure
    return {
        "time_series": {
            # Example entries
            "2023-01": {"total_value": 150000, "change_pct": None},
            "2023-02": {"total_value": 152500, "change_pct": 1.67},
            # More periods...
        },
        "by_isin": {
            # Example for one ISIN
            "US0378331005": {  # Apple Inc.
                "name": "Apple Inc.",
                "time_series": {
                    "2023-01": {"value": 12500, "price": 142.53},
                    "2023-02": {"value": 13200, "price": 150.82, "change_pct": 5.82},
                    # More periods...
                }
            }
            # More ISINs...
        }
    }

@function_tool
def generate_consolidated_report(securities_analysis: dict, performance_analysis: dict = None) -> str:
    """
    Generate a comprehensive consolidated report of securities holdings.
    
    Args:
        securities_analysis: Analysis of securities by ISIN
        performance_analysis: Optional time-based performance analysis
        
    Returns:
        A formatted report as a string
    """
    # Create detailed report with multiple sections
    report = "# Consolidated Securities Holdings Report\n\n"
    
    # Summary section
    report += "## Summary\n"
    report += f"- Total Portfolio Value: ${securities_analysis['total_portfolio_value']:,.2f}\n"
    report += f"- Number of Securities: {securities_analysis['total_isins']}\n"
    report += f"- Report Date: {securities_analysis['report_date']}\n\n"
    
    # Securities with price discrepancies
    discrepancies = {isin: data for isin, data in securities_analysis['securities'].items() 
                    if data.get('price_discrepancies', False)}
    
    if discrepancies:
        report += "## Price Discrepancies\n"
        report += "The following securities have different prices across accounts:\n\n"
        
        for isin, data in discrepancies.items():
            report += f"### {data['security_name']} ({isin})\n"
            report += f"- Min Price: ${data['min_price']:,.2f}\n"
            report += f"- Max Price: ${data['max_price']:,.2f}\n"
            report += f"- Difference: {data['price_difference_pct']:.2f}%\n\n"
    
    # Securities by value
    report += "## Securities by Value\n\n"
    report += "| ISIN | Security Name | Total Value | Banks |\n"
    report += "| ---- | ------------- | ----------- | ----- |\n"
    
    sorted_securities = sorted(
        securities_analysis['securities'].items(), 
        key=lambda x: x[1]['total_value'], 
        reverse=True
    )
    
    for isin, data in sorted_securities:
        banks_str = ", ".join(sorted(data['banks']))
        report += f"| {isin} | {data['security_name']} | ${data['total_value']:,.2f} | {banks_str} |\n"
    
    # Performance over time if provided
    if performance_analysis:
        report += "\n## Performance Over Time\n\n"
        # Add time-based performance information
    
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
        כשאתה מקבל מסמך פיננסי, קרא בעיון והשתמש בפונקציה extract_transactions_from_text כדי לחלץ את העסקאות.
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
        השתמש בפונקציה analyze_spending_patterns כדי לנתח את הנתונים הפיננסיים שניתנים לך.
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
        השתמש בפונקציה generate_financial_advice כדי לייצר עצות פיננסיות רלוונטיות.
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
        השתמש בפונקציה generate_financial_report כדי לייצר דוח פיננסי מקיף.
        """,
        model=get_gemini_model(api_key),
        tools=[generate_financial_report]
    )

# Create new securities analysis agent
def create_securities_analysis_agent(api_key=None):
    """Create a securities analysis agent."""
    return Agent(
        name="מנתח ניירות ערך",
        instructions="""
        אתה סוכן המתמחה בניתוח ניירות ערך לפי ISIN.
        תפקידך הוא לנתח החזקות ניירות ערך מחשבונות שונים ולזהות הבדלי מחירים.
        אתה תספק דוח מקיף עם מידע מפורט על כל נייר ערך והשוואה בין חשבונות.
        כשאתה מקבל רשימת עסקאות, השתמש בפונקציה analyze_securities_by_isin כדי לנתח אותן.
        """,
        model=get_gemini_model(api_key),
        tools=[analyze_securities_by_isin, analyze_performance_over_time, generate_consolidated_report]
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
        לניתוח ניירות ערך לפי ISIN - הפנה למנתח ניירות הערך.
        ענה בעברית על כל השאלות.
        """,
        model=get_gemini_model(api_key),
        handoffs=[
            create_document_processing_agent(api_key),
            create_financial_analysis_agent(api_key),
            create_financial_advisor_agent(api_key),
            create_report_generation_agent(api_key),
            create_securities_analysis_agent(api_key)
        ]
    )
