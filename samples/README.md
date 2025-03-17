# Sample Files

This directory contains sample PDF files for testing the securities processor.

## Required Files

1. `sample_securities.pdf` - A sample securities statement containing:
   - Security names
   - ISIN numbers
   - Quantities
   - Prices
   - Market values

## Usage

You can place your own PDF files here for testing. The example script will look for `sample_securities.pdf` by default.

To run with a sample file:
```bash
python examples/process_securities_pdf.py samples/sample_securities.pdf demo
```
