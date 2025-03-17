import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# הוספת תיקיית הפרויקט לנתיב
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.securities_pdf_processor import SecuritiesPDFProcessor
from utils.ocr_processor import extract_text_from_pdf
from utils.financial_analyzer import FinancialAnalyzer
from utils.pdf_integration import PDFIntegration

def process_pdfs() -> Dict[str, Any]:
    """Process all sample PDFs and return consolidated data."""
    
    # אתחול המעבדים
    securities_processor = SecuritiesPDFProcessor()
    financial_analyzer = FinancialAnalyzer()
    
    # עיבוד המסמכים
    print("מעבד את מסמכי הדוגמה...")
    
    # עיבוד המסמכים
    data = {
        'securities': [],
        'bank_data': None,
        'performance': None,
        'transactions': [],
        'analysis': {}
    }
    
    try:
        # עיבוד דוח ניירות ערך
        securities_path = 'samples/securities_report.pdf'
        if os.path.exists(securities_path):
            securities = securities_processor.process_pdf(securities_path)
            data['securities'] = securities
            
        # עיבוד חשבון בנק
        bank_path = 'samples/bank_statement.pdf'
        if os.path.exists(bank_path):
            bank_data = extract_text_from_pdf(bank_path)
            for item in bank_data:
                if item['type'] == 'bank_statement':
                    data['bank_data'] = item
                    # Categorize transactions
                    for transaction in item.get('transactions', []):
                        transaction['category'] = financial_analyzer.categorize_transaction(transaction)
                        data['transactions'].append(transaction)
                    break
            
        # עיבוד דוח ביצועים
        performance_path = 'samples/performance_report.pdf'
        if os.path.exists(performance_path):
            performance_data = extract_text_from_pdf(performance_path)
            for item in performance_data:
                if item['type'] == 'performance_report':
                    data['performance'] = item
                    break
        
        # Generate financial analysis
        if data['transactions']:
            data['analysis'] = {
                'trends': financial_analyzer.analyze_spending_trends(data['transactions']),
                'summary': financial_analyzer.generate_financial_summary(data['transactions']),
                'budget_alerts': financial_analyzer.check_budget_limits(data['transactions'], {
                    'food': 1000,
                    'entertainment': 500,
                    'shopping': 2000,
                    'transportation': 800,
                    'utilities': 1500
                })
            }
            
    except Exception as e:
        print(f"Error processing PDFs: {str(e)}")
        
    return data

