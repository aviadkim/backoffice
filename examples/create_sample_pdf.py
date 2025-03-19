from fpdf import FPDF
import os

def create_sample_securities_pdf():
    """Create a sample PDF with securities data for testing."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add header
    pdf.cell(200, 10, txt="Securities Statement", ln=1, align="C")
    pdf.ln(10)
    
    # Add sample securities data
    securities = [
        ["Security Name", "ISIN", "Quantity", "Price", "Market Value"],
        ["Apple Inc.", "US0378331005", "100", "150.25", "15,025.00"],
        ["Microsoft Corp", "US5949181045", "50", "280.50", "14,025.00"],
        ["Amazon.com Inc", "US0231351067", "30", "125.75", "3,772.50"],
        ["Tesla Inc", "US88160R1014", "75", "225.30", "16,897.50"],
    ]
    
    # Set column widths
    col_widths = [60, 40, 30, 30, 40]
    
    # Add table
    for row in securities:
        for i, item in enumerate(row):
            pdf.cell(col_widths[i], 10, txt=item, border=1)
        pdf.ln()
    
    # Save PDF
    samples_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "samples")
    if not os.path.exists(samples_dir):
        os.makedirs(samples_dir)
        
    output_path = os.path.join(samples_dir, "sample_securities.pdf")
    pdf.output(output_path)
    print(f"Created sample PDF at: {output_path}")

if __name__ == "__main__":
    create_sample_securities_pdf()
