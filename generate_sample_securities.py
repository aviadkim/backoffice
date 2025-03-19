import os
import random
from datetime import datetime
from fpdf import FPDF

# Define a list of real securities with their ISINs and names
securities = [
    {"isin": "US0378331005", "name": "Apple Inc.", "price": 182.52, "quantity": 100, "value": 18252.00, "currency": "USD"},
    {"isin": "US5949181045", "name": "Microsoft Corp.", "price": 417.88, "quantity": 50, "value": 20894.00, "currency": "USD"},
    {"isin": "US0231351067", "name": "Amazon.com Inc.", "price": 178.75, "quantity": 75, "value": 13406.25, "currency": "USD"},
    {"isin": "US88160R1014", "name": "Tesla Inc.", "price": 177.77, "quantity": 80, "value": 14221.60, "currency": "USD"},
    {"isin": "US30303M1027", "name": "Meta Platforms Inc.", "price": 485.58, "quantity": 30, "value": 14567.40, "currency": "USD"},
    {"isin": "US02079K1079", "name": "Alphabet Inc. Class C", "price": 174.63, "quantity": 60, "value": 10477.80, "currency": "USD"},
    {"isin": "US67066G1040", "name": "NVIDIA Corp.", "price": 919.13, "quantity": 25, "value": 22978.25, "currency": "USD"},
    {"isin": "US0846707026", "name": "Berkshire Hathaway Inc. Class B", "price": 405.42, "quantity": 40, "value": 16216.80, "currency": "USD"},
    {"isin": "US46625H1005", "name": "JPMorgan Chase & Co.", "price": 197.45, "quantity": 70, "value": 13821.50, "currency": "USD"},
    {"isin": "US9311421039", "name": "Walmart Inc.", "price": 60.20, "quantity": 120, "value": 7224.00, "currency": "USD"},
    {"isin": "US4781601046", "name": "Johnson & Johnson", "price": 158.36, "quantity": 90, "value": 14252.40, "currency": "USD"},
    {"isin": "US1912161007", "name": "Coca-Cola Co.", "price": 62.81, "quantity": 150, "value": 9421.50, "currency": "USD"},
    {"isin": "US7427181091", "name": "Procter & Gamble Co.", "price": 161.66, "quantity": 85, "value": 13741.10, "currency": "USD"},
    {"isin": "US5801351017", "name": "McDonald's Corp.", "price": 289.42, "quantity": 45, "value": 13023.90, "currency": "USD"},
    {"isin": "US1101221083", "name": "Bristol-Myers Squibb Co.", "price": 51.52, "quantity": 200, "value": 10304.00, "currency": "USD"},
    {"isin": "US92343V1044", "name": "Verizon Communications Inc.", "price": 39.46, "quantity": 180, "value": 7102.80, "currency": "USD"},
    {"isin": "US6516391066", "name": "Newmont Corp.", "price": 40.17, "quantity": 220, "value": 8837.40, "currency": "USD"},
    {"isin": "US0605051046", "name": "Bank of America Corp.", "price": 37.00, "quantity": 240, "value": 8880.00, "currency": "USD"},
    {"isin": "US9497461015", "name": "Wells Fargo & Co.", "price": 57.66, "quantity": 160, "value": 9225.60, "currency": "USD"},
    {"isin": "US29786A1060", "name": "Etsy Inc.", "price": 72.51, "quantity": 110, "value": 7976.10, "currency": "USD"},
    {"isin": "US00206R1023", "name": "AT&T Inc.", "price": 17.08, "quantity": 350, "value": 5978.00, "currency": "USD"},
    {"isin": "US7170811035", "name": "Pfizer Inc.", "price": 27.82, "quantity": 320, "value": 8902.40, "currency": "USD"},
    {"isin": "US1729674242", "name": "Citigroup Inc.", "price": 58.71, "quantity": 140, "value": 8219.40, "currency": "USD"},
    {"isin": "US5128071082", "name": "Lam Research Corp.", "price": 940.55, "quantity": 12, "value": 11286.60, "currency": "USD"},
    {"isin": "US4370761029", "name": "Home Depot Inc.", "price": 367.33, "quantity": 35, "value": 12856.55, "currency": "USD"}
]

def create_securities_pdf(output_path="sample_securities_25.pdf"):
    """Create a sample PDF with a list of securities"""
    pdf = FPDF()
    pdf.add_page()
    
    # Set font
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Sample Securities Holdings Report", 0, 1, "C")
    
    # Add date
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Report Date: {datetime.now().strftime('%Y-%m-%d')}", 0, 1, "R")
    
    # Add account info
    pdf.cell(0, 10, "Account: SAMPLE-123456", 0, 1)
    pdf.cell(0, 10, "Portfolio Value: $297,570.35", 0, 1)
    pdf.ln(5)
    
    # Add table header
    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 10, "ISIN", 1, 0, "C")
    pdf.cell(60, 10, "Security Name", 1, 0, "C")
    pdf.cell(25, 10, "Price", 1, 0, "C")
    pdf.cell(20, 10, "Quantity", 1, 0, "C")
    pdf.cell(30, 10, "Value", 1, 0, "C")
    pdf.cell(15, 10, "Currency", 1, 1, "C")
    
    # Add securities
    pdf.set_font("Arial", "", 9)
    for security in securities:
        pdf.cell(40, 8, security["isin"], 1, 0)
        pdf.cell(60, 8, security["name"], 1, 0)
        pdf.cell(25, 8, f"{security['price']:.2f}", 1, 0, "R")
        pdf.cell(20, 8, f"{security['quantity']}", 1, 0, "R")
        pdf.cell(30, 8, f"{security['value']:.2f}", 1, 0, "R")
        pdf.cell(15, 8, security["currency"], 1, 1, "C")
    
    # Add summary
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, f"Total Securities: {len(securities)}", 0, 1)
    
    # Add disclaimer
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "Disclaimer: This is a sample report generated for testing purposes only. The securities information presented here is not real investment advice and should not be used for making investment decisions.")
    
    # Save the PDF
    pdf.output(output_path)
    print(f"Sample securities PDF created at: {output_path}")

if __name__ == "__main__":
    create_securities_pdf() 