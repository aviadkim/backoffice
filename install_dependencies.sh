#!/bin/bash

# Update package lists
sudo apt-get update

# Install system dependencies
sudo apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-heb \
    poppler-utils \
    default-jre  # Required for tabula-py

# Install Python dependencies
pip install -e .

# Verify installations
python -c "import cv2; print('OpenCV version:', cv2.__version__)"
python -c "import tabula; print('Tabula-py installed successfully')"
