import os
from datetime import datetime, timedelta
from fpdf import FPDF

def create_securities_report():
    """Create a sample securities report PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add header
    pdf.cell(200, 10, txt="Securities Report", ln=True, align='C')
    pdf.cell(200, 10, txt="As of March 17, 2024", ln=True, align='C')
    pdf.ln(10)
    
    # Add securities data
    securities = [
        {
            "name": "Apple Inc.",
            "isin": "US0378331005",
            "quantity": 100,
            "price": 175.50,
            "market_value": 17550.00
        },
        {
            "name": "Microsoft Corporation",
            "isin": "US5949181045",
            "quantity": 75,
            "price": 425.30,
            "market_value": 31897.50
        },
        {
            "name": "Amazon.com Inc.",
            "isin": "US0231351067",
            "quantity": 50,
            "price": 175.35,
            "market_value": 8767.50
        },
        {
            "name": "Tesla Inc.",
            "isin": "US88160R1014",
            "quantity": 40,
            "price": 172.82,
            "market_value": 6912.80
        }
    ]
    
    for security in securities:
        pdf.cell(200, 10, txt=f"{security['name']} ({security['isin']})", ln=True)
        pdf.cell(200, 10, txt=f"Quantity: {security['quantity']:,.0f}", ln=True)
        pdf.cell(200, 10, txt=f"Price: ${security['price']:,.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Market Value: ${security['market_value']:,.2f}", ln=True)
        pdf.ln(5)
    
    # Save the PDF
    os.makedirs('samples', exist_ok=True)
    pdf.output("samples/securities_report.pdf")

def create_bank_statement():
    """Create a sample bank statement PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add header
    pdf.cell(200, 10, txt="Bank Statement", ln=True, align='C')
    pdf.cell(200, 10, txt="March 1-17, 2024", ln=True, align='C')
    pdf.ln(10)
    
    # Add transactions
    transactions = [
        {
            "date": "2024-03-01",
            "description": "Opening Balance",
            "amount": None,
            "balance": 50000.00
        },
        {
            "date": "2024-03-05",
            "description": "Stock Purchase - AAPL",
            "amount": -17550.00,
            "balance": 32450.00
        },
        {
            "date": "2024-03-07",
            "description": "Stock Purchase - MSFT",
            "amount": -31897.50,
            "balance": 552.50
        },
        {
            "date": "2024-03-10",
            "description": "Deposit",
            "amount": 20000.00,
            "balance": 20552.50
        },
        {
            "date": "2024-03-12",
            "description": "Stock Purchase - AMZN",
            "amount": -8767.50,
            "balance": 11785.00
        },
        {
            "date": "2024-03-15",
            "description": "Stock Purchase - TSLA",
            "amount": -6912.80,
            "balance": 4872.20
        }
    ]
    
    for transaction in transactions:
        pdf.cell(200, 10, txt=f"Date: {transaction['date']}", ln=True)
        pdf.cell(200, 10, txt=f"Description: {transaction['description']}", ln=True)
        if transaction['amount'] is not None:
            pdf.cell(200, 10, txt=f"Amount: ${transaction['amount']:,.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Balance: ${transaction['balance']:,.2f}", ln=True)
        pdf.ln(5)
    
    # Save the PDF
    pdf.output("samples/bank_statement.pdf")

def create_performance_report():
    """Create a sample performance report PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add header
    pdf.cell(200, 10, txt="Performance Report", ln=True, align='C')
    pdf.cell(200, 10, txt="As of March 17, 2024", ln=True, align='C')
    pdf.ln(10)
    
    # Add performance data
    performance_data = [
        {
            "period": "1 Month",
            "return": 2.5,
            "annual_return": 30.0,
            "std_dev": 15.2
        },
        {
            "period": "3 Months",
            "return": 5.8,
            "annual_return": 23.2,
            "std_dev": 14.8
        },
        {
            "period": "6 Months",
            "return": 12.3,
            "annual_return": 24.6,
            "std_dev": 14.5
        },
        {
            "period": "1 Year",
            "return": 22.7,
            "annual_return": 22.7,
            "std_dev": 13.9
        }
    ]
    
    for period in performance_data:
        pdf.cell(200, 10, txt=f"Period: {period['period']}", ln=True)
        pdf.cell(200, 10, txt=f"Return: {period['return']}%", ln=True)
        pdf.cell(200, 10, txt=f"Annual Return: {period['annual_return']}%", ln=True)
        pdf.cell(200, 10, txt=f"Standard Deviation: {period['std_dev']}%", ln=True)
        pdf.ln(5)
    
    # Save the PDF
    pdf.output("samples/performance_report.pdf")

def create_all_sample_pdfs():
    """Create all sample PDFs."""
    create_securities_report()
    create_bank_statement()
    create_performance_report()
    print("Sample PDFs created in samples directory")

if __name__ == "__main__":
    create_all_sample_pdfs() 