def generate_report(data: Dict[str, Any]) -> str:
    """Generate consolidated financial report."""
    
    report = []
    
    # Add header
    report.append("# Consolidated Financial Report")
    report.append(f"Generated on: {datetime.now().strftime('%B %d, %Y')}\n")
    
    # Add summary section
    report.append("## Summary")
    
    # Calculate total assets value from securities
    total_assets = sum(security.get('market_value', 0) for security in data.get('securities', []))
    report.append(f"Total Assets Value: ${total_assets:,.2f}")
    
    # Add financial summary if available
    if data.get('analysis', {}).get('summary'):
        summary = data['analysis']['summary']
        report.append(f"Total Income: ${summary['total_income']:,.2f}")
        report.append(f"Total Expenses: ${summary['total_expenses']:,.2f}")
        report.append(f"Net Income: ${summary['net_income']:,.2f}")
        report.append(f"Average Transaction: ${summary['average_transaction']:,.2f}")
    
    # Add bank balance if available
    if data.get('bank_data') and data['bank_data'].get('balance') is not None:
        report.append(f"Bank Balance: ${data['bank_data']['balance']:,.2f}")
    else:
        report.append("Bank Balance: Not available")
    
    # Add performance summary if available
    if data.get('performance') and data['performance'].get('periods'):
        latest_period = data['performance']['periods'][0]
        if latest_period.get('annual_return') is not None:
            report.append(f"Annual Return (1 Month): {latest_period['annual_return']}%")
    
    # Add budget alerts if any
    if data.get('analysis', {}).get('budget_alerts'):
        report.append("\n### Budget Alerts")
        for alert in data['analysis']['budget_alerts']:
            severity_emoji = "⚠️" if alert['severity'] == 'high' else "⚡"
            report.append(f"{severity_emoji} {alert['category'].title()}: ${alert['excess']:,.2f} over budget")
    
    report.append("\n## Assets Details")
    
    # Add securities details
    if data.get('securities'):
        report.append("\n### Securities")
        for security in data['securities']:
            report.append(f"- {security.get('security_name', 'Unknown')} ({security.get('isin', 'No ISIN')})")
            report.append(f"  Quantity: {security.get('quantity', 0):,.0f}")
            report.append(f"  Price: ${security.get('price', 0):,.2f}")
            report.append(f"  Market Value: ${security.get('market_value', 0):,.2f}\n")
    
    # Add spending analysis if available
    if data.get('analysis', {}).get('trends'):
        report.append("\n## Spending Analysis")
        trends = data['analysis']['trends']
        
        # Add category breakdown
        if trends.get('category_breakdown'):
            report.append("\n### Category Breakdown")
            for category, stats in trends['category_breakdown'].items():
                report.append(f"- {category.title()}:")
                report.append(f"  Total: ${stats['total']:,.2f}")
                report.append(f"  Average: ${stats['average']:,.2f}")
                report.append(f"  Transactions: {stats['count']}")
    
    # Add recent transactions if available
    if data.get('transactions'):
        report.append("\n## Recent Transactions")
        for transaction in data['transactions'][:10]:  # Show last 10 transactions
            amount = transaction.get('amount', 0)
            amount_str = f"${amount:,.2f}" if amount >= 0 else f"(${abs(amount):,.2f})"
            report.append(f"- {transaction.get('date', 'Unknown Date')}: {transaction.get('description', 'Unknown')}")
            report.append(f"  Amount: {amount_str}")
            report.append(f"  Category: {transaction.get('category', 'Unclassified')}\n")
    
    # Add performance details if available
    if data.get('performance') and data['performance'].get('periods'):
        report.append("\n## Performance")
        for period in data['performance']['periods']:
            report.append(f"- {period.get('period', 'Unknown Period')}")
            if period.get('return') is not None:
                report.append(f"  Return: {period['return']}%")
            if period.get('annual_return') is not None:
                report.append(f"  Annual Return: {period['annual_return']}%\n")
    
    # Save report
    report_path = 'samples/consolidated_report.md'
    report_content = '\n'.join(report)
    
    try:
        os.makedirs('samples', exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"Report saved to {report_path}")
        print("\nReport content:")
        print(report_content)
    except Exception as e:
        print(f"Error saving report: {str(e)}")
        
    return report_content

def create_visualizations(data, output_dir):
    """Create and save financial visualizations"""
    # Set style for all plots
    plt.style.use('seaborn')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Spending by Category
    if data['transactions']:
        df_transactions = pd.DataFrame(data['transactions'])
        category_spending = df_transactions.groupby('category')['amount'].sum()
        
        plt.figure(figsize=(10, 6))
        category_spending.plot(kind='bar')
        plt.title('Spending by Category')
        plt.xlabel('Category')
        plt.ylabel('Amount (USD)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'spending_by_category.png'))
        plt.close()
    
    # 2. Monthly Spending Trend
    if data['transactions']:
        df_transactions['date'] = pd.to_datetime(df_transactions['date'])
        monthly_spending = df_transactions.groupby(df_transactions['date'].dt.to_period('M'))['amount'].sum()
        
        plt.figure(figsize=(12, 6))
        monthly_spending.plot(kind='line', marker='o')
        plt.title('Monthly Spending Trend')
        plt.xlabel('Month')
        plt.ylabel('Amount (USD)')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'monthly_spending_trend.png'))
        plt.close()
    
    # 3. Income vs Expenses
    if data['analysis']:
        income = data['analysis'].get('total_income', 0)
        expenses = data['analysis'].get('total_expenses', 0)
        
        plt.figure(figsize=(8, 8))
        plt.pie([income, expenses], labels=['Income', 'Expenses'], autopct='%1.1f%%')
        plt.title('Income vs Expenses')
        plt.savefig(os.path.join(output_dir, 'income_vs_expenses.png'))
        plt.close()

