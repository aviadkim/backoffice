import os
import logging
import easyocr
import cv2
import numpy as np
from datetime import datetime
import fitz  # PyMuPDF
import io
import json
import re
from PIL import Image

class MuPDFEasyOCRExtractor:
    def __init__(self, langs=['en']):
        """
        Initialize the PDF EasyOCR extractor with specified languages.
        
        Args:
            langs (list): List of languages to use for OCR (default: ['en'])
        """
        self.logger = self._setup_logger()
        self.logger.info("Initializing MuPDF EasyOCR extractor")
        self.reader = easyocr.Reader(langs)
        self.langs = langs
        
    def _setup_logger(self):
        """Set up and return a logger."""
        logger = logging.getLogger('mupdf_easyocr_extractor')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Create file handler
        file_handler = logging.FileHandler('logs/mupdf_easyocr_extractor.log')
        file_handler.setLevel(logging.INFO)
        
        # Create formatter and add it to handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        
        return logger
    
    def preprocess_image(self, image):
        """
        Preprocess the image to improve OCR accuracy.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Preprocessed image
        """
        self.logger.info("Preprocessing image")
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Apply thresholding to handle shadows and normalize text
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Apply noise reduction
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        return denoised
    
    def convert_pdf_to_images(self, pdf_path, zoom=1.5):
        """
        Convert PDF file to a list of images using PyMuPDF.
        
        Args:
            pdf_path (str): Path to the PDF file
            zoom (float): Zoom factor for rendering (higher for better quality)
            
        Returns:
            list: List of images as numpy arrays
        """
        try:
            self.logger.info(f"Converting PDF to images using PyMuPDF: {pdf_path}")
            
            # Open the PDF file
            pdf_document = fitz.open(pdf_path)
            self.logger.info(f"PDF has {len(pdf_document)} pages")
            
            np_images = []
            for page_num in range(len(pdf_document)):
                self.logger.info(f"Converting page {page_num + 1} to image")
                page = pdf_document[page_num]
                
                # Set the resolution matrix (zoom factor)
                mat = fitz.Matrix(zoom, zoom)
                
                # Get the pixmap (image) of the page
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Convert pixmap to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Convert PIL Image to numpy array
                np_img = np.array(img)
                np_images.append(np_img)
                
            pdf_document.close()
            self.logger.info(f"Converted PDF to {len(np_images)} images")
            
            return np_images
            
        except Exception as e:
            self.logger.error(f"Error converting PDF to images: {str(e)}")
            return []
    
    def extract_text_from_image(self, image, preprocess=True):
        """
        Extract text from an image using EasyOCR.
        
        Args:
            image: Image as numpy array
            preprocess (bool): Whether to preprocess the image
            
        Returns:
            str: Extracted text
        """
        try:
            # Preprocess the image if requested
            if preprocess:
                image = self.preprocess_image(image)
            
            # Extract text
            self.logger.info("Performing OCR with EasyOCR")
            results = self.reader.readtext(image)
            
            # Combine results
            text = ""
            for (bbox, text_result, prob) in results:
                text += text_result + " "
            
            self.logger.info(f"Extracted {len(results)} text segments")
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting text from image: {str(e)}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path, preprocess=True):
        """
        Extract text from all pages in a PDF file.
        
        Args:
            pdf_path (str): Path to the PDF file
            preprocess (bool): Whether to preprocess the images
            
        Returns:
            dict: Dictionary containing extraction results with text by page
        """
        try:
            self.logger.info(f"Extracting text from PDF: {pdf_path}")
            
            # Convert PDF to images
            images = self.convert_pdf_to_images(pdf_path)
            if not images:
                return {"error": "Failed to convert PDF to images"}
            
            # Extract text from each image
            all_text = ""
            page_texts = []
            
            for i, image in enumerate(images):
                self.logger.info(f"Processing page {i+1}/{len(images)}")
                page_text = self.extract_text_from_image(image, preprocess)
                page_texts.append(page_text)
                all_text += page_text + "\n\n"
                
            # Return results
            results = {
                "pdf_path": pdf_path,
                "total_pages": len(images),
                "total_text_length": len(all_text),
                "page_texts": page_texts,
                "all_text": all_text
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {str(e)}")
            return {"error": str(e)}
    
    def extract_securities(self, text):
        """
        Extract securities information from the text.
        
        Args:
            text (str): The extracted text to parse
            
        Returns:
            list: List of securities found
        """
        securities = []
        
        # ISIN pattern (12 alphanumeric characters)
        isin_pattern = r'\b[A-Z0-9]{12}\b'
        
        # Find all matches
        isin_matches = re.findall(isin_pattern, text)
        
        # Create securities from the matches
        for isin in isin_matches:
            security = {
                "isin": isin,
                "name": "Unknown Security",
                "value": None
            }
            securities.append(security)
        
        # Remove duplicates (based on ISIN)
        unique_securities = []
        seen_isins = set()
        
        for security in securities:
            if security["isin"] not in seen_isins:
                unique_securities.append(security)
                seen_isins.add(security["isin"])
        
        return unique_securities
    
    def save_extracted_content(self, extraction_results, base_filename=None):
        """
        Save the extracted content to files.
        
        Args:
            extraction_results (dict): Results from the extraction
            base_filename (str, optional): Base filename to use. If None, one will be generated.
            
        Returns:
            dict: Dictionary with paths to saved files
        """
        try:
            if not base_filename:
                # Extract filename from path
                if 'pdf_path' in extraction_results:
                    pdf_name = os.path.basename(extraction_results['pdf_path'])
                    base_name = os.path.splitext(pdf_name)[0]
                else:
                    base_name = "pdf_extraction"
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_filename = f"{base_name}_{timestamp}"
            
            # Create the directories if they don't exist
            if not os.path.exists('extracted_data'):
                os.makedirs('extracted_data')
            
            # Save the full JSON data
            json_path = f"extracted_data/{base_filename}_full.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                # Create a copy with a truncated text for better readability
                json_data = extraction_results.copy()
                if 'all_text' in json_data:
                    json_data['all_text_preview'] = json_data['all_text'][:1000] + "..." if len(json_data['all_text']) > 1000 else json_data['all_text']
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            # Save the text separately
            text_path = f"extracted_data/{base_filename}_text.txt"
            if 'all_text' in extraction_results:
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(extraction_results['all_text'])
            
            self.logger.info(f"Saved extracted content to {json_path} and {text_path}")
            
            return {
                "json_path": json_path,
                "text_path": text_path
            }
            
        except Exception as e:
            self.logger.error(f"Error saving extracted content: {str(e)}")
            return {"error": str(e)}
    
    def test_pdf_file(self, pdf_path, save_results=True):
        """
        Test extraction on a specific PDF file and optionally save the results.
        
        Args:
            pdf_path (str): Path to the PDF file
            save_results (bool): Whether to save the extracted content
            
        Returns:
            dict: Dictionary containing extraction results
        """
        try:
            self.logger.info(f"Testing extraction on PDF file: {pdf_path}")
            
            # Extract text from PDF
            extraction_results = self.extract_text_from_pdf(pdf_path)
            
            if "error" in extraction_results:
                return extraction_results
            
            # Extract securities
            all_text = extraction_results.get("all_text", "")
            securities = self.extract_securities(all_text)
            extraction_results["securities"] = securities
            extraction_results["total_securities"] = len(securities)
            
            # Save results if requested
            if save_results:
                saved_paths = self.save_extracted_content(extraction_results)
                extraction_results.update(saved_paths)
            
            # Generate a summary
            summary = {
                "pdf_path": pdf_path,
                "total_pages": extraction_results.get("total_pages", 0),
                "total_text_length": extraction_results.get("total_text_length", 0),
                "total_securities": len(securities),
                "sample_securities": securities[:5],
                "text_preview": all_text[:500] + "..." if len(all_text) > 500 else all_text
            }
            
            if save_results:
                summary.update({
                    "json_path": extraction_results.get("json_path"),
                    "text_path": extraction_results.get("text_path")
                })
            
            self.logger.info(f"Extraction test completed. Found {len(securities)} securities.")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error testing PDF file: {str(e)}")
            return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    extractor = MuPDFEasyOCRExtractor()
    results = extractor.test_pdf_file("uploads/sample.pdf")
    print(f"Extracted text from {results['total_pages']} pages")
    print(f"Found {results['total_securities']} securities")
    for i, security in enumerate(results.get('sample_securities', [])[:5]):
        print(f"  {i+1}. ISIN: {security['isin']}, Name: {security['name']}")
    print(f"Text preview: {results.get('text_preview', '')[:100]}...") 