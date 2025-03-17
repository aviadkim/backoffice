from typing import Dict, Any
import json

class DataStorage:
    def save_document(self, document_data: Dict[str, Any]):
        """Save document to storage"""
        pass
    
    def load_document(self, document_id: str):
        """Load document from storage"""
        pass
