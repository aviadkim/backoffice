import cv2
import easyocr
import os

# נתיב לתיקיית העיבוד
debug_dir = "extracted_data/debug"

# קריאת התמונה המקורית
original_image = cv2.imread("extracted_data/images/mes 28/page_3.png")
print(f"Original image shape: {original_image.shape}")

# קריאת גרסאות מעובדות
processed_images = {}
for filename in os.listdir(debug_dir):
    if filename.startswith("processed_"):
        filepath = os.path.join(debug_dir, filename)
        method = filename.split("_")[1]
        img = cv2.imread(filepath)
        if img is not None:
            processed_images[method] = img
            print(f"Loaded {method} image: {img.shape}")

print(f"Loaded {len(processed_images)} processed images")

# אתחול מנוע OCR
reader = easyocr.Reader(['en'])

# בדיקת OCR על התמונה המקורית
print("\nRunning OCR on original image:")
results_original = reader.readtext(original_image)
print(f"Found {len(results_original)} text segments")
print("First 5 segments:")
for i, (bbox, text, prob) in enumerate(results_original[:5]):
    print(f"{i+1}. '{text}' (confidence: {prob:.2f})")

# בדיקת OCR על כל גרסה מעובדת
for method, img in processed_images.items():
    print(f"\nRunning OCR on {method} image:")
    results = reader.readtext(img)
    print(f"Found {len(results)} text segments")
    print("First 5 segments:")
    for i, (bbox, text, prob) in enumerate(results[:5]):
        print(f"{i+1}. '{text}' (confidence: {prob:.2f})")

# חיפוש ספציפי למספרים שדומים ל-ISIN
print("\nLooking for ISIN-like patterns:")
for method, img in processed_images.items():
    results = reader.readtext(img)
    for bbox, text, prob in results:
        if len(text) >= 10 and any(c.isdigit() for c in text) and any(c.isupper() for c in text):
            print(f"[{method}] Potential ISIN: '{text}' (confidence: {prob:.2f})") 