"""
SEC Filing Scraper - Core functionality for scraping and parsing SEC filings.
"""

import requests
import io
from bs4 import BeautifulSoup
import pandas as pd
import re
import logging
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import textwrap
import traceback
from pathlib import Path

class SECFilingScraper:
    """
    A class to scrape and parse SEC filings (10-K, 10-Q) from SEC.gov.
    
    This scraper handles both HTML and XBRL formats, extracting text content
    and tables while preserving structure and maintaining table headings.
    """
    
    def __init__(self, user_agent=None, delay=1.0, retries=3):
        """
        Initialize the SEC Filing Scraper.
        
        Args:
            user_agent (str, optional): Custom User-Agent for requests.
            delay (float): Delay between requests to respect SEC.gov rate limits.
            retries (int): Number of retry attempts for failed requests.
        """
        self.delay = delay
        self.retries = retries
        self.headers = {
            "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        
        self.logger = logging.getLogger(__name__)
        
        # Configure retry strategy
        self.retry_strategy = Retry(
            total=self.retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        self.adapter = HTTPAdapter(max_retries=self.retry_strategy)
        
    def fetch_html(self, url):
        """
        Fetch HTML content from a URL with retry logic and rate limiting.
        
        Args:
            url (str): The URL to fetch.
            
        Returns:
            str: The HTML content or None if the request failed.
        """
        try:
            with requests.Session() as session:
                session.mount("https://", self.adapter)
                session.mount("http://", self.adapter)
                
                # Add a delay to respect rate limits
                time.sleep(self.delay) 
                
                response = session.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                return response.text
        except requests.RequestException as e:
            self.logger.error(f"Error fetching URL {url}: {e}")
            return None
    
    def is_xbrl_document(self, html_content):
        """
        Check if the document is in XBRL format.
        
        Args:
            html_content (str): The HTML content to check.
            
        Returns:
            bool: True if the document is in XBRL format, False otherwise.
        """
        return (html_content.lstrip().startswith('<?xml') or 
                '<ix:header' in html_content[:1000] or 
                'xmlns:ix="http://www.xbrl.org/' in html_content[:1000] or
                '<div style="display:none;">' in html_content[:1000])
    
    def clean_label(self, label):
        """
        Clean table label text.
        
        Args:
            label (str): The label to clean.
            
        Returns:
            str: The cleaned label.
        """
        # Remove any newlines and extra spaces
        label = ' '.join(label.split())
        # Remove any trailing colons or periods
        label = label.rstrip(':.')
        # Limit the length of the label
        return label[:100] if len(label) > 100 else label
    
    def find_table_label(self, table):
        """
        Find a suitable label for a table by examining surrounding elements.
        
        Args:
            table (BeautifulSoup): The table element.
            
        Returns:
            str: The table label or "Unlabeled Table" if none is found.
        """
        label = None
        
        # Check for caption
        caption = table.find('caption')
        if caption and caption.text.strip():
            label = self.clean_label(caption.text)
            self.logger.debug(f"Label found in caption: {label}")
            return label
        
        # Check for preceding paragraph with bold or strong text
        prev_p = table.find_previous('p')
        if prev_p:
            bold = prev_p.find(['b', 'strong'])
            if bold and bold.text.strip():
                label = self.clean_label(bold.text)
                self.logger.debug(f"Label found in preceding bold text: {label}")
                return label
        
        # Check for preceding headings (up to 3 levels up)
        for i, heading in enumerate(table.find_all_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])):
            if heading.text.strip():
                label = self.clean_label(heading.text)
                self.logger.debug(f"Label found in preceding heading: {label}")
                return label
            if i >= 2:  # Only check up to 3 levels up
                break
        
        # Check for a div with a specific class that might contain the title
        parent_div = table.find_parent('div', class_='table-title')
        if parent_div:
            label = self.clean_label(parent_div.text)
            self.logger.debug(f"Label found in parent div: {label}")
            return label
        
        # Check for any preceding text within a certain distance
        prev_tags = table.find_all_previous(['p', 'span', 'div'], limit=3)
        for tag in prev_tags:
            if tag.text.strip():
                label = self.clean_label(tag.text)
                self.logger.debug(f"Label found in preceding text: {label}")
                return label
        
        # If no label found, use the first row of the table if it looks like a header
        first_row = table.find('tr')
        if first_row and not first_row.find('td') and first_row.find('th'):
            label = self.clean_label(' '.join(th.text.strip() for th in first_row.find_all('th')))
            self.logger.debug(f"Label constructed from table header: {label}")
            return label
        
        self.logger.warning("No label found for table, using default.")
        return "Unlabeled Table"
    
    def parse_html(self, html_content):
        """
        Parse HTML content to extract text and tables.
        
        Args:
            html_content (str): The HTML content to parse.
            
        Returns:
            tuple: (text_content, tables) where text_content is a string and
                  tables is a list of (label, dataframe) tuples.
        """
        if self.is_xbrl_document(html_content):
            # Remove everything before the <body> tag
            body_start = html_content.find('<body')
            if body_start != -1:
                html_content = html_content[body_start:]
            
            # Remove the hidden div containing XBRL data
            html_content = re.sub(r'<div style="display:none">.*?</div>', '', html_content, flags=re.DOTALL)
            
            # Remove ix: tags
            html_content = re.sub(r'<ix:[^>]*>|</ix:[^>]*>', '', html_content)
        
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove all XBRL-related tags
        for tag in soup.find_all(['ix:nonfraction', 'ix:nonnumeric', 'xbrli:measure', 'ix:hidden']):
            tag.decompose()
        
         # Remove any remaining tags with XBRL-related attributes
        for tag in soup.find_all(attrs={'contextref': True, 'unitref': True, 'decimals': True, 'scale': True}):
            tag.unwrap()

        # Extract visible text content with structure
        content = []
        for tag in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span']):
            if tag.name.startswith('h'):
                content.append(f"\n\n{tag.name.upper()}: {tag.text.strip()}\n")
            elif tag.name in ['p', 'div', 'span']:
                # Check if this tag is not just whitespace, not part of a table, and not XBRL content
                if tag.text.strip() and not tag.find_parent('table') and not tag.get('contextref'):
                    content.append(tag.text.strip())
        
        # Extract tables with labels
        tables = []
        for table in soup.find_all('table'):
            label = self.find_table_label(table)
            try:
                df = pd.read_html(io.StringIO(str(table)))[0]
                tables.append((label, df))
            except Exception as e:
                self.logger.warning(f"Failed to parse table: {e}")
                continue
        
        return "\n".join(content), tables
    
    def clean_table(self, df):
        """
        Clean a table dataframe by removing empty rows/columns and formatting.
        
        Args:
            df (DataFrame): The pandas DataFrame to clean.
            
        Returns:
            DataFrame: The cleaned DataFrame.
        """
        # Remove rows and columns with all NaN values
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Replace remaining NaN values with empty strings
        df = df.fillna('')
        
        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        return df
    
    def format_table(self, df, label):
        """
        Format a DataFrame as a string table with label.
        
        Args:
            df (DataFrame): The pandas DataFrame to format.
            label (str): The table label.
            
        Returns:
            str: The formatted table string.
        """
        # Calculate column widths
        col_widths = [max(df[col].astype(str).map(len).max(), len(col)) for col in df.columns]
        
        # Create header
        header = '| ' + ' | '.join(col.ljust(width) for col, width in zip(df.columns, col_widths)) + ' |'
        separator = '|-' + '-|-'.join('-' * width for width in col_widths) + '-|'
        
        # Create rows
        rows = []
        for _, row in df.iterrows():
            row_str = '| ' + ' | '.join(str(cell).ljust(width) for cell, width in zip(row, col_widths)) + ' |'
            rows.append(row_str)
        
        # Combine all parts with the label
        table_str = f"Table: {label}\n\n{header}\n{separator}\n" + '\n'.join(rows)
        
        return table_str
    
    def process_tables(self, tables):
        """
        Process a list of tables by cleaning and formatting them.
        
        Args:
            tables (list): List of (label, DataFrame) tuples.
            
        Returns:
            list: List of formatted table strings.
        """
        processed_tables = []
        for label, df in tables:
            if df.empty:
                self.logger.warning(f"Skipping empty table: {label}")
                continue
            df = self.clean_table(df)
            table_str = self.format_table(df, label)
            processed_tables.append(table_str)
        return processed_tables
    
    def clean_text(self, text_content):
        """
        Clean extracted text content by removing XBRL artifacts and formatting.
        
        Args:
            text_content (str): The text content to clean.
            
        Returns:
            str: The cleaned text content.
        """
        # Remove XBRL-like content
        cleaned_text = re.sub(r'\d{10}[a-z]+:', '', text_content)
        cleaned_text = re.sub(r'[a-z-]+:[A-Z][a-zA-Z]+', '', cleaned_text)
        cleaned_text = re.sub(r'ix:nonnumeric.*?>', '', cleaned_text)
        cleaned_text = re.sub(r'</?[a-z]+:[a-z]+>', '', cleaned_text)
        
        # Remove extra whitespace within lines
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        # Normalize spaces around punctuation
        cleaned_text = re.sub(r'\s*([.,;:!?])\s*', r'\1 ', cleaned_text)
        
        # Remove repeated newlines
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        # Remove page numbers and other common artifacts
        cleaned_text = re.sub(r'\n\s*\d+\s*\n', '\n', cleaned_text)
        
        return cleaned_text
    
    def format_text(self, text_content):
        """
        Format text content with proper headings and paragraph wrapping.
        
        Args:
            text_content (str): The text content to format.
            
        Returns:
            str: The formatted text content.
        """
        lines = text_content.split('\n')
        formatted_text = []
        
        for line in lines:
            if line.startswith(('H1:', 'H2:', 'H3:', 'H4:', 'H5:', 'H6:')):
                # Format headings
                level, title = line.split(':', 1)
                formatted_text.append(f"\n{'#' * int(level[1:])} {title.strip()}\n")
            else:
                # Wrap paragraphs
                formatted_text.append(textwrap.fill(line.strip(), width=80))
        
        return '\n\n'.join(formatted_text)
    
    def scrape_sec_filing(self, url):
        """
        Scrape an SEC filing from the given URL.
        
        Args:
            url (str): The URL of the SEC filing.
            
        Returns:
            tuple: (text_content, tables) where text_content is the formatted text
                  and tables is a list of formatted table strings.
        """
        html_content = self.fetch_html(url)
        if not html_content:
            return None, None

        text_content, tables = self.parse_html(html_content)
        text_content = self.clean_text(text_content)
        text_content = self.format_text(text_content)
        formatted_tables = self.process_tables(tables)
        
        return text_content, formatted_tables
    
    def save_to_files(self, company_symbol, filing_type, text_content, tables, output_dir=None):
        """
        Save scraped content to files.
        
        Args:
            company_symbol (str): The company's ticker symbol.
            filing_type (str): The filing type (e.g., '10-K', '10-Q').
            text_content (str): The formatted text content.
            tables (list): List of formatted table strings.
            output_dir (str, optional): Directory to save files to. Defaults to current directory.
            
        Returns:
            tuple: (text_file_path, tables_file_path) Paths to the saved files.
        """
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = Path.cwd()
        
        text_filename = output_path / f"{company_symbol.lower()}_{filing_type.lower().replace('-', '')}_text.txt"
        tables_filename = output_path / f"{company_symbol.lower()}_{filing_type.lower().replace('-', '')}_tables.txt"
        
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write(text_content)
            
        with open(tables_filename, 'w', encoding='utf-8') as f:
            f.write('\n\n' + ('-' * 80) + '\n\n'.join(tables))
            
        self.logger.info(f"Saved text content to {text_filename}")
        self.logger.info(f"Saved tables to {tables_filename}")
        
        return text_filename, tables_filename 