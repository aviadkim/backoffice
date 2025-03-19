import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

class FinancialAnalyzer:
    """Advanced financial analysis and categorization system."""
    
    def __init__(self):
        """Initialize the financial analyzer."""
        self.categories = {
            'income': {
                'keywords': ['salary', 'deposit', 'interest', 'dividend', 'refund', 'payment received'],
                'patterns': [r'salary', r'deposit', r'interest', r'dividend', r'refund']
            },
            'housing': {
                'keywords': ['rent', 'mortgage', 'property tax', 'maintenance', 'real estate'],
                'patterns': [r'rent', r'mortgage', r'property', r'maintenance']
            },
            'food': {
                'keywords': ['restaurant', 'grocery', 'supermarket', 'cafe', 'food', 'dining'],
                'patterns': [r'restaurant', r'grocery', r'supermarket', r'cafe', r'food']
            },
            'transportation': {
                'keywords': ['gas', 'fuel', 'parking', 'transit', 'uber', 'taxi', 'public transport'],
                'patterns': [r'gas', r'fuel', r'parking', r'transit', r'uber', r'taxi']
            },
            'utilities': {
                'keywords': ['electricity', 'water', 'gas', 'internet', 'phone', 'utility'],
                'patterns': [r'utility', r'bill', r'payment']
            },
            'healthcare': {
                'keywords': ['doctor', 'pharmacy', 'medical', 'dental', 'health', 'hospital'],
                'patterns': [r'doctor', r'pharmacy', r'medical', r'dental', r'health']
            },
            'entertainment': {
                'keywords': ['movie', 'theater', 'sports', 'subscription', 'netflix', 'amazon'],
                'patterns': [r'movie', r'theater', r'sports', r'subscription']
            },
            'shopping': {
                'keywords': ['clothing', 'electronics', 'furniture', 'store', 'shop'],
                'patterns': [r'store', r'shop', r'retail']
            },
            'education': {
                'keywords': ['tuition', 'books', 'course', 'training', 'school', 'university'],
                'patterns': [r'tuition', r'course', r'school', r'university']
            },
            'insurance': {
                'keywords': ['insurance', 'health insurance', 'car insurance', 'life insurance'],
                'patterns': [r'insurance']
            },
            'investments': {
                'keywords': ['stock', 'investment', 'trading', 'broker', 'securities'],
                'patterns': [r'stock', r'investment', r'trading']
            },
            'other': {
                'keywords': [],
                'patterns': []
            }
        }
        
        # Initialize ML model for categorization
        self.ml_pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000)),
            ('clf', MultinomialNB())
        ])
        self.is_trained = False
        
    def categorize_transaction(self, transaction: Dict[str, Any]) -> str:
        """
        Categorize a transaction using both rule-based and ML approaches.
        
        Args:
            transaction: Dictionary containing transaction details
            
        Returns:
            Category name
        """
        description = transaction.get('description', '').lower()
        amount = transaction.get('amount', 0)
        
        # Rule-based categorization
        for category, rules in self.categories.items():
            # Check keywords
            if any(keyword in description for keyword in rules['keywords']):
                return category
            
            # Check patterns
            if any(pattern in description for pattern in rules['patterns']):
                return category
        
        # ML-based categorization if trained
        if self.is_trained:
            try:
                category = self.ml_pipeline.predict([description])[0]
                return category
            except Exception as e:
                logger.error(f"ML categorization failed: {str(e)}")
        
        # Default categorization based on amount
        if amount > 0:
            return 'income'
        elif amount < 0:
            return 'other'
        
        return 'unclassified'
    
    def train_categorization_model(self, training_data: List[Dict[str, Any]]):
        """
        Train the ML model for transaction categorization.
        
        Args:
            training_data: List of transactions with known categories
        """
        try:
            descriptions = [t.get('description', '') for t in training_data]
            categories = [t.get('category', 'other') for t in training_data]
            
            self.ml_pipeline.fit(descriptions, categories)
            self.is_trained = True
            logger.info("ML categorization model trained successfully")
        except Exception as e:
            logger.error(f"Failed to train ML model: {str(e)}")
    
    def analyze_spending_trends(self, transactions: List[Dict[str, Any]], 
                              period: str = 'monthly') -> Dict[str, Any]:
        """
        Analyze spending trends over time.
        
        Args:
            transactions: List of transactions
            period: Analysis period ('daily', 'weekly', 'monthly', 'yearly')
            
        Returns:
            Dictionary containing trend analysis
        """
        try:
            # Convert transactions to DataFrame
            df = pd.DataFrame(transactions)
            df['date'] = pd.to_datetime(df['date'])
            
            # Group by period
            if period == 'daily':
                grouped = df.groupby(df['date'].dt.date)
            elif period == 'weekly':
                grouped = df.groupby(df['date'].dt.isocalendar().week)
            elif period == 'monthly':
                grouped = df.groupby(df['date'].dt.to_period('M'))
            else:  # yearly
                grouped = df.groupby(df['date'].dt.year)
            
            # Calculate metrics
            analysis = {
                'total_spending': grouped['amount'].sum().to_dict(),
                'average_transaction': grouped['amount'].mean().to_dict(),
                'transaction_count': grouped.size().to_dict(),
                'category_breakdown': {}
            }
            
            # Category breakdown
            for category in self.categories.keys():
                category_transactions = df[df['category'] == category]
                if not category_transactions.empty:
                    analysis['category_breakdown'][category] = {
                        'total': category_transactions['amount'].sum(),
                        'average': category_transactions['amount'].mean(),
                        'count': len(category_transactions)
                    }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing spending trends: {str(e)}")
            return {}
    
    def check_budget_limits(self, transactions: List[Dict[str, Any]], 
                          budget_limits: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Check if spending exceeds budget limits.
        
        Args:
            transactions: List of transactions
            budget_limits: Dictionary of category budget limits
            
        Returns:
            List of budget alerts
        """
        alerts = []
        
        try:
            # Calculate spending by category
            spending_by_category = {}
            for transaction in transactions:
                category = transaction.get('category', 'other')
                amount = abs(transaction.get('amount', 0))
                spending_by_category[category] = spending_by_category.get(category, 0) + amount
            
            # Check against limits
            for category, limit in budget_limits.items():
                spent = spending_by_category.get(category, 0)
                if spent > limit:
                    alerts.append({
                        'category': category,
                        'spent': spent,
                        'limit': limit,
                        'excess': spent - limit,
                        'severity': 'high' if (spent - limit) / limit > 0.2 else 'medium'
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking budget limits: {str(e)}")
            return []
    
    def generate_financial_summary(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive financial summary.
        
        Args:
            transactions: List of transactions
            
        Returns:
            Dictionary containing financial summary
        """
        try:
            df = pd.DataFrame(transactions)
            
            summary = {
                'total_income': df[df['amount'] > 0]['amount'].sum(),
                'total_expenses': abs(df[df['amount'] < 0]['amount'].sum()),
                'net_income': df['amount'].sum(),
                'transaction_count': len(transactions),
                'average_transaction': df['amount'].mean(),
                'largest_expense': abs(df[df['amount'] < 0]['amount'].min()),
                'largest_income': df[df['amount'] > 0]['amount'].max(),
                'category_summary': {}
            }
            
            # Category summary
            for category in self.categories.keys():
                category_transactions = df[df['category'] == category]
                if not category_transactions.empty:
                    summary['category_summary'][category] = {
                        'total': category_transactions['amount'].sum(),
                        'count': len(category_transactions),
                        'average': category_transactions['amount'].mean()
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating financial summary: {str(e)}")
            return {} 