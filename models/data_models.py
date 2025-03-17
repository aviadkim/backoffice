from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class Document:
    id: str
    title: str
    content: str
    created_at: datetime
    processed: bool
    tags: List[str]
    
@dataclass
class AnalysisResult:
    document_id: str
    score: float
    summary: str
    created_at: datetime
