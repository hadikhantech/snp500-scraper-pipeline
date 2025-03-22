# SEC Scraper

A Python package for scraping and processing SEC filings (10-K, 10-Q) from S&P 500 companies.

## Features

- Scrapes SEC filings (10-K, 10-Q) from SEC.gov
- Handles both HTML and XBRL formats
- Separates tables and text content
- Preserves table headings when possible
- Supports all S&P 500 companies
- Command-line interface for easy use
- Rate limiting to comply with SEC.gov requirements

## Installation

You can install the package directly from GitHub:

```bash
pip install git+https://github.com/yourusername/sec-scraper.git
```

Or clone the repository and install locally:

```bash
git clone https://github.com/yourusername/sec-scraper.git
cd sec-scraper
pip install -e .
```

## Usage

### Command Line Interface

The SEC Scraper provides a simple command-line interface:

```bash
# Scrape MSFT 10-K filing
sec-scraper --symbol MSFT --filing-type 10-K

# Scrape AAPL 10-Q filing
sec-scraper --symbol AAPL --filing-type 10-Q

# Scrape multiple companies
sec-scraper --symbol MSFT --symbol AAPL --symbol NVDA --filing-type 10-K

# Scrape all technology sector companies (limited to 5)
sec-scraper --sector "Information Technology" --limit 5 --filing-type 10-K

# Specify output directory
sec-scraper --symbol MSFT --filing-type 10-K --output-dir ./data/msft
```

### Python API

You can also use the scraper from your Python code:

```python
from sec_scraper.scrapers.sec_filing_scraper import SECFilingScraper
from sec_scraper.data.snp500 import SNP500Data

# Initialize the scraper
scraper = SECFilingScraper()

# Scrape a specific filing
url = "https://www.sec.gov/Archives/edgar/data/789019/000095017023035122/msft-20230630.htm"
text_content, tables = scraper.scrape_sec_filing(url)

# Save the results
scraper.save_to_files("MSFT", "10-K", text_content, tables, output_dir="./data")

# Use S&P 500 data
snp500 = SNP500Data()
snp500.download_data()  # Download latest S&P 500 data

# Get company info
microsoft = snp500.get_company_by_symbol("MSFT")
print(microsoft)

# Get companies by sector
tech_companies = snp500.get_companies_by_sector("Information Technology")
print(f"Found {len(tech_companies)} technology companies")
```

## Example Output

The scraper produces two types of output files:

1. Text content: `{symbol}_10k_text.txt` or `{symbol}_10q_text.txt`
2. Tables: `{symbol}_10k_tables.txt` or `{symbol}_10q_tables.txt`

### Text Content

The text content preserves the heading structure and paragraphs from the original document:

```
# ITEM 1. BUSINESS
  
Microsoft Corporation was founded in 1975...

## PART I

### ITEM 1. BUSINESS

Microsoft Corporation was founded in 1975. We develop, license, and support software, 
services, devices, and solutions worldwide.
```

### Tables

Tables are formatted with their original structure and headings:

```
Table: INCOME STATEMENTS

| (In millions, except per share amounts) | 2023 | 2022 | 2021 |
|----------------------------------------|------|------|------|
| Revenue                                | $211,915 | $198,270 | $168,088 |
| Cost of revenue                        | 65,865 | 62,650 | 52,232 |
| Gross margin                           | 146,050 | 135,620 | 115,856 |
| Research and development               | 27,195 | 24,512 | 20,716 |
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- SEC.gov for providing access to the financial filings
- Wikipedia for S&P 500 company data

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 