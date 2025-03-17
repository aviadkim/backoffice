import unittest
from unittest.mock import patch, Mock
import pandas as pd
import numpy as np
import tempfile
import os
import io
import json
import logging
from utils.securities_analyzer import SecuritiesAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestSecuritiesAnalyzer(unittest.TestCase):
    """Test the enhanced securities analyzer."""
    
    def setUp(self):
        """Set up the test environment."""
        self.analyzer = SecuritiesAnalyzer()
        
        # Create sample securities data
        self.sample_securities = [
            {
                'isin': 'US0378331005',
                'security_name': 'Apple Inc.',
                'quantity': 100,
                'price': 150.25,
                'market_value': 15025.00,
                'bank': 'Morgan Stanley'
            },
            {
                'isin': 'US0378331005',
                'security_name': 'Apple Inc.',
                'quantity': 50,
                'price': 152.50,
                'market_value': 7625.00,
                'bank': 'Schwab'
            },
            {
                'isin': 'US5949181045',
                'security_name': 'Microsoft Corp',
                'quantity': 75,
                'price': 280.50,
                'market_value': 21037.50,
                'bank': 'Morgan Stanley'
            },
            {
                'isin': 'US88160R1014',
                'security_name': 'Tesla Inc',
                'quantity': 30,
                'price': 225.30,
                'market_value': 6759.00,
                'bank': 'Schwab'
            }
        ]
        
        # Create sample historical data (3 periods)
        self.sample_historical = []
        
        # Period 1 (Jan 2023)
        self.sample_historical.extend([
            {
                'date': '2023-01-31',
                'isin': 'US0378331005',
                'security_name': 'Apple Inc.',
                'quantity': 100,
                'price': 145.00,
                'market_value': 14500.00,
                'bank': 'Morgan Stanley'
            },
            {
                'date': '2023-01-31',
                'isin': 'US5949181045',
                'security_name': 'Microsoft Corp',
                'quantity': 75,
                'price': 250.00,
                'market_value': 18750.00,
                'bank': 'Morgan Stanley'
            }
        ])
        
        # Period 2 (Feb 2023)
        self.sample_historical.extend([
            {
                'date': '2023-02-28',
                'isin': 'US0378331005',
                'security_name': 'Apple Inc.',
                'quantity': 120,  # Added 20 shares
                'price': 148.00,
                'market_value': 17760.00,
                'bank': 'Morgan Stanley'
            },
            {
                'date': '2023-02-28',
                'isin': 'US5949181045',
                'security_name': 'Microsoft Corp',
                'quantity': 75,
                'price': 255.00,
                'market_value': 19125.00,
                'bank': 'Morgan Stanley'
            },
            {
                'date': '2023-02-28',
                'isin': 'US88160R1014',
                'security_name': 'Tesla Inc',
                'quantity': 30,
                'price': 200.00,
                'market_value': 6000.00,
                'bank': 'Schwab'
            }
        ])
        
        # Period 3 (Mar 2023)
        self.sample_historical.extend([
            {
                'date': '2023-03-31',
                'isin': 'US0378331005',
                'security_name': 'Apple Inc.',
                'quantity': 150,  # Added 30 more
                'price': 152.50,
                'market_value': 22875.00,
                'bank': 'Morgan Stanley'
            },
            {
                'date': '2023-03-31',
                'isin': 'US0378331005',
                'security_name': 'Apple Inc.',
                'quantity': 50,
                'price': 152.50,
                'market_value': 7625.00,
                'bank': 'Schwab'
            },
            {
                'date': '2023-03-31',
                'isin': 'US5949181045',
                'security_name': 'Microsoft Corp',
                'quantity': 75,
                'price': 280.50,
                'market_value': 21037.50,
                'bank': 'Morgan Stanley'
            },
            {
                'date': '2023-03-31',
                'isin': 'US88160R1014',
                'security_name': 'Tesla Inc',
                'quantity': 30,
                'price': 225.30,
                'market_value': 6759.00,
                'bank': 'Schwab'
            }
        ])
    
    def test_analyze_securities_by_isin(self):
        """Test analyzing securities by ISIN."""
        analysis = self.analyzer.analyze_securities_by_isin(self.sample_securities)
        
        # Verify analysis structure and content
        self.assertEqual(analysis['status'], 'success')
        self.assertIn('summary', analysis)
        self.assertIn('securities', analysis)
        
        # Check summary
        summary = analysis['summary']
        self.assertEqual(summary['total_securities'], 3)
        self.assertGreater(summary['total_portfolio_value'], 0)
        
        # Check for Apple data
        securities = analysis['securities']
        apple_isin = 'US0378331005'
        
        self.assertIn(apple_isin, securities)
        apple_data = securities[apple_isin]
        
        self.assertEqual(apple_data['security_name'], 'Apple Inc.')
        self.assertEqual(apple_data['total_quantity'], 150)
        self.assertEqual(apple_data['total_market_value'], 22650.00)
        
        # Check price discrepancies (Apple has a price difference)
        self.assertTrue(len(summary['price_discrepancies']) > 0)
        
        # Check source-specific data
        self.assertIn('Morgan Stanley', apple_data['holdings_by_source'])
        self.assertIn('Schwab', apple_data['holdings_by_source'])
    
    def test_analyze_performance_over_time(self):
        """Test analyzing performance over time."""
        performance = self.analyzer.analyze_performance_over_time(self.sample_historical, 'monthly')
        
        # Verify performance structure
        self.assertEqual(performance['status'], 'success')
        self.assertIn('overall_performance', performance)
        self.assertIn('performance_by_period', performance)
        self.assertIn('best_performing_securities', performance)
        self.assertIn('securities_performance', performance)
        
        # Check overall performance
        overall = performance['overall_performance']
        self.assertGreater(overall['last_period'], overall['first_period'])
        
        # Check periods
        periods = performance['performance_by_period']
        self.assertEqual(len(periods), 3)  # 3 months
        
        # Check securities performance
        securities_perf = performance['securities_performance']
        self.assertIn('US0378331005', securities_perf)  # Apple
        self.assertIn('US5949181045', securities_perf)  # Microsoft
        
        # Check Apple's performance - should have increased
        apple_perf = securities_perf['US0378331005']['performance_by_period']
        first_price = apple_perf[0]['price']
        last_price = apple_perf[-1]['price']
        self.assertGreater(last_price, first_price)
    
    def test_generate_consolidated_report(self):
        """Test report generation."""
        # First get the analysis results
        securities_analysis = self.analyzer.analyze_securities_by_isin(self.sample_securities)
        performance_analysis = self.analyzer.analyze_performance_over_time(self.sample_historical, 'monthly')
        
        # Generate report
        report = self.analyzer.generate_consolidated_report(securities_analysis, performance_analysis)
        
        # Check report content
        self.assertIn("# Securities Portfolio Analysis Report", report)
        self.assertIn("## Portfolio Summary", report)
        self.assertIn("## Top Holdings", report)
        self.assertIn("## Performance Analysis", report)
        
        # Check for specific securities
        self.assertIn("Apple Inc.", report)
        self.assertIn("Microsoft Corp", report)
        self.assertIn("Tesla Inc", report)
        
        # Verify the report includes performance data
        self.assertIn("Performance by Period", report)
        self.assertIn("Best Performing Securities", report)
        
        # Save report to file for inspection
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(report)
            report_path = f.name
        
        logger.info(f"Sample report saved to {report_path}")
    
    def test_price_discrepancies(self):
        """Test price discrepancy detection."""
        # Create data with significant price differences
        securities_with_discrepancies = [
            {
                'isin': 'US0378331005',
                'security_name': 'Apple Inc.',
                'quantity': 100,
                'price': 150.00,
                'market_value': 15000.00,
                'bank': 'Bank A'
            },
            {
                'isin': 'US0378331005',
                'security_name': 'Apple Inc.',
                'quantity': 50,
                'price': 170.00,  # 13.3% higher price
                'market_value': 8500.00,
                'bank': 'Bank B'
            }
        ]
        
        # Set a lower tolerance to ensure detection
        self.analyzer.price_tolerance = 0.05  # 5%
        
        analysis = self.analyzer.analyze_securities_by_isin(securities_with_discrepancies)
        
        # Verify discrepancy is detected
        discrepancies = analysis['summary']['price_discrepancies']
        self.assertEqual(len(discrepancies), 1)
        
        discrepancy = discrepancies[0]
        self.assertEqual(discrepancy['isin'], 'US0378331005')
        self.assertEqual(discrepancy['min_price'], 150.00)
        self.assertEqual(discrepancy['max_price'], 170.00)
        self.assertGreater(discrepancy['difference_percent'], 10)  # Should be around 13.3%
        
        # Now try with price difference within tolerance
        securities_without_discrepancies = [
            {
                'isin': 'US0378331005',
                'security_name': 'Apple Inc.',
                'quantity': 100,
                'price': 150.00,
                'market_value': 15000.00,
                'bank': 'Bank A'
            },
            {
                'isin': 'US0378331005',
                'security_name': 'Apple Inc.',
                'quantity': 50,
                'price': 153.00,  # Only 2% higher
                'market_value': 7650.00,
                'bank': 'Bank B'
            }
        ]
        
        analysis = self.analyzer.analyze_securities_by_isin(securities_without_discrepancies)
        
        # Verify no discrepancy is detected
        discrepancies = analysis['summary']['price_discrepancies']
        self.assertEqual(len(discrepancies), 0)

if __name__ == "__main__":
    unittest.main()