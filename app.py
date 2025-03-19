import os
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
from utils.mistral_extractor import MistralExtractor
import logging
import json
from datetime import datetime
import shutil

# Configure logging
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Application configuration
app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
    UPLOAD_FOLDER='uploads',
    EXTRACTED_DATA_FOLDER='extracted_data',
    ALLOWED_EXTENSIONS={'pdf'},
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
    TEMP_FOLDER='temp',
    LOG_FOLDER='logs',
    DEBUG=os.environ.get('FLASK_ENV') == 'development'
)

# Create necessary directories
for folder in [
    app.config['UPLOAD_FOLDER'],
    app.config['EXTRACTED_DATA_FOLDER'],
    app.config['TEMP_FOLDER'],
    app.config['LOG_FOLDER']
]:
    os.makedirs(folder, exist_ok=True)

# Configure file handler for app.log
file_handler = logging.FileHandler('logs/app.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Configure console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_extracted_data(content, filename):
    """Save extracted content to a JSON file and copy original file."""
    try:
        # Create extracted_data directory if it doesn't exist
        os.makedirs(app.config['EXTRACTED_DATA_FOLDER'], exist_ok=True)
        
        # Generate timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = os.path.splitext(filename)[0]
        
        # Save content to JSON file
        json_filename = f"{base_filename}_{timestamp}_full.json"
        json_filepath = os.path.join(app.config['EXTRACTED_DATA_FOLDER'], json_filename)
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        
        logger.info(f'Saved extracted content to: {json_filepath}')
        
        # Copy original file to extracted_data directory
        original_filepath = os.path.join(app.config['TEMP_FOLDER'], filename)
        if os.path.exists(original_filepath):
            pdf_filename = f"{base_filename}_{timestamp}.pdf"
            pdf_filepath = os.path.join(app.config['EXTRACTED_DATA_FOLDER'], pdf_filename)
            shutil.copy2(original_filepath, pdf_filepath)
            logger.info(f'Saved original file to: {pdf_filepath}')
        
        return json_filepath
        
    except Exception as e:
        logger.error(f'Error saving extracted data: {str(e)}', exc_info=True)
        raise

def cleanup_temp_files():
    """Clean up temporary files older than 1 hour."""
    try:
        current_time = datetime.now()
        temp_dir = app.config['TEMP_FOLDER']
        
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            # Remove files older than 1 hour
            if (current_time - file_modified).total_seconds() > 3600:
                try:
                    os.remove(filepath)
                    logger.info(f'Cleaned up temporary file: {filepath}')
                except Exception as e:
                    logger.error(f'Error cleaning up temporary file {filepath}: {str(e)}')
        
        logger.info('Completed temporary files cleanup')
        
    except Exception as e:
        logger.error(f'Error during temporary files cleanup: {str(e)}', exc_info=True)

@app.before_request
def before_request():
    """Run before each request."""
    cleanup_temp_files()

@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    temp_filepath = None
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            logger.error('No file part in request')
            return jsonify({'error': 'לא נבחר קובץ'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            logger.error('No selected file')
            return jsonify({'error': 'לא נבחר קובץ'}), 400
        
        # Check file type
        if not allowed_file(file.filename):
            logger.error(f'Invalid file type: {file.filename}')
            return jsonify({'error': 'סוג קובץ לא חוקי. אנא העלה קובץ PDF בלבד'}), 400
        
        # Save file temporarily
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        secure_name = secure_filename(os.path.splitext(file.filename)[0])
        filename = f"{secure_name}_{timestamp}.pdf"
        temp_filepath = os.path.join(app.config['TEMP_FOLDER'], filename)
        
        try:
            file.save(temp_filepath)
            logger.info(f'File saved temporarily: {temp_filepath}')
            
            # Verify file was saved correctly
            if not os.path.exists(temp_filepath):
                logger.error(f'File was not saved properly: {temp_filepath}')
                return jsonify({'error': 'שגיאה בשמירת הקובץ: הקובץ לא נשמר'}), 500
                
            file_size = os.path.getsize(temp_filepath)
            if file_size == 0:
                logger.error(f'Saved file is empty: {temp_filepath}')
                return jsonify({'error': 'שגיאה בשמירת הקובץ: הקובץ ריק'}), 500
                
            logger.info(f'File saved successfully: {temp_filepath}, size: {file_size} bytes')
            
        except Exception as e:
            logger.error(f'Error saving file: {str(e)}', exc_info=True)
            return jsonify({'error': f'שגיאה בשמירת הקובץ: {str(e)}'}), 500
        
        # Extract content
        try:
            logger.info(f'Starting content extraction from {temp_filepath}')
            extractor = MistralExtractor()
            content = extractor.extract_all_content(temp_filepath)
            logger.info(f'Content extraction completed successfully')
        except Exception as e:
            logger.error(f'Error extracting content: {str(e)}', exc_info=True)
            # Don't delete the file on extraction error to allow for debugging
            permanent_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                shutil.copy2(temp_filepath, permanent_path)
                logger.info(f'Copied problematic file to {permanent_path} for debugging')
            except Exception as copy_error:
                logger.error(f'Failed to copy problematic file: {str(copy_error)}')
            return jsonify({'error': f'שגיאה בחילוץ התוכן מהקובץ: {str(e)}'}), 500
        
        # Check if content was extracted
        if not content.get('text') and not content.get('tables') and not content.get('images'):
            logger.warning('No content extracted from file')
            # Keep the file for debugging
            permanent_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                shutil.copy2(temp_filepath, permanent_path)
                logger.info(f'Copied problematic file to {permanent_path} for debugging')
            except Exception as copy_error:
                logger.error(f'Failed to copy problematic file: {str(copy_error)}')
            return jsonify({'error': 'לא ניתן לחלץ תוכן מהקובץ. ייתכן שהקובץ מוגן או מכיל תמונות בלבד'}), 400
        
        logger.info(f'Extracted {len(content.get("tables", []))} tables and {len(content.get("images", []))} images')
        
        # Save extracted data
        try:
            save_extracted_data(content, filename)
            logger.info(f'Extracted data saved successfully')
        except Exception as e:
            logger.error(f'Error saving extracted data: {str(e)}', exc_info=True)
            return jsonify({'error': f'שגיאה בשמירת התוצאות: {str(e)}'}), 500
        
        return jsonify(content)
        
    except Exception as e:
        logger.error(f'Error processing file: {str(e)}', exc_info=True)
        return jsonify({'error': f'שגיאה בעיבוד הקובץ: {str(e)}'}), 500
        
    finally:
        # Don't delete the temp file immediately after processing
        # Wait for the next cleanup cycle to remove it
        logger.info(f'File processing completed. Temporary file will be cleaned up later.')

@app.route('/progress')
def get_progress():
    """Get current processing progress."""
    return jsonify({
        "status": "processing",
        "progress": 50,  # This should be updated based on actual progress
        "message": "Processing file..."
    })

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file size limit exceeded error."""
    logger.error('File size limit exceeded')
    return jsonify({'error': 'הקובץ גדול מדי. הגודל המקסימלי הוא 16MB'}), 413

@app.errorhandler(500)
def internal_server_error(error):
    """Handle internal server error."""
    logger.error(f'Internal server error: {str(error)}', exc_info=True)
    return jsonify({'error': 'שגיאת שרת פנימית. אנא נסה שוב מאוחר יותר'}), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle not found error."""
    logger.error(f'Not found error: {str(error)}')
    return jsonify({'error': 'הדף לא נמצא'}), 404

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all other exceptions."""
    logger.error(f'Unhandled exception: {str(error)}', exc_info=True)
    return jsonify({'error': 'שגיאה לא צפויה. אנא נסה שוב מאוחר יותר'}), 500

if __name__ == '__main__':
    app.run(debug=True)