def export_to_excel(data, output_path):
    """Export financial data to Excel with multiple sheets"""
    with pd.ExcelWriter(output_path) as writer:
        # Transactions Sheet
        if data['transactions']:
            df_transactions = pd.DataFrame(data['transactions'])
            df_transactions.to_excel(writer, sheet_name='Transactions', index=False)
        
        # Summary Sheet
        summary_data = {
            'Metric': [
                'Total Assets',
                'Bank Balance',
                'Total Income',
                'Total Expenses',
                'Net Income',
                'Annual Return'
            ],
            'Value (USD)': [
                data['total_assets'],
                data['bank_balance'],
                data['analysis'].get('total_income', 0),
                data['analysis'].get('total_expenses', 0),
                data['analysis'].get('net_income', 0),
                data['analysis'].get('annual_return', 0)
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        # Category Analysis Sheet
        if data['transactions']:
            df_transactions = pd.DataFrame(data['transactions'])
            category_analysis = df_transactions.groupby('category').agg({
                'amount': ['sum', 'mean', 'count']
            }).round(2)
            category_analysis.columns = ['Total Amount', 'Average Amount', 'Number of Transactions']
            category_analysis.to_excel(writer, sheet_name='Category Analysis')

def generate_consolidated_report():
    """Generate a consolidated financial report from multiple documents"""
    try:
        # Initialize processors
        securities_processor = SecuritiesPDFProcessor()
        pdf_integration = PDFIntegration()
        financial_analyzer = FinancialAnalyzer()
        
        # Create samples directory if it doesn't exist
        os.makedirs('samples', exist_ok=True)
        
        # Process documents
        data = {
            'total_assets': 0,
            'bank_balance': 0,
            'securities': [],
            'bank_data': None,
            'performance': None,
            'transactions': [],
            'analysis': {}
        }
        
        # Process securities report
        securities_path = 'samples/securities_report.pdf'
        if os.path.exists(securities_path):
            securities_data = securities_processor.process_securities_pdf(securities_path)
            if securities_data:
                data['securities'] = securities_data
                data['total_assets'] = sum(security['value_usd'] for security in securities_data)
        
        # Process bank statement
        bank_path = 'samples/bank_statement.pdf'
        if os.path.exists(bank_path):
            bank_data = pdf_integration.process_financial_document(bank_path, 'bank')
            if bank_data:
                data['bank_data'] = bank_data
                # Extract transactions and categorize them
                transactions = []
                for page in bank_data:
                    for table in page.get('tables', []):
                        for row in table:
                            if len(row) >= 4:  # Ensure row has enough columns
                                transaction = {
                                    'date': row[0],
                                    'description': row[1],
                                    'amount': float(row[2].replace(',', '')),
                                    'balance': float(row[3].replace(',', ''))
                                }
                                # Categorize transaction
                                transaction['category'] = financial_analyzer.categorize_transaction(transaction)
                                transactions.append(transaction)
                
                data['transactions'] = transactions
                if transactions:
                    data['bank_balance'] = transactions[-1]['balance']
        
        # Process performance report
        performance_path = 'samples/performance_report.pdf'
        if os.path.exists(performance_path):
            performance_data = pdf_integration.process_financial_document(performance_path, 'performance')
            if performance_data:
                data['performance'] = performance_data
        
        # Generate financial analysis
        if data['transactions']:
            data['analysis'] = financial_analyzer.generate_financial_summary(data['transactions'])
        
        # Create visualizations
        create_visualizations(data, 'samples/visualizations')
        
        # Export to Excel
        export_to_excel(data, 'samples/financial_report.xlsx')
        
        # Generate markdown report
        report = f"""# Consolidated Financial Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Total Assets Value: ${data['total_assets']:,.2f}
- Bank Balance: ${data['bank_balance']:,.2f}
- Total Income: ${data['analysis'].get('total_income', 0):,.2f}
- Total Expenses: ${data['analysis'].get('total_expenses', 0):,.2f}
- Net Income: ${data['analysis'].get('net_income', 0):,.2f}
- Annual Return: {data['analysis'].get('annual_return', 0):.2f}%

## Assets Details
"""
        for security in data['securities']:
            report += f"- {security['name']}: {security['quantity']} units, Value: ${security['value_usd']:,.2f}\n"
        
        report += "\n## Recent Transactions\n"
        if data['transactions']:
            for transaction in data['transactions'][-5:]:  # Show last 5 transactions
                report += f"- {transaction['date']}: {transaction['description']} (${transaction['amount']:,.2f}) - {transaction['category']}\n"
        
        report += "\n## Performance\n"
        if data['performance']:
            for page in data['performance']:
                for table in page.get('tables', []):
                    for row in table:
                        report += f"- {row[0]}: {row[1]}\n"
        
        # Add budget alerts if any
        if data['analysis'].get('budget_alerts'):
            report += "\n## Budget Alerts\n"
            for alert in data['analysis']['budget_alerts']:
                report += f"- {alert['category']}: {alert['message']}\n"
        
        # Save report
        with open('samples/consolidated_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("Report generated successfully!")
        print("\nFiles generated:")
        print("1. samples/consolidated_report.md - Detailed markdown report")
        print("2. samples/financial_report.xlsx - Excel report with multiple sheets")
        print("3. samples/visualizations/ - Directory containing financial charts")
        
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        raise

if __name__ == "__main__":
    generate_consolidated_report() 