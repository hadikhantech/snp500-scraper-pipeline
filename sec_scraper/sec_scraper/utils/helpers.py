"""
Helper functions for SEC scraper.

This module provides various utility functions used throughout the SEC scraper.
"""

import os
import logging
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Set up logging with the specified level and file.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str, optional): Path to log file. If None, log to console only.
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    handlers = [logging.StreamHandler()]
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    logger.info(f"Logging setup complete. Level: {log_level}, File: {log_file}")

def ensure_dir(directory: str) -> str:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory (str): Directory path
        
    Returns:
        str: The directory path
    """
    directory_path = Path(directory)
    directory_path.mkdir(parents=True, exist_ok=True)
    return str(directory_path)

def save_json(data: Union[Dict, List], filepath: str) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data (dict or list): Data to save
        filepath (str): Path to save the JSON file
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.debug(f"Saved JSON data to {filepath}")

def load_json(filepath: str) -> Union[Dict, List]:
    """
    Load data from a JSON file.
    
    Args:
        filepath (str): Path to the JSON file
        
    Returns:
        dict or list: The loaded data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_company_symbol(symbol: str) -> str:
    """
    Normalize a company symbol.
    
    Args:
        symbol (str): Company symbol
        
    Returns:
        str: Normalized symbol
    """
    # Remove any non-alphanumeric characters and convert to uppercase
    return re.sub(r'[^A-Za-z0-9]', '', symbol).upper()

def normalize_filing_type(filing_type: str) -> str:
    """
    Normalize a filing type.
    
    Args:
        filing_type (str): Filing type
        
    Returns:
        str: Normalized filing type
    """
    # Convert to uppercase and remove hyphens
    return filing_type.upper().replace('-', '')

def get_quarter_from_date(date_str: str) -> int:
    """
    Get the quarter from a date string.
    
    Args:
        date_str (str): Date string (YYYY-MM-DD format)
        
    Returns:
        int: Quarter number (1-4)
    """
    month = int(date_str.split('-')[1])
    return (month - 1) // 3 + 1

def get_current_quarter() -> int:
    """
    Get the current quarter.
    
    Returns:
        int: Current quarter number (1-4)
    """
    now = datetime.now()
    return (now.month - 1) // 3 + 1

def get_current_year() -> int:
    """
    Get the current year.
    
    Returns:
        int: Current year
    """
    return datetime.now().year

def create_output_filename(company_symbol: str, filing_type: str, content_type: str, 
                          year: Optional[int] = None, quarter: Optional[int] = None,
                          output_dir: Optional[str] = None) -> str:
    """
    Create a standardized output filename for scraped content.
    
    Args:
        company_symbol (str): Company symbol
        filing_type (str): Filing type (10-K, 10-Q)
        content_type (str): Content type (text, tables)
        year (int, optional): Filing year
        quarter (int, optional): Filing quarter (for 10-Q)
        output_dir (str, optional): Output directory
        
    Returns:
        str: Output filename
    """
    # Normalize inputs
    company_symbol = normalize_company_symbol(company_symbol)
    filing_type = normalize_filing_type(filing_type)
    
    # Build filename components
    components = [company_symbol.lower(), filing_type.lower()]
    
    # Add year and quarter if provided
    if year:
        components.append(str(year))
    if quarter and filing_type == '10Q':
        components.append(f"q{quarter}")
    
    # Add content type
    components.append(content_type.lower())
    
    # Combine components with underscores
    filename = f"{'_'.join(components)}.txt"
    
    # Add output directory if provided
    if output_dir:
        return os.path.join(ensure_dir(output_dir), filename)
    
    return filename 