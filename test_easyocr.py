from utils.easyocr_extractor import EasyOCRExtractor

def main():
    print("Initializing EasyOCR extractor...")
    extractor = EasyOCRExtractor()
    
    print("Testing image extraction on corner.png...")
    results = extractor.test_image_file('uploads/corner.png')
    
    print(f"Extracted {results['text_length']} characters of text")
    print(f"Sample text: {results['text']}")
    
    if 'output_file' in results and results['output_file']:
        print(f"Saved results to: {results['output_file']}")

if __name__ == "__main__":
    main() 