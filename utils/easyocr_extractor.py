import os
import logging
import easyocr
import cv2
import numpy as np
from datetime import datetime

class EasyOCRExtractor:
    def __init__(self, langs=['en']):
        """
        Initialize the EasyOCR extractor with specified languages.
        
        Args:
            langs (list): List of languages to use for OCR (default: ['en'])
        """
        self.logger = self._setup_logger()
        self.logger.info("Initializing EasyOCR extractor")
        self.reader = easyocr.Reader(langs)
        self.langs = langs
        
    def _setup_logger(self):
        """Set up and return a logger."""
        logger = logging.getLogger('easyocr_extractor')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Create file handler
        file_handler = logging.FileHandler('logs/easyocr_extractor.log')
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
    
    def extract_text_from_image(self, image_path, preprocess=True):
        """
        Extract text from an image using EasyOCR.
        
        Args:
            image_path (str): Path to the image file
            preprocess (bool): Whether to preprocess the image
            
        Returns:
            str: Extracted text
        """
        try:
            self.logger.info(f"Extracting text from image: {image_path}")
            
            # Read the image
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error(f"Failed to read image: {image_path}")
                return ""
            
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
            self.logger.debug(f"Extracted text: {text}")
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting text from image: {str(e)}")
            return ""
    
    def save_extracted_text(self, text, output_file=None):
        """
        Save extracted text to a file.
        
        Args:
            text (str): Extracted text to save
            output_file (str, optional): Path to save the text to. If None, a default path will be generated.
            
        Returns:
            str: Path where the text was saved
        """
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"extracted_data/easyocr_{timestamp}.txt"
            
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Write the text to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
                
            self.logger.info(f"Saved extracted text to {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error saving extracted text: {str(e)}")
            return None
    
    def test_image_file(self, image_path, save_results=True):
        """
        Test extraction on a specific image file and optionally save the results.
        
        Args:
            image_path (str): Path to the image file
            save_results (bool): Whether to save the extracted text
            
        Returns:
            dict: Dictionary containing extraction results
        """
        try:
            self.logger.info(f"Testing extraction on image file: {image_path}")
            
            # Extract text
            text = self.extract_text_from_image(image_path)
            
            # Save results if requested
            if save_results and text:
                output_file = self.save_extracted_text(text)
            else:
                output_file = None
                
            # Return results
            results = {
                "image_path": image_path,
                "text_length": len(text),
                "output_file": output_file,
                "text": text[:500] + "..." if len(text) > 500 else text
            }
            
            self.logger.info(f"Extraction test completed. Text length: {len(text)}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing image file: {str(e)}")
            return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    extractor = EasyOCRExtractor()
    results = extractor.test_image_file("uploads/corner.png")
    print(f"Extracted {results['text_length']} characters of text")
    print(f"Sample text: {results['text']}") 