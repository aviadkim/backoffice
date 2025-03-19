from utils.pdf_to_images_extractor import PDFToImagesExtractor
import sys
import os
import time

def main():
    # Default PDF file
    pdf_file = "uploads/mes 28.2.25.pdf"
    
    # Check if a PDF file was specified as a command-line argument
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        
    # Check if the file exists
    if not os.path.exists(pdf_file):
        print(f"Error: File '{pdf_file}' not found.")
        return
    
    print(f"Initializing PDF to Images Extractor...")
    extractor = PDFToImagesExtractor(langs=['en'])
    
    print(f"Testing extraction on PDF file: {pdf_file}")
    print("This may take several minutes for large PDF files...")
    print("The PDF will be converted to high-quality images and then processed with EasyOCR.")
    
    # Save the intermediate images for inspection
    save_images = True
    
    # Save intermediate results after each page
    save_intermediate = True
    
    start_time = time.time()
    results = extractor.test_pdf_file(pdf_file, save_images=save_images, save_intermediate=save_intermediate)
    elapsed_time = time.time() - start_time
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return
    
    print(f"\nExtraction Results (completed in {elapsed_time:.2f} seconds):")
    print(f"- Total pages: {results['total_pages']}")
    print(f"- Total text length: {results['total_text_length']} characters")
    print(f"- Total securities found: {results['total_securities']}")
    
    if results['total_securities'] > 0:
        print("\nSample securities:")
        for i, security in enumerate(results.get('sample_securities', [])[:5]):
            print(f"  {i+1}. ISIN: {security['isin']}, Name: {security['name']}")
    
    # Display financial summary
    if 'financial_summary' in results:
        summary = results['financial_summary']
        print("\nFinancial Summary:")
        
        if summary.get('amounts'):
            print("  Currency amounts found:", ', '.join(summary['amounts'][:5]))
            
        if summary.get('percentages'):
            print("  Percentages found:", ', '.join(summary['percentages'][:5]))
            
        if summary.get('dates'):
            print("  Dates found:", ', '.join(summary['dates'][:5]))
    
    if 'json_path' in results:
        print(f"\nFull results saved to: {results['json_path']}")
    if 'text_path' in results:
        print(f"Extracted text saved to: {results['text_path']}")
    
    if save_images:
        images_dir = os.path.join("extracted_data", "images", os.path.basename(pdf_file).split(".")[0])
        if os.path.exists(images_dir):
            print(f"Individual page images saved to: {images_dir}")
    
    print("\nText preview:")
    print(results.get('text_preview', '')[:300] + "...")

if __name__ == "__main__":
    main() 