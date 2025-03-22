# Stock Market RAG with SEC Filings

A repository for scraping stock market data from SEC.gov and processing it using RAG (Retrieval Augmented Generation) techniques.

## Overview

This repository contains tools for:

1. **SEC Filings Scraper**: A Python package (`sec-scraper`) for scraping 10-K and 10-Q filings from S&P 500 companies, with separate extraction of text and tables.
2. **Processing Pipeline**: Tools for processing and organizing the scraped data.
3. **RAG Integration**: (Coming soon) Tools for chunking the data and using it with Retrieval Augmented Generation.

## SEC Scraper

The `sec-scraper` package provides a robust solution for scraping SEC filings. See the [sec_scraper/README.md](sec_scraper/README.md) for detailed documentation.

### Key Features

- Scrapes SEC filings (10-K, 10-Q) from SEC.gov
- Handles both HTML and XBRL formats
- Separates tables and text content
- Preserves table headings when possible
- Supports all S&P 500 companies
- Command-line interface for easy use

### Quick Start

```bash
# Install the package
cd sec_scraper
pip install -e .

# Scrape MSFT 10-K filing
sec-scraper --symbol MSFT --filing-type 10-K

# Scrape multiple companies
sec-scraper --symbol MSFT --symbol AAPL --symbol NVDA --filing-type 10-K

# Scrape all technology sector companies (limited to 5)
sec-scraper --sector "Information Technology" --limit 5 --filing-type 10-K
```

## Setup

1. Clone this repository
2. Create a `.env` file in the root directory based on the `.env.example` file
3. Set your API keys in the `.env` file

```
OPENROUTER_API_KEY=your-actual-api-key-here
HUGGINGFACE_API_KEY=your-actual-api-key-here
```

## Project Structure

```
stock-market-rag/
├── .env.example          # Template for environment variables
├── README.md             # Main documentation
├── LICENSE               # License file
├── metadata-research/    # Scripts and data for S&P 500 metadata
├── scrape/               # Legacy scraping scripts and sample data
└── sec_scraper/          # New SEC filings scraper package
    ├── sec_scraper/      # Package source code
    │   ├── scrapers/     # Scraping functionality
    │   ├── data/         # Data handling
    │   ├── utils/        # Utility functions
    │   └── cli/          # Command-line interface
    ├── setup.py          # Package installation script
    ├── requirements.txt  # Package dependencies
    └── README.md         # Package documentation
```

## Roadmap

1. ✅ Scraper for SEC filings with text and table separation
2. 🔄 Pipeline for scraping all S&P 500 companies
3. ⏳ Text chunking based on metadata parameters
4. ⏳ RAG integration for financial analysis

## Security

- Never commit API keys or sensitive credentials to the repository
- Use environment variables for all API keys
- The `.env` file is included in `.gitignore` to prevent accidental commits

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
