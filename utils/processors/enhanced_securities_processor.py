import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine
import yaml

logger = logging.getLogger(__name__)

class EnhancedSecuritiesProcessor:
    """Enhanced processor for securities data with AI capabilities"""
    
    def __init__(self, db_connection: str, templates_dir: str, model_path: str):
        """Initialize the processor with database and model paths"""
        self.db_engine = create_engine(db_connection)
        self.templates_dir = templates_dir
        self.model_path = model_path
        
        # Load templates
        self.templates = self._load_templates()
        
        # Initialize Gemini
        load_dotenv()
        if os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            logger.warning("No Gemini API key found. AI features will be disabled.")
            self.model = None

    def _load_templates(self) -> Dict[str, Any]:
        """Load document processing templates"""
        templates = {}
        try:
            for file in os.listdir(self.templates_dir):
                if file.endswith('.yaml'):
                    with open(os.path.join(self.templates_dir, file)) as f:
                        template = yaml.safe_load(f)
                        templates[template['name']] = template
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
        return templates

    def process_document(self, text: str, institution: Optional[str] = None) -> List[Dict[str, Any]]:
        """Process a document using templates and AI assistance"""
        securities = []
        
        # Try template-based extraction first
        if institution and institution.lower() in self.templates:
            securities.extend(self._process_with_template(text, self.templates[institution.lower()]))
        
        # Use AI for additional extraction
        if self.model and (not securities or len(securities) < 2):
            securities.extend(self._process_with_ai(text))
        
        return securities

    def _process_with_template(self, text: str, template: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process text using a specific template"""
        securities = []
        try:
            for field in template['fields']:
                for pattern in field['patterns']:
                    # Apply regex patterns from template
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        security = {}
                        security[field['name']] = match.group(1)
                        securities.append(security)
        except Exception as e:
            logger.error(f"Template processing error: {e}")
        return securities

    def _process_with_ai(self, text: str) -> List[Dict[str, Any]]:
        """Process text using Gemini AI"""
        if not self.model:
            return []
            
        try:
            prompt = """
            Extract securities information from the following text.
            Return a JSON array of objects with these fields:
            - security_name: Name of the security
            - isin: ISIN if available
            - quantity: Number of shares/units
            - price: Price per share/unit
            - market_value: Total market value
            
            Text:
            {text}
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse JSON from response
            json_str = response.text
            securities = json.loads(json_str)
            
            return securities
            
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return []

    def save_to_db(self, securities: List[Dict[str, Any]]) -> bool:
        """Save processed securities to database"""
        try:
            df = pd.DataFrame(securities)
            df.to_sql('securities', self.db_engine, if_exists='append', index=False)
            return True
        except Exception as e:
            logger.error(f"Database error: {e}")
            return False

    def get_securities_by_isin(self, isin: str) -> List[Dict[str, Any]]:
        """Retrieve securities by ISIN"""
        try:
            query = f"SELECT * FROM securities WHERE isin = '{isin}'"
            df = pd.read_sql(query, self.db_engine)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []