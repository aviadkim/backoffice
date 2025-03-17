import streamlit as st
import pandas as pd
import numpy as np
import os
import tempfile
import json
import matplotlib.pyplot as plt
import io
from datetime import datetime
import base64
from utils.securities_analyzer import SecuritiesAnalyzer
from utils.agent_runner import FinancialAgentRunner
import logging
from dotenv import load_dotenv

# Load environment variables and configure logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize securities analyzer
securities_analyzer = SecuritiesAnalyzer()

# Initialize agent runner if API key is available
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
agent_runner = None
if GEMINI_API_KEY:
    agent_runner = FinancialAgentRunner(api_key=GEMINI_API_KEY)

def get_download_link(content, filename, filetype="csv"):
    """Generate a download link for content."""
    if filetype == "csv":
        b64 = base64.b64encode(content.encode()).decode()
        mime = "text/csv"
    elif filetype == "json":
        b64 = base64.b64encode(content.encode()).decode()
        mime = "application/json"
    elif filetype == "md":
        b64 = base64.b64encode(content.encode()).decode()
        mime = "text/markdown"
    else:
        b64 = base64.b64encode(content).decode()
        mime = "application/octet-stream"
    
    href = f'<a href="data:{mime};base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

def create_portfolio_chart(securities_analysis):
    """Create a portfolio chart based on securities analysis."""
    if not securities_analysis or 'securities' not in securities_analysis:
        return None
    
    # Extract data for visualization
    securities = securities_analysis['securities']
    names = []
    values = []
    
    for isin, data in securities.items():
        names.append(data.get('security_name', 'Unknown'))
        values.append(data.get('total_market_value', 0))
    
    # Sort by value (largest first)
    sorted_indices = np.argsort(values)[::-1]
    names = [names[i] for i in sorted_indices]
    values = [values[i] for i in sorted_indices]
    
    # Limit to top 10 for readability
    if len(names) > 10:
        other_value = sum(values[10:])
        names = names[:10] + ['Other']
        values = values[:10] + [other_value]
    
    # Create pie chart
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.pie(values, labels=names, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title('Portfolio Composition by Market Value')
    
    return fig

def create_banks_chart(securities_analysis):
    """Create a chart showing securities by bank/source."""
    if not securities_analysis or 'securities' not in securities_analysis:
        return None
    
    # Extract data for visualization
    securities = securities_analysis['securities']
    
    # Group by bank
    bank_totals = {}
    
    for isin, data in securities.items():
        holdings = data.get('holdings_by_source', {})
        
        for bank, values in holdings.items():
            if bank not in bank_totals:
                bank_totals[bank] = 0
            
            bank_totals[bank] += values.get('market_value', 0)
    
    # Prepare data for chart
    banks = list(bank_totals.keys())
    values = list(bank_totals.values())
    
    # Sort by value
    sorted_indices = np.argsort(values)[::-1]
    banks = [banks[i] for i in sorted_indices]
    values = [values[i] for i in sorted_indices]
    
    # Create bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(banks, values)
    ax.set_xlabel('Institution')
    ax.set_ylabel('Market Value ($)')
    ax.set_title('Securities Holdings by Financial Institution')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    return fig

def create_performance_chart(performance_analysis):
    """Create a chart showing portfolio performance over time."""
    if not performance_analysis or 'performance_by_period' not in performance_analysis:
        return None
    
    # Extract data
    periods = performance_analysis['performance_by_period']
    
    # Prepare data for chart
    period_labels = [p.get('period', '') for p in periods]
    values = [p.get('total_market_value', 0) for p in periods]
    
    # Create line chart
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(period_labels, values, marker='o', linestyle='-', linewidth=2)
    ax.set_xlabel('Period')
    ax.set_ylabel('Portfolio Value ($)')
    ax.set_title('Portfolio Value Over Time')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    return fig

def main():
    """Main function for the securities analysis page."""
    st.title("Enhanced Securities Analysis")
    
    # Initialize session state if needed
    if 'securities' not in st.session_state:
        st.session_state.securities = []
    
    if 'securities_analysis' not in st.session_state:
        st.session_state.securities_analysis = None
    
    if 'performance_analysis' not in st.session_state:
        st.session_state.performance_analysis = None
    
    # Check if we have securities data
    has_securities = len(st.session_state.securities) > 0
    
    # Display securities data
    if has_securities:
        st.subheader("Securities Data")
        st.write(f"You have {len(st.session_state.securities)} securities loaded.")
        
        # Show sample
        with st.expander("View Sample Data"):
            st.dataframe(pd.DataFrame(st.session_state.securities[:5]))
    
    # Actions for securities data
    st.subheader("Analysis Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Analyze Current Securities", disabled=not has_securities):
            with st.spinner("Analyzing securities..."):
                try:
                    # Perform analysis
                    analysis = securities_analyzer.analyze_securities_by_isin(st.session_state.securities)
                    st.session_state.securities_analysis = analysis
                    
                    if analysis['status'] == 'success':
                        st.success("Securities analysis completed successfully!")
                    else:
                        st.error(f"Analysis failed: {analysis.get('message', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"Error analyzing securities: {str(e)}")
                    logger.error(f"Error analyzing securities: {str(e)}", exc_info=True)
    
    with col2:
        if st.button("Generate Performance Analysis", disabled=not has_securities):
            with st.spinner("Analyzing performance..."):
                try:
                    # Create historical data (mock for this example)
                    # In a real app, you would load historical data from a database
                    
                    # Use current securities as the most recent period
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    historical_data = []
                    
                    # Add current securities to historical data
                    for security in st.session_state.securities:
                        security_copy = security.copy()
                        security_copy['date'] = current_date
                        historical_data.append(security_copy)
                    
                    # Perform performance analysis
                    performance = securities_analyzer.analyze_performance_over_time(historical_data, 'monthly')
                    st.session_state.performance_analysis = performance
                    
                    if performance['status'] == 'success':
                        st.success("Performance analysis completed successfully!")
                    else:
                        st.error(f"Performance analysis failed: {performance.get('message', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"Error analyzing performance: {str(e)}")
                    logger.error(f"Error analyzing performance: {str(e)}", exc_info=True)
    
    # Display analysis results if available
    if st.session_state.securities_analysis and st.session_state.securities_analysis['status'] == 'success':
        st.subheader("Securities Analysis Results")
        
        # Summary information
        summary = st.session_state.securities_analysis['summary']
        st.write(f"**Total Portfolio Value:** ${summary['total_portfolio_value']:,.2f}")
        st.write(f"**Total Securities:** {summary['total_securities']}")
        
        # Portfolio composition chart
        st.subheader("Portfolio Composition")
        fig = create_portfolio_chart(st.session_state.securities_analysis)
        if fig:
            st.pyplot(fig)
        
        # Holdings by bank chart
        st.subheader("Holdings by Institution")
        bank_fig = create_banks_chart(st.session_state.securities_analysis)
        if bank_fig:
            st.pyplot(bank_fig)
        
        # Price discrepancies if any
        discrepancies = summary.get('price_discrepancies', [])
        if discrepancies:
            st.subheader("Price Discrepancies")
            st.warning(f"Found {len(discrepancies)} securities with price discrepancies across sources.")
            
            discrepancies_df = pd.DataFrame(discrepancies)
            st.dataframe(discrepancies_df)
    
    # Display performance analysis if available
    if st.session_state.performance_analysis and st.session_state.performance_analysis['status'] == 'success':
        st.subheader("Performance Analysis")
        
        # Overall performance
        overall = st.session_state.performance_analysis['overall_performance']
        if overall:
            st.write(f"**Starting Value:** ${overall['first_period']:,.2f}")
            st.write(f"**Current Value:** ${overall['last_period']:,.2f}")
            
            change = overall['change']
            percent_change = overall['percent_change']
            
            if change > 0:
                st.write(f"**Change:** 📈 +${change:,.2f} (+{percent_change:.2f}%)")
            else:
                st.write(f"**Change:** 📉 ${change:,.2f} ({percent_change:.2f}%)")
        
        # Performance chart
        st.subheader("Portfolio Value Over Time")
        perf_fig = create_performance_chart(st.session_state.performance_analysis)
        if perf_fig:
            st.pyplot(perf_fig)
        
        # Best performing securities
        best_performers = st.session_state.performance_analysis.get('best_performing_securities', [])
        if best_performers:
            st.subheader("Best Performing Securities")
            best_df = pd.DataFrame(best_performers)[['security_name', 'first_price', 'last_price', 'percent_change']]
            st.dataframe(best_df)
        
        # Worst performing securities
        worst_performers = st.session_state.performance_analysis.get('worst_performing_securities', [])
        if worst_performers:
            st.subheader("Worst Performing Securities")
            worst_df = pd.DataFrame(worst_performers)[['security_name', 'first_price', 'last_price', 'percent_change']]
            st.dataframe(worst_df)
    
    # Generate consolidated report if both analyses are available
    if (st.session_state.securities_analysis and st.session_state.securities_analysis['status'] == 'success' and
        st.session_state.performance_analysis and st.session_state.performance_analysis['status'] == 'success'):
        
        st.subheader("Generate Consolidated Report")
        
        if st.button("Generate Report"):
            with st.spinner("Generating comprehensive report..."):
                try:
                    # Generate report using local processor
                    report = securities_analyzer.generate_consolidated_report(
                        st.session_state.securities_analysis,
                        st.session_state.performance_analysis
                    )
                    
                    # Display report
                    st.subheader("Consolidated Securities Report")
                    st.markdown(report)
                    
                    # Provide download link
                    report_filename = f"securities_report_{datetime.now().strftime('%Y%m%d')}.md"
                    st.markdown(get_download_link(report, report_filename, "md"), unsafe_allow_html=True)
                    
                    # If agent runner is available, offer AI insights
                    if agent_runner:
                        st.subheader("Get AI-Powered Insights")
                        
                        if st.button("Generate AI Insights"):
                            with st.spinner("Generating AI insights..."):
                                try:
                                    # Use the agent to analyze the securities
                                    ai_analysis = agent_runner.analyze_securities(
                                        st.session_state.securities
                                    )
                                    
                                    if isinstance(ai_analysis, dict):
                                        st.subheader("AI Insights")
                                        
                                        # Display key insights
                                        if 'insights' in ai_analysis:
                                            for insight in ai_analysis['insights']:
                                                st.info(insight)
                                        
                                        # Display recommendations
                                        if 'recommendations' in ai_analysis:
                                            st.subheader("AI Recommendations")
                                            for rec in ai_analysis['recommendations']:
                                                st.success(rec)
                                    else:
                                        st.error("Failed to generate AI insights")
                                
                                except Exception as e:
                                    st.error(f"Error generating AI insights: {str(e)}")
                                    logger.error(f"Error generating AI insights: {str(e)}", exc_info=True)
                
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")
                    logger.error(f"Error generating report: {str(e)}", exc_info=True)
    
    # Upload additional securities data
    st.subheader("Upload Securities Data")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload securities CSV or JSON", type=["csv", "json"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                # Process CSV
                securities_df = pd.read_csv(uploaded_file)
                new_securities = securities_df.to_dict('records')
            else:
                # Process JSON
                new_securities = json.loads(uploaded_file.getvalue().decode('utf-8'))
                
                # Ensure it's a list
                if isinstance(new_securities, dict):
                    if 'securities' in new_securities:
                        new_securities = new_securities['securities']
                    else:
                        new_securities = [new_securities]
            
            # Add to existing securities
            if st.button("Add to Current Securities"):
                st.session_state.securities.extend(new_securities)
                st.success(f"Added {len(new_securities)} securities to your data.")
                st.experimental_rerun()
            
            # Replace existing securities
            if st.button("Replace Current Securities"):
                st.session_state.securities = new_securities
                st.session_state.securities_analysis = None
                st.session_state.performance_analysis = None
                st.success(f"Replaced securities data with {len(new_securities)} new records.")
                st.experimental_rerun()
        
        except Exception as e:
            st.error(f"Error processing uploaded file: {str(e)}")
            logger.error(f"Error processing uploaded file: {str(e)}", exc_info=True)
    
    # Display instructions
    with st.expander("Instructions"):
        st.markdown("""
        ### How to use the Securities Analysis page
        
        1. **Upload securities data** from a PDF using the Document Upload page
        2. **Analyze the securities** to get insights into your portfolio
        3. **Generate a performance analysis** to see how your portfolio has changed over time
        4. **Create a consolidated report** with all the insights
        
        ### Data Format
        
        You can upload additional securities data in CSV or JSON format. The CSV should have the following columns:
        
        - `isin` - International Securities Identification Number
        - `security_name` - Name of the security
        - `quantity` - Number of shares or units
        - `price` - Price per share or unit
        - `market_value` - Total market value
        - `bank` - Financial institution holding the security
        
        ### Tips
        
        - For price discrepancy detection, upload securities data from multiple sources
        - For performance analysis, include historical data with dates
        - Use the AI insights for personalized recommendations based on your portfolio
        """)

if __name__ == "__main__":
    main()