# FinAnalyzer

A powerful financial document analysis tool that uses cloud services for OCR and text extraction.

## Features

- Upload and analyze bank statements and securities reports
- Extract text and tables from PDF documents using Google Cloud Vision API
- Process securities information with AI-powered analysis
- Generate reports and visualizations
- Smart bot for financial insights

## Prerequisites

- Python 3.8 or higher
- Google Cloud account with Vision API enabled
- Gemini API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/finanalyzer.git
cd finanalyzer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google Cloud credentials:
   - Create a Google Cloud project
   - Enable the Vision API
   - Create a service account and download the credentials JSON file
   - Place the credentials file in a secure location
   - Update the `GOOGLE_APPLICATION_CREDENTIALS` path in `.env`

4. Set up Gemini API:
   - Get a Gemini API key from Google AI Studio
   - Update the `GEMINI_API_KEY` in `.env`

## Usage

1. Start the application:
```bash
python -m streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Upload your financial documents and start analyzing!

## Configuration

The application can be configured through the following files:

- `.env`: Environment variables for API keys and credentials
- `.streamlit/config.toml`: Streamlit configuration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.