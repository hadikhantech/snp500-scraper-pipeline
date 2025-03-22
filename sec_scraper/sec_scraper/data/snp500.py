"""
S&P 500 data handling module.

This module provides functionality to load, process, and access
S&P 500 company data for the SEC scraper.
"""

import csv
import os
import logging
import pandas as pd
from pathlib import Path
import requests
from typing import List, Dict, Optional, Union, Tuple
import time

logger = logging.getLogger(__name__)

class SNP500Data:
    """
    Class for handling S&P 500 company data.
    
    This class provides methods to load S&P 500 company data from various sources,
    and to access and filter that data for use with the SEC scraper.
    """
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the S&P 500 data handler.
        
        Args:
            data_path (str, optional): Path to a CSV file containing S&P 500 data.
                If None, the module will use the bundled sample data file.
        """
        self.companies = []
        self.data_path = data_path
        self._dataframe = None
        
        # Load data if provided
        if data_path:
            self.load_data(data_path)
        else:
            # Load sample data
            sample_data_path = os.path.join(os.path.dirname(__file__), 'sample_snp500_data.csv')
            if os.path.exists(sample_data_path):
                self.load_data(sample_data_path)
                logger.info("Loaded sample S&P 500 data")
            else:
                logger.warning("Sample S&P 500 data not found")
    
    def load_data(self, data_path: str) -> bool:
        """
        Load S&P 500 data from a CSV file.
        
        Args:
            data_path (str): Path to the CSV file.
            
        Returns:
            bool: True if data was loaded successfully, False otherwise.
        """
        try:
            self._dataframe = pd.read_csv(data_path)
            self.companies = self._dataframe.to_dict('records')
            logger.info(f"Loaded {len(self.companies)} S&P 500 companies from {data_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load S&P 500 data from {data_path}: {e}")
            return False
    
    def download_data(self, output_path: Optional[str] = None) -> bool:
        """
        Download current S&P 500 data from Wikipedia.
        
        Args:
            output_path (str, optional): Path to save the downloaded data.
                If None, data is only loaded into memory.
                
        Returns:
            bool: True if data was downloaded successfully, False otherwise.
        """
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        
        try:
            logger.info("Downloading S&P 500 data from Wikipedia...")
            tables = pd.read_html(url)
            df = tables[0]
            
            # Clean up column names
            df.columns = [col.replace('\n', ' ') for col in df.columns]
            
            # Rename columns to match our expected format
            column_mapping = {
                'Symbol': 'Symbol',
                'Security': 'Company Name',
                'GICS Sector': 'GICS Sector',
                'GICS Sub-Industry': 'GICS Sub-Industry',
                'Headquarters Location': 'Headquarters Location',
                'Date first added': 'Date Added to S&P500',
                'CIK': 'CIK',
                'Founded': 'Founded'
            }
            
            # Apply mapping for columns that exist
            rename_dict = {old: new for old, new in column_mapping.items() if old in df.columns}
            df = df.rename(columns=rename_dict)
            
            # Add missing columns with empty values
            for col in column_mapping.values():
                if col not in df.columns:
                    df[col] = ''
            
            # Save data if output_path is provided
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                df.to_csv(output_path, index=False)
                logger.info(f"Saved S&P 500 data to {output_path}")
            
            # Update internal data
            self._dataframe = df
            self.companies = df.to_dict('records')
            self.data_path = output_path
            
            logger.info(f"Downloaded {len(self.companies)} S&P 500 companies")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download S&P 500 data: {e}")
            return False
    
    def get_company_by_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Get company data by ticker symbol.
        
        Args:
            symbol (str): The company's ticker symbol.
            
        Returns:
            dict: Company data or None if not found.
        """
        symbol = symbol.upper()
        for company in self.companies:
            if company['Symbol'] == symbol:
                return company
        logger.warning(f"Company with symbol {symbol} not found in S&P 500 data")
        return None
    
    def get_companies_by_sector(self, sector: str) -> List[Dict]:
        """
        Get companies by sector.
        
        Args:
            sector (str): The GICS sector to filter by.
            
        Returns:
            list: List of company data dictionaries.
        """
        return [company for company in self.companies
                if company['GICS Sector'].lower() == sector.lower()]
    
    def get_sec_filing_url(self, symbol: str, filing_type: str, year: Optional[int] = None) -> Optional[str]:
        """
        Construct the URL for an SEC filing document.
        
        Args:
            symbol (str): The company's ticker symbol.
            filing_type (str): The filing type (e.g., '10-K', '10-Q').
            year (int, optional): The year of the filing. If None, the latest filing is used.
            
        Returns:
            str: The URL of the SEC filing or None if the company or filing was not found.
        """
        company = self.get_company_by_symbol(symbol)
        if not company or not company['CIK']:
            logger.warning(f"Cannot generate URL: Company {symbol} not found or missing CIK")
            return None
        
        cik = company['CIK']
        
        # Pad CIK with leading zeros to 10 digits
        cik_padded = f"{int(cik):010d}"
        
        # Normalize filing type format
        filing_type = filing_type.upper().replace('-', '')
        
        # Construct the base URL for browse filings
        browse_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_padded}&type={filing_type}"
        if year:
            browse_url += f"&dateb={year}1231&datea={year}0101"
        browse_url += "&owner=exclude&count=10"
        
        # This is a simplification. A more robust solution would:
        # 1. Scrape the browse page to find the most recent filing
        # 2. Navigate to the filing detail page
        # 3. Extract the actual document URL
        
        logger.info(f"Generated browse URL for {symbol} {filing_type}: {browse_url}")
        
        return browse_url
    
    def get_all_symbols(self) -> List[str]:
        """
        Get all ticker symbols in the S&P 500 data.
        
        Returns:
            list: List of ticker symbols.
        """
        return [company['Symbol'] for company in self.companies]
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        Get the S&P 500 data as a pandas DataFrame.
        
        Returns:
            DataFrame: The S&P 500 data.
        """
        return self._dataframe.copy() if self._dataframe is not None else pd.DataFrame()
    
    def filter_companies(self, **kwargs) -> List[Dict]:
        """
        Filter companies by any attribute.
        
        Args:
            **kwargs: Key-value pairs to filter by.
            
        Returns:
            list: List of company data dictionaries.
        """
        result = []
        for company in self.companies:
            match = True
            for key, value in kwargs.items():
                if key not in company or company[key] != value:
                    match = False
                    break
            if match:
                result.append(company)
        return result 