"""Setup script for enhanced securities processing system"""
import os
from pathlib import Path
import logging
from dotenv import load_dotenv
import yaml
from utils.processors.enhanced_securities_processor import EnhancedSecuritiesProcessor
from utils.data_storage import init_db

logger = logging.getLogger(__name__)

def setup_enhanced_system():
    """Set up the enhanced securities processing system"""
    load_dotenv()
    
    # Configure paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    templates_dir = data_dir / 'templates'
    models_dir = data_dir / 'models'
    db_dir = data_dir / 'db'
    
    # Create directories if they don't exist
    for dir_path in [templates_dir, models_dir, db_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {dir_path}")
    
    # Initialize database
    db_url = os.getenv('DATABASE_URL', f'sqlite:///{db_dir}/securities.db')
    engine = init_db(db_url)
    
    # Initialize processor with all components
    processor = EnhancedSecuritiesProcessor(
        db_connection=db_url,
        templates_dir=str(templates_dir),
        model_path=str(models_dir / 'document_classifier.pkl')
    )
    
    # Create some basic templates for common banks
    basic_templates = {
        'generic_bank': {
            'name': 'generic_bank_template',
            'institution': 'Generic Bank',
            'document_type': 'statement',
            'fields': [
                {
                    'name': 'security_name',
                    'field_type': 'string',
                    'required': True,
                    'patterns': [
                        r'(?:security|bond|stock|fund|etf|share)[\s:]+([A-Za-z0-9\s.,&\'-]+)',
                        r'([A-Za-z0-9\s.,&\'-]{3,50})\s+[A-Z]{2}[A-Z0-9]{10}'
                    ],
                    'validation_rules': []
                },
                {
                    'name': 'isin',
                    'field_type': 'string',
                    'required': True,
                    'patterns': [r'[A-Z]{2}[A-Z0-9]{10}'],
                    'validation_rules': []
                }
            ],
            'layout_markers': {},
            'sample_identifiers': ['statement', 'portfolio', 'securities']
        }
    }
    
    # Save basic templates
    for template_id, template_data in basic_templates.items():
        template_path = templates_dir / f"{template_id}.yaml"
        with open(template_path, 'w') as f:
            yaml.dump(template_data, f)
        logger.info(f"Created template: {template_path}")
    
    logger.info("Enhanced securities processing system setup complete")
    return processor

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_enhanced_system()