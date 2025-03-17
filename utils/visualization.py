import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FinancialVisualizer:
    """Utility for creating financial visualizations."""
    
    @staticmethod
    def create_holdings_pie_chart(securities_data: Dict[str, Any], title: str = "התפלגות החזקות לפי נייר ערך") -> go.Figure:
        """Create a pie chart showing distribution of holdings."""
        try:
            values = [data['total_value'] for data in securities_data['securities'].values()]
            labels = [data['security_name'] for data in securities_data['securities'].values()]
            
            fig = px.pie(
                values=values,
                names=labels,
                hole=0.4,
                title=title
            )
            
            fig.update_layout(
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                )
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating holdings pie chart: {str(e)}")
            return None

    @staticmethod
    def create_bank_comparison_chart(securities_data: Dict[str, Any]) -> go.Figure:
        """Create a stacked bar chart comparing holdings across banks."""
        try:
            # Prepare data
            bank_holdings = []
            for isin, data in securities_data['securities'].items():
                for holding in data.get('holdings', []):
                    bank_holdings.append({
                        'Bank': holding.get('bank', 'Unknown'),
                        'Security': data['security_name'],
                        'Value': holding.get('market_value', 0)
                    })
            
            df = pd.DataFrame(bank_holdings)
            
            fig = px.bar(
                df,
                x='Bank',
                y='Value',
                color='Security',
                title='השוואת החזקות בין בנקים',
                labels={'Value': 'שווי ($)', 'Bank': 'בנק/חשבון', 'Security': 'נייר ערך'}
            )
            
            fig.update_layout(
                barmode='stack',
                height=500,
                xaxis={'categoryorder': 'total descending'}
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating bank comparison chart: {str(e)}")
            return None

    @staticmethod
    def create_price_discrepancy_chart(securities_data: Dict[str, Any]) -> go.Figure:
        """Create a visualization of price discrepancies."""
        try:
            discrepancies = []
            for isin, data in securities_data['securities'].items():
                if data.get('price_discrepancies', False):
                    discrepancies.append({
                        'Security': data['security_name'],
                        'Min Price': data['min_price'],
                        'Max Price': data['max_price'],
                        'Difference %': data['price_difference_pct']
                    })
            
            if not discrepancies:
                return None
            
            df = pd.DataFrame(discrepancies)
            
            fig = go.Figure()
            
            # Add price range bars
            fig.add_trace(go.Bar(
                name='טווח מחירים',
                x=df['Security'],
                y=df['Max Price'] - df['Min Price'],
                base=df['Min Price'],
                marker_color='lightgrey',
                hovertemplate=(
                    'נייר ערך: %{x}<br>' +
                    'מחיר מינימלי: $%{base:.2f}<br>' +
                    'מחיר מקסימלי: $%{base:.2f}<br>' +
                    'פער: %{y:.2f}%<br>' +
                    '<extra></extra>'
                )
            ))
            
            # Add markers for min and max prices
            fig.add_trace(go.Scatter(
                name='מחיר מינימלי',
                x=df['Security'],
                y=df['Min Price'],
                mode='markers',
                marker=dict(color='blue', size=8),
                hovertemplate='מחיר מינימלי: $%{y:.2f}<extra></extra>'
            ))
            
            fig.add_trace(go.Scatter(
                name='מחיר מקסימלי',
                x=df['Security'],
                y=df['Max Price'],
                mode='markers',
                marker=dict(color='red', size=8),
                hovertemplate='מחיר מקסימלי: $%{y:.2f}<extra></extra>'
            ))
            
            fig.update_layout(
                title='פערי מחירים בין חשבונות',
                xaxis_title='נייר ערך',
                yaxis_title='מחיר ($)',
                height=400,
                showlegend=True,
                hovermode='x unified'
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating price discrepancy chart: {str(e)}")
            return None

    @staticmethod
    def create_performance_chart(performance_data: Dict[str, Any]) -> go.Figure:
        """Create a line chart showing performance over time."""
        try:
            # Extract time series data
            time_series = performance_data.get('time_series', {})
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'Period': period,
                    'Value': data['total_value'],
                    'Change': data.get('change_pct', 0)
                }
                for period, data in time_series.items()
            ])
            
            # Create figure with secondary y-axis
            fig = go.Figure()
            
            # Add total value line
            fig.add_trace(go.Scatter(
                x=df['Period'],
                y=df['Value'],
                name='שווי תיק',
                line=dict(color='blue'),
                hovertemplate='תקופה: %{x}<br>שווי: $%{y:,.2f}<extra></extra>'
            ))
            
            # Add percent change bars on secondary axis
            fig.add_trace(go.Bar(
                x=df['Period'],
                y=df['Change'],
                name='שינוי באחוזים',
                marker_color='lightblue',
                yaxis='y2',
                hovertemplate='תקופה: %{x}<br>שינוי: %{y:.1f}%<extra></extra>'
            ))
            
            fig.update_layout(
                title='ביצועי תיק לאורך זמן',
                xaxis_title='תקופה',
                yaxis_title='שווי תיק ($)',
                yaxis2=dict(
                    title='שינוי באחוזים (%)',
                    overlaying='y',
                    side='right'
                ),
                height=500,
                hovermode='x unified'
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating performance chart: {str(e)}")
            return None

    @staticmethod
    def create_correlation_heatmap(securities_data: Dict[str, Any]) -> go.Figure:
        """Create a correlation heatmap between securities."""
        try:
            # Extract daily returns for each security (if available)
            securities = {}
            for isin, data in securities_data['securities'].items():
                if 'returns' in data:  # This would need to be calculated elsewhere
                    securities[data['security_name']] = data['returns']
            
            if not securities:
                return None
            
            # Create correlation matrix
            df = pd.DataFrame(securities)
            corr_matrix = df.corr()
            
            # Create heatmap
            fig = px.imshow(
                corr_matrix,
                title='מטריצת קורלציות בין ניירות ערך',
                labels=dict(x='נייר ערך', y='נייר ערך', color='קורלציה'),
                color_continuous_scale='RdBu',
                aspect='auto'
            )
            
            fig.update_layout(
                height=600,
                width=800
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating correlation heatmap: {str(e)}")
            return None

    def create_allocation_treemap(self, securities_data: Dict[str, Any]):
        """
        Create a treemap visualization of portfolio allocation.
        
        Args:
            securities_data: Dict containing securities data with ISIN keys
            
        Returns:
            Plotly figure object
        """
        # Prepare data structure
        allocation_data = []
        for isin, data in securities_data.items():
            for holding in data.get('holdings', []):
                allocation_data.append({
                    'Bank': holding.get('bank', 'Unknown'),
                    'Security': data.get('security_name', f"Unknown ({isin})"),
                    'Value': holding.get('market_value', 0)
                })
        
        df = pd.DataFrame(allocation_data)
        
        fig = px.treemap(
            df,
            path=[px.Constant('Portfolio'), 'Bank', 'Security'],
            values='Value',
            title='Portfolio Structure',
            custom_data=['Value']
        )
        
        fig.update_traces(
            hovertemplate=(
                '%{label}<br>' +
                'Value: $%{customdata[0]:,.2f}<br>' +
                '<extra></extra>'
            )
        )
        
        fig.update_layout(height=700)
        return fig
    
    def create_dashboard(self, securities_data: Dict[str, Any], performance_data: Dict[str, Any] = None):
        """
        Create a comprehensive dashboard with multiple visualizations.
        
        Args:
            securities_data: Dict containing securities data with ISIN keys
            performance_data: Optional dict containing performance data
            
        Returns:
            Dict of Plotly figure objects
        """
        figures = {}
        
        # Create holdings pie chart
        figures['holdings_pie'] = self.create_holdings_pie_chart(securities_data)
        
        # Create bank comparison
        figures['bank_comparison'] = self.create_bank_comparison_chart(securities_data)
        
        # Create price discrepancy chart
        figures['price_discrepancies'] = self.create_price_discrepancy_chart(securities_data)
        
        # Create allocation treemap
        figures['allocation_treemap'] = self.create_allocation_treemap(securities_data)
        
        # Create performance chart if data available
        if performance_data:
            figures['performance'] = self.create_performance_chart(performance_data)
        
        return figures
    
    def create_correlation_matrix(self, securities_data: Dict[str, Any]):
        """
        Create a correlation matrix heatmap of security returns.
        
        Args:
            securities_data: Dict containing securities data with ISIN keys
            
        Returns:
            Plotly figure object
        """
        # Extract returns data if available
        returns_data = {}
        for isin, data in securities_data.items():
            if 'returns' in data:
                security_name = data.get('security_name', f"Unknown ({isin})")
                returns_data[security_name] = data['returns']
        
        if not returns_data:
            fig = go.Figure()
            fig.add_annotation(
                text="No returns data available for correlation analysis",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # Create correlation matrix
        returns_df = pd.DataFrame(returns_data)
        corr_matrix = returns_df.corr()
        
        # Create heatmap
        fig = px.imshow(
            corr_matrix,
            labels=dict(color="Correlation"),
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            color_continuous_scale="RdBu",
            aspect="auto"
        )
        
        fig.update_layout(
            title="Securities Correlation Matrix",
            height=600,
            width=800
        )
        
        return fig

# Combine both classes' functionality
class SecurityVisualizer(FinancialVisualizer):
    """Combined visualizer with all security analysis capabilities."""
    
    def __init__(self):
        super().__init__()
        
    def create_complete_analysis(self, securities_data: Dict[str, Any], performance_data: Dict[str, Any] = None):
        """
        Create a complete set of visualizations for security analysis.
        
        Args:
            securities_data: Dict containing securities data
            performance_data: Optional performance data
            
        Returns:
            Dict containing all visualization figures
        """
        figures = self.create_dashboard(securities_data, performance_data)
        
        # Add correlation matrix if we have returns data
        corr_matrix = self.create_correlation_matrix(securities_data)
        if corr_matrix:
            figures['correlation_matrix'] = corr_matrix
        
        return figures
