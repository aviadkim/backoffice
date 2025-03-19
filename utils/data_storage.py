"""Database schema and utilities for securities data storage"""
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, Table, Column, String, Float, Integer, DateTime, MetaData
from datetime import datetime
import logging
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)

class DataStorage:
    def save_document(self, document_data: Dict[str, Any]):
        """Save document to storage"""
        pass
    
    def load_document(self, document_id: str):
        """Load document from storage"""
        pass

def init_db(db_url: str):
    """Initialize the database with required tables"""
    engine = create_engine(db_url)
    metadata = MetaData()

    # Securities table
    Table('securities', metadata,
        Column('id', Integer, primary_key=True),
        Column('isin', String(12), nullable=False, index=True),
        Column('security_name', String(100)),
        Column('quantity', Float),
        Column('price', Float),
        Column('market_value', Float),
        Column('bank', String(50)),
        Column('currency', String(3)),
        Column('created_at', DateTime, default=datetime.now),
        Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now)
    )

    # Templates table
    Table('templates', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(50), unique=True),
        Column('institution', String(50)),
        Column('document_type', String(20)),
        Column('template_data', String),  # JSON
        Column('created_at', DateTime, default=datetime.now)
    )

    # Create tables
    metadata.create_all(engine)
    return engine

def get_db_connection(db_url: str):
    """Get a database connection, creating tables if needed"""
    try:
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None
