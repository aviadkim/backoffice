# utils/export_utils.py
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class ReportExporter:
    """Utility for exporting reports in various formats."""
    
    def __init__(self, export_dir: str = "exports"):
        """Initialize the exporter with target directory."""
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
    
    def export_excel(self, report_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Export report data to Excel format.
        
        Args:
            report_data: Dict containing report data
            filename: Optional filename, defaults to timestamp-based name
            
        Returns:
            Path to the exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"financial_report_{timestamp}.xlsx"
        
        file_path = os.path.join(self.export_dir, filename)
        
        # Create a Pandas Excel writer
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                "Metric": ["Report Date", "Total Portfolio Value", "Number of Securities"],
                "Value": [
                    report_data.get('report_date', 'N/A'),
                    f"${report_data.get('total_portfolio_value', 0):,.2f}",
                    report_data.get('total_isins', 0)
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Securities sheet
            securities_data = []
            for isin, data in report_data.get('securities', {}).items():
                row = {
                    'ISIN': isin,
                    'Security Name': data.get('security_name', 'Unknown'),
                    'Total Value': data.get('total_value', 0),
                    'Price Discrepancy': 'Yes' if data.get('price_discrepancies', False) else 'No',
                    'Min Price': data.get('min_price', 'N/A') if data.get('price_discrepancies', False) else 'N/A',
                    'Max Price': data.get('max_price', 'N/A') if data.get('price_discrepancies', False) else 'N/A',
                    'Difference %': f"{data.get('price_difference_pct', 0):.2f}%" if data.get('price_discrepancies', False) else 'N/A',
                    'Banks': ', '.join(data.get('banks', []))
                }
                securities_data.append(row)
            
            pd.DataFrame(securities_data).to_excel(writer, sheet_name='Securities', index=False)
            
            # Bank breakdown sheet
            bank_data = {}
            for isin, data in report_data.get('securities', {}).items():
                security_name = data.get('security_name', 'Unknown')
                
                for holding in data.get('holdings', []):
                    bank = holding.get('bank', 'Unknown')
                    if bank not in bank_data:
                        bank_data[bank] = []
                    
                    bank_data[bank].append({
                        'ISIN': isin,
                        'Security Name': security_name,
                        'Quantity': holding.get('quantity', 0),
                        'Price': holding.get('price', 0),
                        'Market Value': holding.get('market_value', 0)
                    })
            
            # Create a sheet for each bank
            for bank, holdings in bank_data.items():
                bank_sheet = pd.DataFrame(holdings)
                bank_sheet.to_excel(writer, sheet_name=f'Bank_{bank}'[:31], index=False)  # Excel limits sheet names to 31 chars
            
            # Performance sheet (if available)
            if 'performance' in report_data:
                performance_data = []
                for period, data in report_data.get('performance', {}).get('time_series', {}).items():
                    performance_data.append({
                        'Period': period,
                        'Total Value': data.get('total_value', 0),
                        'Change %': f"{data.get('change_pct', 'N/A'):,.2f}%" if data.get('change_pct') is not None else 'N/A'
                    })
                
                pd.DataFrame(performance_data).to_excel(writer, sheet_name='Performance', index=False)
        
        return file_path
    
    def export_csv(self, report_data: Dict[str, Any], filename: Optional[str] = None) -> List[str]:
        """
        Export report data to CSV format (multiple files).
        
        Args:
            report_data: Dict containing report data
            filename: Optional base filename, defaults to timestamp-based name
            
        Returns:
            List of paths to the exported files
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_base = f"financial_report_{timestamp}"
        else:
            filename_base = filename.split('.')[0]  # Remove extension if present
        
        exported_files = []
        
        # Securities CSV
        securities_data = []
        for isin, data in report_data.get('securities', {}).items():
            row = {
                'ISIN': isin,
                'Security Name': data.get('security_name', 'Unknown'),
                'Total Value': data.get('total_value', 0),
                'Price Discrepancy': 'Yes' if data.get('price_discrepancies', False) else 'No',
                'Min Price': data.get('min_price', 'N/A') if data.get('price_discrepancies', False) else 'N/A',
                'Max Price': data.get('max_price', 'N/A') if data.get('price_discrepancies', False) else 'N/A',
                'Difference %': f"{data.get('price_difference_pct', 0):.2f}%" if data.get('price_discrepancies', False) else 'N/A',
                'Banks': ', '.join(data.get('banks', []))
            }
            securities_data.append(row)
        
        securities_file = os.path.join(self.export_dir, f"{filename_base}_securities.csv")
        pd.DataFrame(securities_data).to_csv(securities_file, index=False)
        exported_files.append(securities_file)
        
        # Holdings by bank CSV
        holdings_data = []
        for isin, data in report_data.get('securities', {}).items():
            security_name = data.get('security_name', 'Unknown')
            
            for holding in data.get('holdings', []):
                holdings_data.append({
                    'ISIN': isin,
                    'Security Name': security_name,
                    'Bank': holding.get('bank', 'Unknown'),
                    'Quantity': holding.get('quantity', 0),
                    'Price': holding.get('price', 0),
                    'Market Value': holding.get('market_value', 0)
                })
        
        holdings_file = os.path.join(self.export_dir, f"{filename_base}_holdings.csv")
        pd.DataFrame(holdings_data).to_csv(holdings_file, index=False)
        exported_files.append(holdings_file)
        
        # Performance CSV (if available)
        if 'performance' in report_data:
            performance_data = []
            for period, data in report_data.get('performance', {}).get('time_series', {}).items():
                performance_data.append({
                    'Period': period,
                    'Total Value': data.get('total_value', 0),
                    'Change %': data.get('change_pct', 'N/A')
                })
            
            performance_file = os.path.join(self.export_dir, f"{filename_base}_performance.csv")
            pd.DataFrame(performance_data).to_csv(performance_file, index=False)
            exported_files.append(performance_file)
        
        return exported_files
    
    def export_json(self, report_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Export report data to JSON format.
        
        Args:
            report_data: Dict containing report data
            filename: Optional filename, defaults to timestamp-based name
            
        Returns:
            Path to the exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"financial_report_{timestamp}.json"
        
        file_path = os.path.join(self.export_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return file_path