import cv2
from PIL import Image
import pytesseract

# Load the image
image_path = "extracted_data/images/mes 28/page_3.png"
image = cv2.imread(image_path)

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply thresholding - try different methods
# 1. Simple binary thresholding
_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

# 2. Adaptive thresholding
adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                cv2.THRESH_BINARY, 11, 2)

# 3. Otsu's thresholding
_, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# Save the processed images
cv2.imwrite("simple_binary.png", binary)
cv2.imwrite("simple_adaptive.png", adaptive)
cv2.imwrite("simple_otsu.png", otsu)

print("Processing complete. Saved three versions of the processed image.") 