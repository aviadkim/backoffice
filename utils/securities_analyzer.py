import pandas as pd
import numpy as np
import logging
import json
from typing import Dict, List, Any, Union, Optional, Tuple
import time
from datetime import datetime, timedelta
import hashlib
import re

logger = logging.getLogger(__name__)

class SecuritiesAnalyzer:
    """
    Analyzes securities portfolios from multiple sources.
    """
    
    def __init__(self):
        self.securities_data = {}
        self.price_tolerance = 0.05  # 5% tolerance for price differences
    
    def analyze_securities_by_isin(self, securities_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze securities by ISIN across different accounts.
        
        Args:
            securities_list: List of securities data dictionaries
            
        Returns:
            Analysis results by ISIN
        """
        if not securities_list:
            return {'status': 'error', 'message': 'No securities data provided'}
        
        # Group securities by ISIN
        securities_by_isin = {}
        for security in securities_list:
            if 'isin' not in security:
                continue
                
            isin = security['isin']
            if isin not in securities_by_isin:
                securities_by_isin[isin] = []
                
            securities_by_isin[isin].append(security)
        
        # Process each ISIN group
        results = {}
        price_discrepancies = []
        
        for isin, securities in securities_by_isin.items():
            # Extract security details
            name = self._get_most_common_value(securities, 'security_name')
            
            # Aggregate quantities and values
            total_quantity = sum(float(s.get('quantity', 0)) for s in securities if s.get('quantity') is not None)
            total_market_value = sum(float(s.get('market_value', 0)) for s in securities if s.get('market_value') is not None)
            
            # Calculate weighted average price
            weighted_price = total_market_value / total_quantity if total_quantity > 0 else None
            
            # Check for price discrepancies
            prices = [float(s.get('price', 0)) for s in securities if s.get('price') is not None and float(s.get('price', 0)) > 0]
            if len(prices) > 1:
                min_price = min(prices)
                max_price = max(prices)
                
                # Check if price difference exceeds tolerance
                if min_price > 0 and (max_price - min_price) / min_price > self.price_tolerance:
                    price_discrepancies.append({
                        'isin': isin,
                        'security_name': name,
                        'min_price': min_price,
                        'max_price': max_price,
                        'difference_percent': round(((max_price - min_price) / min_price) * 100, 2),
                        'sources': [s.get('bank', 'Unknown') for s in securities]
                    })
            
            # Track holdings by bank/source
            holdings_by_source = {}
            for security in securities:
                source = security.get('bank', 'Unknown')
                quantity = float(security.get('quantity', 0))
                market_value = float(security.get('market_value', 0))
                
                if source not in holdings_by_source:
                    holdings_by_source[source] = {'quantity': 0, 'market_value': 0}
                
                holdings_by_source[source]['quantity'] += quantity
                holdings_by_source[source]['market_value'] += market_value
            
            # Store results for this ISIN
            results[isin] = {
                'isin': isin,
                'security_name': name,
                'total_quantity': total_quantity,
                'total_market_value': total_market_value,
                'weighted_average_price': weighted_price,
                'holdings_by_source': holdings_by_source,
                'price_range': {'min': min(prices), 'max': max(prices)} if prices else {}
            }
        
        # Prepare summary information
        total_securities = len(results)
        total_portfolio_value = sum(security.get('total_market_value', 0) for security in results.values())
        
        # Top holdings by value
        top_holdings = sorted(
            results.values(), 
            key=lambda x: x.get('total_market_value', 0), 
            reverse=True
        )[:10]  # Top 10
        
        summary = {
            'total_securities': total_securities,
            'total_portfolio_value': total_portfolio_value,
            'top_holdings': [
                {
                    'isin': holding['isin'],
                    'security_name': holding['security_name'],
                    'market_value': holding['total_market_value'],
                    'percent_of_portfolio': round((holding['total_market_value'] / total_portfolio_value) * 100, 2) if total_portfolio_value > 0 else 0
                }
                for holding in top_holdings
            ],
            'price_discrepancies': price_discrepancies
        }
        
        return {
            'status': 'success',
            'summary': summary,
            'securities': results
        }
    
    def analyze_performance_over_time(self, historical_data: List[Dict[str, Any]], grouping: str = 'monthly') -> Dict[str, Any]:
        """
        Analyze securities performance over time.
        
        Args:
            historical_data: List of historical securities values
            grouping: Time grouping (monthly, quarterly, yearly)
            
        Returns:
            Performance analysis results
        """
        if not historical_data:
            return {'status': 'error', 'message': 'No historical data provided'}
        
        try:
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(historical_data)
            
            # Ensure date column is datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            elif 'report_date' in df.columns:
                df['date'] = pd.to_datetime(df['report_date'])
                
            # Group by date and ISIN
            if grouping == 'monthly':
                df['period'] = df['date'].dt.strftime('%Y-%m')
            elif grouping == 'quarterly':
                df['period'] = df['date'].dt.year.astype(str) + '-Q' + (df['date'].dt.quarter).astype(str)
            elif grouping == 'yearly':
                df['period'] = df['date'].dt.year
            else:
                return {'status': 'error', 'message': f'Invalid grouping: {grouping}'}
            
            # Group by period and calculate totals
            period_summary = df.groupby('period').agg({
                'total_market_value': 'sum'
            }).reset_index()
            
            # Calculate period-over-period changes
            period_summary['prev_value'] = period_summary['total_market_value'].shift(1)
            period_summary['change'] = period_summary['total_market_value'] - period_summary['prev_value']
            period_summary['percent_change'] = (period_summary['change'] / period_summary['prev_value']) * 100
            
            # Calculate performance metrics
            performance_by_period = period_summary.to_dict('records')
            
            # Securities performance for each security
            securities_performance = {}
            for isin in df['isin'].unique():
                security_data = df[df['isin'] == isin]
                
                # Get name from latest record
                latest_record = security_data.loc[security_data['date'].idxmax()]
                security_name = latest_record.get('security_name', 'Unknown')
                
                # Group by period and calculate performance
                security_by_period = security_data.groupby('period').agg({
                    'price': 'last',
                    'quantity': 'last',
                    'market_value': 'last'
                }).reset_index()
                
                # Calculate period-over-period changes
                security_by_period['prev_price'] = security_by_period['price'].shift(1)
                security_by_period['price_change'] = security_by_period['price'] - security_by_period['prev_price']
                security_by_period['price_percent_change'] = (security_by_period['price_change'] / security_by_period['prev_price']) * 100
                
                securities_performance[isin] = {
                    'security_name': security_name,
                    'performance_by_period': security_by_period.to_dict('records')
                }
            
            # Calculate overall performance
            first_period = period_summary.iloc[0]['total_market_value'] if not period_summary.empty else 0
            last_period = period_summary.iloc[-1]['total_market_value'] if not period_summary.empty else 0
            
            if first_period > 0:
                overall_change = last_period - first_period
                overall_percent_change = (overall_change / first_period) * 100
            else:
                overall_change = 0
                overall_percent_change = 0
            
            # Calculate best and worst performing securities
            best_performing = []
            worst_performing = []
            
            for isin, data in securities_performance.items():
                periods = data['performance_by_period']
                if len(periods) >= 2:
                    first_price = periods[0]['price']
                    last_price = periods[-1]['price']
                    
                    if first_price > 0:
                        total_percent_change = ((last_price - first_price) / first_price) * 100
                        
                        performance_entry = {
                            'isin': isin,
                            'security_name': data['security_name'],
                            'first_price': first_price,
                            'last_price': last_price,
                            'percent_change': total_percent_change
                        }
                        
                        if total_percent_change > 0:
                            best_performing.append(performance_entry)
                        else:
                            worst_performing.append(performance_entry)
            
            # Sort by performance
            best_performing = sorted(best_performing, key=lambda x: x['percent_change'], reverse=True)[:5]
            worst_performing = sorted(worst_performing, key=lambda x: x['percent_change'])[:5]
            
            return {
                'status': 'success',
                'overall_performance': {
                    'first_period': first_period,
                    'last_period': last_period,
                    'change': overall_change,
                    'percent_change': overall_percent_change
                },
                'performance_by_period': performance_by_period,
                'best_performing_securities': best_performing,
                'worst_performing_securities': worst_performing,
                'securities_performance': securities_performance
            }
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Error analyzing performance: {str(e)}'
            }
    
    def generate_consolidated_report(self, securities_analysis: Dict[str, Any], 
                                    performance_analysis: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a consolidated securities report.
        
        Args:
            securities_analysis: Results from analyze_securities_by_isin
            performance_analysis: Optional results from analyze_performance_over_time
            
        Returns:
            Markdown formatted report
        """
        try:
            # Basic validation
            if not securities_analysis or securities_analysis.get('status') != 'success':
                return "# Securities Analysis Report\n\nNo valid securities data was provided for analysis."
            
            report = ["# Securities Portfolio Analysis Report", ""]
            
            # Add timestamp
            report.append(f"**Report Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            report.append("")
            
            # Add portfolio summary
            summary = securities_analysis.get('summary', {})
            report.append("## Portfolio Summary")
            report.append("")
            report.append(f"- **Total Securities:** {summary.get('total_securities', 0)}")
            report.append(f"- **Total Portfolio Value:** ${summary.get('total_portfolio_value', 0):,.2f}")
            report.append("")
            
            # Add top holdings
            top_holdings = summary.get('top_holdings', [])
            if top_holdings:
                report.append("## Top Holdings")
                report.append("")
                report.append("| Security | ISIN | Market Value | % of Portfolio |")
                report.append("|---------|------|--------------|----------------|")
                
                for holding in top_holdings:
                    report.append(
                        f"| {holding.get('security_name', 'Unknown')} | "
                        f"{holding.get('isin', 'Unknown')} | "
                        f"${holding.get('market_value', 0):,.2f} | "
                        f"{holding.get('percent_of_portfolio', 0):.2f}% |"
                    )
                
                report.append("")
            
            # Add price discrepancies
            discrepancies = summary.get('price_discrepancies', [])
            if discrepancies:
                report.append("## Price Discrepancies")
                report.append("")
                report.append("The following securities have price discrepancies across different sources:")
                report.append("")
                report.append("| Security | ISIN | Min Price | Max Price | Difference (%) | Sources |")
                report.append("|---------|------|-----------|-----------|--------------|---------|")
                
                for disc in discrepancies:
                    sources = ", ".join(disc.get('sources', ['Unknown']))
                    report.append(
                        f"| {disc.get('security_name', 'Unknown')} | "
                        f"{disc.get('isin', 'Unknown')} | "
                        f"${disc.get('min_price', 0):,.2f} | "
                        f"${disc.get('max_price', 0):,.2f} | "
                        f"{disc.get('difference_percent', 0):.2f}% | "
                        f"{sources} |"
                    )
                
                report.append("")
            
            # Add detailed securities list
            securities = securities_analysis.get('securities', {})
            if securities:
                report.append("## All Securities")
                report.append("")
                report.append("| Security | ISIN | Quantity | Market Value | Avg Price |")
                report.append("|---------|------|----------|--------------|-----------|")
                
                for isin, security in securities.items():
                    report.append(
                        f"| {security.get('security_name', 'Unknown')} | "
                        f"{security.get('isin', 'Unknown')} | "
                        f"{security.get('total_quantity', 0):,.2f} | "
                        f"${security.get('total_market_value', 0):,.2f} | "
                        f"${security.get('weighted_average_price', 0):,.2f} |"
                    )
                
                report.append("")
            
            # Add performance analysis if available
            if performance_analysis and performance_analysis.get('status') == 'success':
                report.append("## Performance Analysis")
                report.append("")
                
                # Overall performance
                overall = performance_analysis.get('overall_performance', {})
                report.append("### Overall Portfolio Performance")
                report.append("")
                
                first_period = overall.get('first_period', 0)
                last_period = overall.get('last_period', 0)
                change = overall.get('change', 0)
                percent_change = overall.get('percent_change', 0)
                
                report.append(f"- **Starting Value:** ${first_period:,.2f}")
                report.append(f"- **Current Value:** ${last_period:,.2f}")
                report.append(f"- **Change:** ${change:,.2f} ({percent_change:.2f}%)")
                report.append("")
                
                # Period by period performance
                period_performance = performance_analysis.get('performance_by_period', [])
                if period_performance:
                    report.append("### Performance by Period")
                    report.append("")
                    report.append("| Period | Portfolio Value | Change | % Change |")
                    report.append("|--------|----------------|--------|----------|")
                    
                    for period in period_performance:
                        if 'prev_value' in period and period['prev_value']:
                            report.append(
                                f"| {period.get('period', 'Unknown')} | "
                                f"${period.get('total_market_value', 0):,.2f} | "
                                f"${period.get('change', 0):,.2f} | "
                                f"{period.get('percent_change', 0):.2f}% |"
                            )
                    
                    report.append("")
                
                # Best performing securities
                best_performing = performance_analysis.get('best_performing_securities', [])
                if best_performing:
                    report.append("### Best Performing Securities")
                    report.append("")
                    report.append("| Security | ISIN | Initial Price | Current Price | % Change |")
                    report.append("|---------|------|---------------|--------------|----------|")
                    
                    for security in best_performing:
                        report.append(
                            f"| {security.get('security_name', 'Unknown')} | "
                            f"{security.get('isin', 'Unknown')} | "
                            f"${security.get('first_price', 0):,.2f} | "
                            f"${security.get('last_price', 0):,.2f} | "
                            f"{security.get('percent_change', 0):.2f}% |"
                        )
                    
                    report.append("")
                
                # Worst performing securities
                worst_performing = performance_analysis.get('worst_performing_securities', [])
                if worst_performing:
                    report.append("### Worst Performing Securities")
                    report.append("")
                    report.append("| Security | ISIN | Initial Price | Current Price | % Change |")
                    report.append("|---------|------|---------------|--------------|----------|")
                    
                    for security in worst_performing:
                        report.append(
                            f"| {security.get('security_name', 'Unknown')} | "
                            f"{security.get('isin', 'Unknown')} | "
                            f"${security.get('first_price', 0):,.2f} | "
                            f"${security.get('last_price', 0):,.2f} | "
                            f"{security.get('percent_change', 0):,.2f}% |"
                        )
                    
                    report.append("")
            
            # Add disclaimer
            report.append("## Disclaimer")
            report.append("")
            report.append("*This report is generated automatically and is for informational purposes only. "
                        "The information contained in this report should not be considered as financial advice. "
                        "Please consult with a financial advisor before making any investment decisions.*")
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error generating consolidated report: {str(e)}", exc_info=True)
            return f"# Error Generating Report\n\nAn error occurred while generating the report: {str(e)}"
    
    def _get_most_common_value(self, items: List[Dict[str, Any]], key: str) -> Any:
        """
        Get the most common value for a given key in a list of dictionaries.
        
        Args:
            items: List of dictionaries
            key: Key to extract
            
        Returns:
            Most common value
        """
        values = [item.get(key) for item in items if key in item and item[key] is not None]
        if not values:
            return None
            
        # Count occurrences
        value_counts = {}
        for value in values:
            if value not in value_counts:
                value_counts[value] = 0
            value_counts[value] += 1
        
        # Find most common
        most_common = max(value_counts.items(), key=lambda x: x[1])[0]
        return most_common

    def analyze_portfolio(self, securities: List[Dict[Any, Any]]) -> Dict[str, Any]:
        """
        Analyze portfolio data and generate comprehensive insights.
        
        Args:
            securities: List of security dictionaries
            
        Returns:
            Dictionary containing portfolio analysis
        """
        if not securities:
            return {"error": "No securities data provided"}
        
        try:
            # Convert to DataFrame for analysis
            df = pd.DataFrame(securities)
            
            # Calculate portfolio metrics
            total_value = df['market_value'].sum()
            holdings_count = len(df)
            
            # Calculate allocations
            df['allocation'] = (df['market_value'] / total_value * 100).round(2)
            
            # Group by bank
            bank_allocation = df.groupby('bank')['market_value'].sum().to_dict()
            bank_percentages = {k: (v/total_value * 100).round(2) for k, v in bank_allocation.items()}
            
            # Calculate top holdings
            top_holdings = df.nlargest(5, 'market_value')[
                ['security_name', 'market_value', 'allocation']
            ].to_dict('records')
            
            # Basic risk metrics
            concentration_risk = self._calculate_concentration_risk(df)
            
            return {
                "summary": {
                    "total_value": total_value,
                    "number_of_securities": holdings_count,
                    "number_of_banks": len(bank_allocation),
                    "concentration_risk": concentration_risk
                },
                "allocations": {
                    "by_bank": bank_percentages,
                    "top_holdings": top_holdings
                },
                "risk_metrics": {
                    "concentration_score": concentration_risk,
                    "bank_diversity_score": len(bank_allocation) / max(1, holdings_count),
                    "largest_position_size": df['allocation'].max()
                },
                "recommendations": self._generate_recommendations(
                    df, bank_percentages, concentration_risk
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {str(e)}", exc_info=True)
            return {"error": f"Analysis failed: {str(e)}"}
    
    def get_portfolio_changes(self, 
                            current_securities: List[Dict[Any, Any]], 
                            previous_securities: List[Dict[Any, Any]]) -> Dict[str, Any]:
        """
        Calculate changes between two portfolio snapshots.
        
        Args:
            current_securities: Current portfolio securities
            previous_securities: Previous portfolio securities
            
        Returns:
            Dictionary containing portfolio changes analysis
        """
        try:
            current_df = pd.DataFrame(current_securities)
            previous_df = pd.DataFrame(previous_securities)
            
            # Calculate total value changes
            current_total = current_df['market_value'].sum()
            previous_total = previous_df['market_value'].sum()
            value_change = current_total - previous_total
            percent_change = (value_change / previous_total * 100).round(2)
            
            # Find new and removed securities
            current_isins = set(current_df['isin'])
            previous_isins = set(previous_df['isin'])
            
            new_securities = current_df[current_df['isin'].isin(current_isins - previous_isins)]
            removed_securities = previous_df[previous_df['isin'].isin(previous_isins - current_isins)]
            
            # Calculate position changes for existing securities
            common_isins = current_isins.intersection(previous_isins)
            position_changes = []
            
            for isin in common_isins:
                current_pos = current_df[current_df['isin'] == isin].iloc[0]
                previous_pos = previous_df[previous_df['isin'] == isin].iloc[0]
                
                value_change = current_pos['market_value'] - previous_pos['market_value']
                percent_change = (value_change / previous_pos['market_value'] * 100).round(2)
                
                if abs(percent_change) > 1:  # Only include significant changes
                    position_changes.append({
                        "security_name": current_pos['security_name'],
                        "isin": isin,
                        "value_change": value_change,
                        "percent_change": percent_change
                    })
            
            return {
                "summary": {
                    "total_value_change": value_change,
                    "total_percent_change": percent_change,
                    "securities_added": len(new_securities),
                    "securities_removed": len(removed_securities)
                },
                "new_securities": new_securities[['security_name', 'isin', 'market_value']].to_dict('records'),
                "removed_securities": removed_securities[['security_name', 'isin', 'market_value']].to_dict('records'),
                "position_changes": sorted(
                    position_changes,
                    key=lambda x: abs(x['percent_change']),
                    reverse=True
                )
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio changes: {str(e)}", exc_info=True)
            return {"error": f"Change analysis failed: {str(e)}"}
    
    def _calculate_concentration_risk(self, df: pd.DataFrame) -> float:
        """Calculate portfolio concentration risk score."""
        # Using Herfindahl-Hirschman Index (HHI)
        allocations = df['allocation'] / 100  # Convert to decimals
        hhi = (allocations ** 2).sum()
        
        # Normalize to 0-100 scale
        max_hhi = 1  # Maximum when portfolio is 100% in one security
        min_hhi = 1 / len(df)  # Minimum when equally distributed
        normalized_hhi = ((hhi - min_hhi) / (max_hhi - min_hhi) * 100).round(2)
        
        return normalized_hhi
    
    def _generate_recommendations(self, 
                                df: pd.DataFrame, 
                                bank_alloc: Dict[str, float], 
                                concentration_risk: float) -> List[str]:
        """Generate portfolio recommendations based on analysis."""
        recommendations = []
        
        # Check concentration risk
        if concentration_risk > 70:
            recommendations.append(
                "Portfolio shows high concentration risk. Consider diversifying holdings."
            )
        
        # Check bank diversification
        if len(bank_alloc) < 2:
            recommendations.append(
                "Consider diversifying across multiple banks to reduce institutional risk."
            )
        elif max(bank_alloc.values()) > 70:
            recommendations.append(
                "High exposure to a single bank. Consider redistributing holdings."
            )
        
        # Check position sizes
        large_positions = df[df['allocation'] > 20]
        if not large_positions.empty:
            securities = ", ".join(large_positions['security_name'])
            recommendations.append(
                f"Large position concentration in: {securities}. Consider rebalancing."
            )
        
        return recommendations

def analyze_securities(securities_data: List[Dict[Any, Any]], 
                      previous_data: Optional[List[Dict[Any, Any]]] = None) -> Dict[str, Any]:
    """
    Convenience function to analyze securities data.
    
    Args:
        securities_data: Current securities data
        previous_data: Optional previous securities data for change analysis
        
    Returns:
        Dictionary containing analysis results
    """
    analyzer = SecuritiesAnalyzer()
    analysis = analyzer.analyze_portfolio(securities_data)
    
    if previous_data:
        changes = analyzer.get_portfolio_changes(securities_data, previous_data)
        analysis['changes'] = changes
    
    return analysis