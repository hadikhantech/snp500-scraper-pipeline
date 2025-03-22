"""
Command-line interface for SEC scraper.

This module provides a command-line interface for the SEC scraper,
allowing users to scrape SEC filings for S&P 500 companies.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

from ..scrapers.sec_filing_scraper import SECFilingScraper
from ..scrapers.edgar_url_parser import EdgarURLParser
from ..data.snp500 import SNP500Data
from ..utils.helpers import setup_logging, ensure_dir, normalize_company_symbol, normalize_filing_type

logger = logging.getLogger(__name__)

def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Scrape SEC filings (10-K, 10-Q) from S&P 500 companies",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--symbol', '-s',
        help='Company symbol (e.g., MSFT). Can be used multiple times.',
        action='append',
        default=[]
    )
    
    parser.add_argument(
        '--filing-type', '-f',
        help='Filing type to scrape (10-K or 10-Q)',
        choices=['10-K', '10-Q', '10K', '10Q'],
        default='10-K'
    )
    
    parser.add_argument(
        '--year', '-y',
        help='Filing year',
        type=int,
        default=None
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        help='Output directory',
        default='output'
    )
    
    parser.add_argument(
        '--snp500-data', '-d',
        help='Path to S&P 500 data CSV file. If not provided, data will be downloaded.',
        default=None
    )
    
    parser.add_argument(
        '--download-snp500',
        help='Download latest S&P 500 data even if file exists',
        action='store_true'
    )
    
    parser.add_argument(
        '--sector', '-c',
        help='Scrape companies in a specific sector only',
        default=None
    )
    
    parser.add_argument(
        '--limit', '-l',
        help='Limit the number of companies to scrape',
        type=int,
        default=None
    )
    
    parser.add_argument(
        '--delay', '-w',
        help='Delay between requests in seconds',
        type=float,
        default=1.0
    )
    
    parser.add_argument(
        '--retries', '-r',
        help='Number of retries for failed requests',
        type=int,
        default=3
    )
    
    parser.add_argument(
        '--log-level',
        help='Logging level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO'
    )
    
    parser.add_argument(
        '--log-file',
        help='Log file path',
        default=None
    )
    
    parser.add_argument(
        '--use-sample-urls',
        help='Use sample URLs for testing instead of scraping EDGAR',
        action='store_true'
    )
    
    return parser.parse_args()

def main():
    """
    Main entry point for the SEC scraper CLI.
    """
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Create output directory
    output_dir = ensure_dir(args.output_dir)
    logger.info(f"Output directory: {output_dir}")
    
    # Initialize S&P 500 data
    snp500 = SNP500Data(args.snp500_data)
    
    # Download S&P 500 data if needed
    if args.download_snp500 or (not args.snp500_data and not snp500.companies):
        data_dir = ensure_dir(os.path.join(output_dir, 'data'))
        output_path = os.path.join(data_dir, 'snp500_data.csv')
        logger.info(f"Downloading S&P 500 data to {output_path}...")
        if not snp500.download_data(output_path):
            logger.error("Failed to download S&P 500 data. Exiting.")
            sys.exit(1)
    
    # Determine which companies to scrape
    companies_to_scrape = []
    if args.symbol:
        # Use specific symbols
        for symbol in args.symbol:
            company = snp500.get_company_by_symbol(symbol)
            if company:
                companies_to_scrape.append(company)
            else:
                logger.warning(f"Company with symbol {symbol} not found in S&P 500 data")
    elif args.sector:
        # Use companies from a specific sector
        companies_to_scrape = snp500.get_companies_by_sector(args.sector)
        logger.info(f"Found {len(companies_to_scrape)} companies in sector: {args.sector}")
    else:
        # Use all companies
        companies_to_scrape = snp500.companies
        logger.info(f"Using all {len(companies_to_scrape)} companies")
    
    # Apply limit if specified
    if args.limit and args.limit > 0:
        companies_to_scrape = companies_to_scrape[:args.limit]
        logger.info(f"Limited to {len(companies_to_scrape)} companies")
    
    if not companies_to_scrape:
        logger.error("No companies to scrape. Exiting.")
        sys.exit(1)
    
    # Initialize the scraper and URL parser
    scraper = SECFilingScraper(delay=args.delay, retries=args.retries)
    url_parser = EdgarURLParser(delay=args.delay/2, retries=args.retries)
    
    # Process each company
    logger.info(f"Starting to scrape {len(companies_to_scrape)} companies for {args.filing_type} filings...")
    
    # Keep track of progress
    success_count = 0
    error_count = 0
    
    for i, company in enumerate(companies_to_scrape):
        symbol = company['Symbol']
        logger.info(f"[{i+1}/{len(companies_to_scrape)}] Processing {symbol}...")
        
        # Generate the EDGAR browse URL
        browse_url = snp500.get_sec_filing_url(symbol, args.filing_type, args.year)
        if not browse_url:
            logger.error(f"Could not generate URL for {symbol}")
            error_count += 1
            continue
        
        # Determine the document URL
        if args.use_sample_urls:
            # Use sample URLs for testing
            if symbol.upper() == 'MSFT' and args.filing_type in ['10-K', '10K']:
                url = "https://www.sec.gov/Archives/edgar/data/789019/000095017023035122/msft-20230630.htm"
            elif symbol.upper() == 'MSFT' and args.filing_type in ['10-Q', '10Q']:
                url = "https://www.sec.gov/Archives/edgar/data/789019/000095017023014423/msft-20230331.htm"
            elif symbol.upper() == 'AAPL' and args.filing_type in ['10-K', '10K']:
                url = "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm"
            elif symbol.upper() == 'NVDA' and args.filing_type in ['10-K', '10K']:
                url = "https://www.sec.gov/Archives/edgar/data/1045810/000104581023000031/nvda-20230129.htm"
            else:
                logger.warning(f"No sample URL for {symbol} {args.filing_type}, using browse URL")
                url = browse_url
        else:
            # Use the URL parser to find the actual document URL
            logger.info(f"Finding document URL for {symbol} {args.filing_type} from {browse_url}...")
            url = url_parser.get_document_url(browse_url, args.filing_type)
            if not url:
                logger.error(f"Could not find document URL for {symbol} {args.filing_type}")
                error_count += 1
                continue
        
        try:
            # Scrape the filing
            logger.info(f"Scraping {symbol} {args.filing_type} from {url}...")
            text_content, tables = scraper.scrape_sec_filing(url)
            
            if not text_content:
                logger.error(f"Failed to scrape {symbol} {args.filing_type}")
                error_count += 1
                continue
            
            # Save the results
            company_dir = ensure_dir(os.path.join(output_dir, symbol.lower()))
            filing_type_normalized = normalize_filing_type(args.filing_type)
            
            # Save text content
            text_file = os.path.join(company_dir, f"{symbol.lower()}_{filing_type_normalized.lower()}_text.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            logger.info(f"Saved text content to {text_file}")
            
            # Save tables
            tables_file = os.path.join(company_dir, f"{symbol.lower()}_{filing_type_normalized.lower()}_tables.txt")
            with open(tables_file, 'w', encoding='utf-8') as f:
                f.write('\n\n' + ('-' * 80) + '\n\n'.join(tables))
            logger.info(f"Saved tables to {tables_file}")
            
            # Save metadata
            metadata_file = os.path.join(company_dir, f"{symbol.lower()}_{filing_type_normalized.lower()}_metadata.txt")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                f.write(f"Company: {company['Company Name']}\n")
                f.write(f"Symbol: {symbol}\n")
                f.write(f"Filing Type: {args.filing_type}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Sector: {company.get('GICS Sector', '')}\n")
                f.write(f"Industry: {company.get('GICS Sub-Industry', '')}\n")
                f.write(f"Scrape Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
            logger.info(f"Saved metadata to {metadata_file}")
            
            success_count += 1
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
            error_count += 1
            continue
    
    # Display summary
    logger.info(f"Scraping complete. Processed {len(companies_to_scrape)} companies.")
    logger.info(f"Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    main() 