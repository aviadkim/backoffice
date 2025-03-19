import cv2
from PIL import Image
import numpy as np
import os

# Load the image for page 4
image_path = "extracted_data/images/mes 28/page_4.png"
image = cv2.imread(image_path)

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Create output directory
output_dir = "page4_processed"
os.makedirs(output_dir, exist_ok=True)

# Apply different preprocessing techniques
# 1. Enhanced contrast with CLAHE
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(gray)
cv2.imwrite(os.path.join(output_dir, "enhanced.png"), enhanced)

# 2. Adaptive thresholding
adaptive = cv2.adaptiveThreshold(
    enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
    cv2.THRESH_BINARY, 11, 2
)
cv2.imwrite(os.path.join(output_dir, "adaptive.png"), adaptive)

# 3. Otsu's thresholding
blur = cv2.GaussianBlur(enhanced, (5, 5), 0)
_, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
cv2.imwrite(os.path.join(output_dir, "otsu.png"), otsu)

# 4. Simple binary thresholding
_, binary = cv2.threshold(enhanced, 127, 255, cv2.THRESH_BINARY)
cv2.imwrite(os.path.join(output_dir, "binary.png"), binary)

# 5. Try different kernel sizes for adaptive thresholding
for block_size in [7, 15, 21]:
    adaptive_custom = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, block_size, 2
    )
    cv2.imwrite(os.path.join(output_dir, f"adaptive_block{block_size}.png"), adaptive_custom)

# 6. Try inverting the image (sometimes helps with white text on dark background)
inverted = cv2.bitwise_not(gray)
cv2.imwrite(os.path.join(output_dir, "inverted.png"), inverted)

# 7. Dilate and erode (can help with connecting broken text)
kernel = np.ones((2, 2), np.uint8)
dilated = cv2.dilate(adaptive, kernel, iterations=1)
cv2.imwrite(os.path.join(output_dir, "dilated.png"), dilated)

eroded = cv2.erode(adaptive, kernel, iterations=1)
cv2.imwrite(os.path.join(output_dir, "eroded.png"), eroded)

print(f"Processing complete. Results saved in '{output_dir}' directory.") 