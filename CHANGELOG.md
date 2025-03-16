# FinAnalyzer Changelog

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
