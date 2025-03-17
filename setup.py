from setuptools import setup, find_packages

setup(
    name="pdf_processor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pdfplumber",
        "pandas",
        "opencv-python-headless",
        "numpy",
        "pytesseract",
        "fpdf",
        "tabula-py",
        "pdf2image",
    ],
    python_requires=">=3.6",
)
