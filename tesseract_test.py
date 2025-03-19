import cv2
from PIL import Image
import pytesseract
import os

# Set the path to the Tesseract executable if needed
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load the original image
image_path = "extracted_data/images/mes 28/page_3.png"
pil_image = Image.open(image_path)

# Load pre-processed images
processed_images = {
    "original": pil_image,
    "binary": Image.open("simple_binary.png"),
    "adaptive": Image.open("simple_adaptive.png"),
    "otsu": Image.open("simple_otsu.png")
}

# Create results directory
results_dir = "ocr_results"
os.makedirs(results_dir, exist_ok=True)

# Process with different configurations
for name, img in processed_images.items():
    print(f"Processing {name} image...")
    
    # Use different OCR configurations
    text_default = pytesseract.image_to_string(img)
    text_with_digits = pytesseract.image_to_string(img, config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    
    # Output text
    with open(f"{results_dir}/{name}_default.txt", "w", encoding="utf-8") as f:
        f.write(text_default)
    
    with open(f"{results_dir}/{name}_digits.txt", "w", encoding="utf-8") as f:
        f.write(text_with_digits)
    
    # Look for ISIN-like patterns
    potential_isins = []
    for line in text_default.split('\n'):
        if len(line.strip()) >= 10:
            words = line.strip().split()
            for word in words:
                if len(word) >= 10 and any(c.isdigit() for c in word) and any(c.isupper() for c in word):
                    potential_isins.append(word)
    
    if potential_isins:
        print(f"Potential ISINs in {name} image:")
        for isin in potential_isins:
            print(f"  {isin}")
    else:
        print(f"No potential ISINs found in {name} image")

print("Processing complete. Results saved in the 'ocr_results' directory") 