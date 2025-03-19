# FinAnalyzer Changelog

## Version 3.1.0 - Enhanced Securities AI Processing

### New Features
- **AI-Powered Securities Processing**: 
  - Enhanced template-based extraction with AI fallback
  - Improved accuracy in ISIN and security name detection
  - Smart field mapping and validation
  - Multi-bank template support
- **Database Integration**:
  - SQLite/PostgreSQL support for data persistence
  - Efficient storage and retrieval of securities data
  - Template management system
- **Enhanced Security Analysis**:
  - Advanced pattern recognition for document processing
  - Improved performance metrics calculation
  - Better handling of multi-currency portfolios
- **UI/UX Improvements**:
  - Redesigned securities chatbot interface
  - Real-time processing status updates
  - Enhanced error handling and user feedback

### Technical Improvements
- Migrated to Gemini 1.5 Pro for improved AI capabilities
- Enhanced document processing pipeline
- Added comprehensive error handling
- Improved session state management
- Added new utilities for database operations

### Bug Fixes
- Fixed template matching accuracy
- Improved error recovery in document processing
- Enhanced ISIN validation
- Better handling of malformed PDF inputs

## Version 1.3.0 - Enhanced PDF Processing Module

### New Features
- **Advanced PDF Processing**: Added support for multiple global financial institutions
  - Support for major global investment banks (JP Morgan, Goldman Sachs, etc.)
  - Support for international brokerages (Interactive Brokers, Charles Schwab, etc.)
  - Support for European and Asian financial institutions
- **Improved Data Extraction**: Enhanced accuracy in extracting financial data from PDFs
- **Multi-format Export System**: Added comprehensive export capabilities
  - Excel export with multiple sheets and formatting
  - CSV export with data categorization
  - JSON export for raw data
- **Enhanced Visualization Suite**: New visualization tools and improvements

## Version 1.2.0 - Securities Analysis Module

### New Features
- **Securities Analysis Module**: Added comprehensive ISIN-based securities analysis
  - Portfolio consolidation across multiple banks/accounts
  - Price discrepancy detection between different financial institutions
  - Detailed holdings breakdown and distribution analysis
  - Performance tracking over time
- **Enhanced Visualization**: Added new interactive charts for securities analysis
  - Holdings distribution by security
  - Bank/account comparison charts
  - Security valuation breakdown
- **Multi-file Uploads**: Support for processing multiple files simultaneously
- **Reports Management System**: Save, load, and export securities analysis reports
- **Email Integration Framework**: Groundwork for automatic report retrieval via email

### Technical Improvements
- Improved data processing pipeline for financial documents
- Enhanced error handling throughout the application
- Added automatic data persistence for reports
- Better session state management

### Bug Fixes
- Fixed JSON parsing errors in agent response handling
- Improved the reliability of the Gemini function calling
- Enhanced error recovery in document processing
