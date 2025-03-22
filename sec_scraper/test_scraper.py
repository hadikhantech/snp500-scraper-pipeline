"""
Test script for the SEC scraper package.

This script demonstrates how to use the SEC scraper to scrape
an SEC filing for a sample company.
"""

import logging
import os
from sec_scraper.scrapers.sec_filing_scraper import SECFilingScraper
from sec_scraper.scrapers.edgar_url_parser import EdgarURLParser
from sec_scraper.data.snp500 import SNP500Data
from sec_scraper.utils.helpers import setup_logging

def main():
    """
    Main function to test the SEC scraper.
    """
    # Setup logging
    setup_logging(log_level="INFO")
    logger = logging.getLogger(__name__)
    
    # Create output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize S&P 500 data (uses sample data)
    snp500 = SNP500Data()
    
    # Choose a company to scrape
    symbol = "MSFT"
    filing_type = "10-K"
    
    company = snp500.get_company_by_symbol(symbol)
    if not company:
        logger.error(f"Company with symbol {symbol} not found in S&P 500 data")
        return
    
    logger.info(f"Testing SEC scraper with {company['Company Name']} ({symbol}) {filing_type}")
    
    # Get Edgar URL
    browse_url = snp500.get_sec_filing_url(symbol, filing_type)
    if not browse_url:
        logger.error(f"Could not generate URL for {symbol}")
        return
    
    # For this test, we'll use a known URL to avoid network issues
    url = "https://www.sec.gov/Archives/edgar/data/789019/000095017023035122/msft-20230630.htm"
    logger.info(f"Using test URL: {url}")
    
    # Initialize and run the scraper
    scraper = SECFilingScraper(delay=1.0)
    
    # Scrape the filing
    logger.info(f"Scraping {symbol} {filing_type} from {url}...")
    text_content, tables = scraper.scrape_sec_filing(url)
    
    if not text_content:
        logger.error(f"Failed to scrape {symbol} {filing_type}")
        return
    
    # Save results
    text_file = os.path.join(output_dir, f"{symbol.lower()}_{filing_type.lower().replace('-', '')}_text.txt")
    tables_file = os.path.join(output_dir, f"{symbol.lower()}_{filing_type.lower().replace('-', '')}_tables.txt")
    
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text_content)
    logger.info(f"Saved text content to {text_file}")
    
    with open(tables_file, 'w', encoding='utf-8') as f:
        f.write('\n\n' + ('-' * 80) + '\n\n'.join(tables))
    logger.info(f"Saved tables to {tables_file}")
    
    logger.info("Test completed successfully!")

if __name__ == "__main__":
    main() 