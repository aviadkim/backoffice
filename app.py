import os
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
from utils.mistral_extractor import MistralExtractor
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing."""
    logger.info("Received file upload request")
    
    if 'file' not in request.files:
        logger.error("No file part in request")
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        logger.error("No selected file")
        return jsonify({"error": "No selected file"}), 400
        
    if not allowed_file(file.filename):
        logger.error(f"Invalid file type: {file.filename}")
        return jsonify({"error": "Invalid file type"}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logger.info(f"Saving file to: {filepath}")
        file.save(filepath)
        logger.info(f"Saved uploaded file to: {filepath}")
        logger.info(f"File size: {os.path.getsize(filepath)} bytes")
        
        # Process file
        logger.info("Starting file processing")
        extractor = MistralExtractor()
        
        # Extract content
        logger.info("Extracting content from file")
        try:
            content = extractor.extract_all_content(filepath)
            logger.info("Content extraction completed")
        except Exception as e:
            logger.error(f"Error during content extraction: {str(e)}", exc_info=True)
            raise
        
        if content is None:
            logger.error("Failed to extract content from file")
            return jsonify({
                "status": "error",
                "error": "Failed to process file",
                "progress": 0
            }), 500
            
        logger.info("Successfully extracted content")
        logger.info(f"Extracted {len(content.get('tables', []))} tables")
        logger.info(f"Extracted {len(content.get('transactions', []))} transactions")
        
        # Clean up uploaded file
        os.remove(filepath)
        logger.info("Cleaned up uploaded file")
        
        return jsonify({
            "status": "success",
            "message": "File processed successfully",
            "content": content,
            "progress": 100
        })
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        # Clean up on error
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({
            "status": "error",
            "error": str(e),
            "progress": 0
        }), 500

@app.route('/progress')
def get_progress():
    """Get current processing progress."""
    return jsonify({
        "status": "processing",
        "progress": 50,  # This should be updated based on actual progress
        "message": "Processing file..."
    })

if __name__ == '__main__':
    app.run(debug=True)