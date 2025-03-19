import os
import logging
import easyocr
import cv2
import numpy as np
from datetime import datetime
import fitz  # PyMuPDF
import re
import json
import tempfile
from PIL import Image

class PDFToImagesExtractor:
    def __init__(self, langs=['en']):
        """
        Initialize the PDF to Images Extractor with specified languages.
        
        Args:
            langs (list): List of languages to use for OCR (default: ['en'])
        """
        self.logger = self._setup_logger()
        self.logger.info("Initializing PDF to Images Extractor")
        self.reader = easyocr.Reader(langs)
        self.langs = langs
        
    def _setup_logger(self):
        """Set up and return a logger."""
        logger = logging.getLogger('pdf_to_images_extractor')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Create file handler
        file_handler = logging.FileHandler('logs/pdf_to_images_extractor.log')
        file_handler.setLevel(logging.INFO)
        
        # Create formatter and add it to handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        
        return logger
    
    def convert_pdf_to_images(self, pdf_path, zoom=2.0, output_dir=None, save_images=False):
        """
        Convert PDF file to a list of images.
        
        Args:
            pdf_path (str): Path to the PDF file
            zoom (float): Zoom factor for rendering (higher for better quality)
            output_dir (str): Directory to save images (if save_images is True)
            save_images (bool): Whether to save the converted images to disk
            
        Returns:
            list: List of images as numpy arrays
        """
        try:
            self.logger.info(f"Converting PDF to images: {pdf_path}")
            
            # Create output directory if save_images is True
            if save_images and output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Open the PDF file
            pdf_document = fitz.open(pdf_path)
            self.logger.info(f"PDF has {len(pdf_document)} pages")
            
            images = []
            for page_num in range(len(pdf_document)):
                self.logger.info(f"Converting page {page_num + 1}/{len(pdf_document)} to image")
                page = pdf_document[page_num]
                
                # Set the resolution matrix (zoom factor)
                mat = fitz.Matrix(zoom, zoom)
                
                # Get the pixmap (image) of the page
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Convert pixmap to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Convert PIL Image to numpy array for OpenCV processing
                np_img = np.array(img)
                
                # Save image if requested
                if save_images and output_dir:
                    image_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
                    cv2.imwrite(image_path, cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR))
                    self.logger.info(f"Saved page image to {image_path}")
                
                images.append(np_img)
                
            pdf_document.close()
            self.logger.info(f"Converted PDF to {len(images)} images")
            
            return images
            
        except Exception as e:
            self.logger.error(f"Error converting PDF to images: {str(e)}")
            return []
    
    def preprocess_image(self, image):
        """
        Preprocess the image to improve OCR accuracy.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Preprocessed image
        """
        try:
            self.logger.info("Preprocessing image")
            
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Increase contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Apply different preprocessing techniques and keep the best one for OCR
            
            # Method 1: Adaptive thresholding
            thresh_adaptive = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Method 2: Otsu's thresholding after Gaussian blur
            blur = cv2.GaussianBlur(enhanced, (5, 5), 0)
            _, thresh_otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Method 3: Simple binary thresholding
            _, thresh_binary = cv2.threshold(enhanced, 127, 255, cv2.THRESH_BINARY)
            
            # Apply noise reduction to all methods
            denoised_adaptive = cv2.fastNlMeansDenoising(thresh_adaptive, None, 10, 7, 21)
            denoised_otsu = cv2.fastNlMeansDenoising(thresh_otsu, None, 10, 7, 21)
            denoised_binary = cv2.fastNlMeansDenoising(thresh_binary, None, 10, 7, 21)
            
            # Save all preprocessing versions for debugging and comparison
            debug_dir = os.path.join("extracted_data", "debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            cv2.imwrite(os.path.join(debug_dir, f"original_{timestamp}.png"), gray)
            cv2.imwrite(os.path.join(debug_dir, f"enhanced_{timestamp}.png"), enhanced)
            cv2.imwrite(os.path.join(debug_dir, f"adaptive_{timestamp}.png"), denoised_adaptive)
            cv2.imwrite(os.path.join(debug_dir, f"otsu_{timestamp}.png"), denoised_otsu)
            cv2.imwrite(os.path.join(debug_dir, f"binary_{timestamp}.png"), denoised_binary)
            
            # Return the adaptive thresholding version as default
            return denoised_adaptive
            
        except Exception as e:
            self.logger.error(f"Error preprocessing image: {str(e)}")
            return image  # Return original image if preprocessing fails
    
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
                processed_image = self.preprocess_image(image)
            else:
                processed_image = image
            
            # Extract text
            self.logger.info("Performing OCR with EasyOCR")
            results = self.reader.readtext(processed_image)
            
            # Combine results
            text = ""
            for (bbox, text_result, prob) in results:
                text += text_result + " "
            
            self.logger.info(f"Extracted {len(results)} text segments")
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting text from image: {str(e)}")
            return ""
    
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
        
        # Find all ISIN matches
        isin_matches = re.findall(isin_pattern, text)
        
        # Regular expressions for additional information
        # Look for patterns like "USD 50,000" or similar
        amount_pattern = r'\b(USD|EUR|GBP|CHF|JPY|CAD)\s*[0-9,.]+\b'
        
        # Look for percentage patterns like "5.65%" or "5,65%"
        percentage_pattern = r'\b\d+[.,]\d+\s*%\b'
        
        # Look for date patterns
        date_pattern = r'\b\d{2}[./-]\d{2}[./-]\d{2,4}\b'
        
        # Extract amounts, percentages, and dates
        amounts = re.findall(amount_pattern, text)
        percentages = re.findall(percentage_pattern, text)
        dates = re.findall(date_pattern, text)
        
        # Create securities from the ISIN matches
        for isin in isin_matches:
            # Look for security name near the ISIN
            context_start = max(0, text.find(isin) - 100)
            context_end = min(len(text), text.find(isin) + 100)
            context = text[context_start:context_end]
            
            # Try to identify security name from context (simplified approach)
            name = "Unknown Security"
            if "CITIGROUP" in context or "CITI" in context:
                name = "CITIGROUP"
            elif "GOLDMAN" in context:
                name = "GOLDMAN SACHS"
            elif "JPMORGAN" in context or "JP MORGAN" in context:
                name = "JP MORGAN"
            elif "BOFA" in context or "BANK OF AMERICA" in context:
                name = "BANK OF AMERICA"
            
            # Extract other relevant information
            security = {
                "isin": isin,
                "name": name,
                "context": context,  # Keep context for manual review
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
        
        # Add summary of other extracted information
        summary = {
            "amounts": amounts[:10] if len(amounts) > 10 else amounts,
            "percentages": percentages[:10] if len(percentages) > 10 else percentages,
            "dates": dates[:10] if len(dates) > 10 else dates
        }
        
        return unique_securities, summary
    
    def extract_text_from_pdf(self, pdf_path, preprocess=True, save_images=False, save_intermediate=False):
        """
        Extract text from all pages in a PDF file.
        
        Args:
            pdf_path (str): Path to the PDF file
            preprocess (bool): Whether to preprocess the images
            save_images (bool): Whether to save the intermediate images
            save_intermediate (bool): Whether to save intermediate results after each page
            
        Returns:
            dict: Dictionary containing extraction results with text by page
        """
        try:
            self.logger.info(f"Extracting text from PDF: {pdf_path}")
            
            # Create a temporary directory for images if needed
            if save_images:
                output_dir = os.path.join("extracted_data", "images", os.path.basename(pdf_path).split(".")[0])
            else:
                output_dir = None
            
            # Convert PDF to images
            images = self.convert_pdf_to_images(pdf_path, save_images=save_images, output_dir=output_dir)
            if not images:
                return {"error": "Failed to convert PDF to images"}
            
            # Extract text from each image
            all_text = ""
            page_texts = []
            
            # Base filename for intermediate files
            if save_intermediate:
                base_name = os.path.splitext(os.path.basename(pdf_path))[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                intermediate_dir = os.path.join("extracted_data", "intermediate", f"{base_name}_{timestamp}")
                os.makedirs(intermediate_dir, exist_ok=True)
                self.logger.info(f"Saving intermediate results to {intermediate_dir}")
            
            for i, image in enumerate(images):
                self.logger.info(f"Processing page {i+1}/{len(images)}")
                page_text = self.extract_text_from_image(image, preprocess)
                page_texts.append(page_text)
                all_text += page_text + "\n\n"
                
                # Save intermediate result for this page if requested
                if save_intermediate:
                    page_num = i + 1
                    page_file = os.path.join(intermediate_dir, f"page_{page_num}.txt")
                    with open(page_file, 'w', encoding='utf-8') as f:
                        f.write(page_text)
                    self.logger.info(f"Saved intermediate text for page {page_num} to {page_file}")
                
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
            
            # Save securities separately if they exist
            securities_path = None
            if 'securities' in extraction_results and extraction_results['securities']:
                securities_path = f"extracted_data/{base_filename}_securities.json"
                with open(securities_path, 'w', encoding='utf-8') as f:
                    json.dump(extraction_results['securities'], f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved extracted content to {json_path} and {text_path}")
            
            saved_paths = {
                "json_path": json_path,
                "text_path": text_path
            }
            
            if securities_path:
                saved_paths["securities_path"] = securities_path
                
            return saved_paths
            
        except Exception as e:
            self.logger.error(f"Error saving extracted content: {str(e)}")
            return {"error": str(e)}
    
    def test_pdf_file(self, pdf_path, save_results=True, save_images=False, save_intermediate=False):
        """
        Test extraction on a specific PDF file and optionally save the results.
        
        Args:
            pdf_path (str): Path to the PDF file
            save_results (bool): Whether to save the extracted content
            save_images (bool): Whether to save the intermediate images
            save_intermediate (bool): Whether to save intermediate results after each page
            
        Returns:
            dict: Dictionary containing extraction results
        """
        try:
            self.logger.info(f"Testing extraction on PDF file: {pdf_path}")
            
            # Extract text from PDF
            extraction_results = self.extract_text_from_pdf(
                pdf_path, save_images=save_images, save_intermediate=save_intermediate
            )
            
            if "error" in extraction_results:
                return extraction_results
            
            # Extract securities and other financial info
            all_text = extraction_results.get("all_text", "")
            securities, summary = self.extract_securities(all_text)
            extraction_results["securities"] = securities
            extraction_results["summary"] = summary
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
                "financial_summary": summary,
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
    extractor = PDFToImagesExtractor()
    results = extractor.test_pdf_file("uploads/sample.pdf", save_images=True)
    print(f"Extracted text from {results['total_pages']} pages")
    print(f"Found {results['total_securities']} securities")
    for i, security in enumerate(results.get('sample_securities', [])[:5]):
        print(f"  {i+1}. ISIN: {security['isin']}, Name: {security['name']}")
    print(f"Text preview: {results.get('text_preview', '')[:100]}...") 