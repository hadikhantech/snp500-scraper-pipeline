"""
EDGAR URL Parser - Extracts document URLs from EDGAR browse pages.
"""

import re
import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List, Tuple
import time

logger = logging.getLogger(__name__)

class EdgarURLParser:
    """
    Parser for EDGAR browse pages to extract document URLs.
    
    This class is responsible for extracting the actual document URLs
    from EDGAR browse pages, which are needed to access the filing documents.
    """
    
    def __init__(self, delay: float = 0.1, retries: int = 3):
        """
        Initialize the EDGAR URL parser.
        
        Args:
            delay (float): Delay between requests in seconds.
            retries (int): Number of retries for failed requests.
        """
        self.delay = delay
        self.retries = retries
        self.base_url = "https://www.sec.gov"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
    def get_document_url(self, browse_url: str, filing_type: str) -> Optional[str]:
        """
        Extract the document URL from an EDGAR browse page.
        
        Args:
            browse_url (str): URL of the EDGAR browse page.
            filing_type (str): Type of filing to extract (10-K, 10-Q).
            
        Returns:
            str: URL of the document or None if not found.
        """
        # Normalize filing type
        filing_type = filing_type.upper().replace('-', '')
        
        try:
            # Fetch the browse page
            time.sleep(self.delay)
            response = requests.get(browse_url, headers=self.headers)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find the table with filings
            table = soup.find('table', class_='tableFile')
            if not table:
                logger.warning(f"No filings table found at {browse_url}")
                return None
            
            # Look for the filing type in the table
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    # Check if this is the correct filing type
                    filing_text = cells[0].get_text().strip().upper()
                    if filing_type in filing_text:
                        # Find the document link
                        document_link = None
                        for i, cell in enumerate(cells):
                            links = cell.find_all('a', href=True)
                            for link in links:
                                href = link.get('href')
                                link_text = link.get_text().strip().lower()
                                if 'html' in link_text and '/Archives/' in href:
                                    document_link = href
                                    break
                            if document_link:
                                break
                        
                        if document_link:
                            # Construct the full URL
                            if document_link.startswith('/'):
                                document_url = f"{self.base_url}{document_link}"
                            else:
                                document_url = document_link
                            
                            logger.info(f"Found document URL: {document_url}")
                            return document_url
            
            logger.warning(f"No document link found for {filing_type} at {browse_url}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing EDGAR browse page {browse_url}: {e}")
            return None
    
    def get_multiple_urls(self, browse_url: str, filing_type: str, num_filings: int = 1) -> List[Dict]:
        """
        Extract multiple document URLs from an EDGAR browse page.
        
        Args:
            browse_url (str): URL of the EDGAR browse page.
            filing_type (str): Type of filing to extract (10-K, 10-Q).
            num_filings (int): Number of filings to retrieve.
            
        Returns:
            list: List of dictionaries with document information.
        """
        # Normalize filing type
        filing_type = filing_type.upper().replace('-', '')
        
        results = []
        
        try:
            # Fetch the browse page
            time.sleep(self.delay)
            response = requests.get(browse_url, headers=self.headers)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find the table with filings
            table = soup.find('table', class_='tableFile')
            if not table:
                logger.warning(f"No filings table found at {browse_url}")
                return results
            
            # Look for the filing type in the table
            rows = table.find_all('tr')
            for row in rows:
                if len(results) >= num_filings:
                    break
                    
                cells = row.find_all('td')
                if len(cells) >= 3:
                    # Check if this is the correct filing type
                    filing_text = cells[0].get_text().strip().upper()
                    if filing_type in filing_text:
                        # Extract filing date
                        filing_date = cells[3].get_text().strip() if len(cells) > 3 else ""
                        
                        # Find the document link and description
                        document_link = None
                        document_description = ""
                        
                        # Find the Documents link
                        for i, cell in enumerate(cells):
                            links = cell.find_all('a', href=True)
                            for link in links:
                                href = link.get('href')
                                link_text = link.get_text().strip().lower()
                                if 'documents' in link_text and '/Archives/' in href:
                                    # This is the "Documents" button - follow it to get the actual document
                                    documents_url = f"{self.base_url}{href}" if href.startswith('/') else href
                                    document_link, document_description = self._extract_document_from_documents_page(documents_url)
                                    break
                            if document_link:
                                break
                        
                        if document_link:
                            # Add to results
                            results.append({
                                'url': document_link,
                                'date': filing_date,
                                'type': filing_text,
                                'description': document_description
                            })
            
            if not results:
                logger.warning(f"No document links found for {filing_type} at {browse_url}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error parsing EDGAR browse page {browse_url}: {e}")
            return results
    
    def _extract_document_from_documents_page(self, documents_url: str) -> Tuple[Optional[str], str]:
        """
        Extract the document URL from an EDGAR documents page.
        
        Args:
            documents_url (str): URL of the EDGAR documents page.
            
        Returns:
            tuple: (document_url, description) or (None, "") if not found.
        """
        try:
            # Fetch the documents page
            time.sleep(self.delay)
            response = requests.get(documents_url, headers=self.headers)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find the table with documents
            table = soup.find('table', class_='tableFile')
            if not table:
                logger.warning(f"No documents table found at {documents_url}")
                return None, ""
            
            # Look for the main document (usually the first one with an .htm extension)
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    # Check if this is an HTML document
                    document_text = cells[2].get_text().strip().lower() if len(cells) > 2 else ""
                    if document_text.endswith('.htm') or document_text.endswith('.html'):
                        # Find the document link
                        links = cells[2].find_all('a', href=True) if len(cells) > 2 else []
                        for link in links:
                            href = link.get('href')
                            if href and ('/Archives/' in href or '/archive/' in href.lower()):
                                document_url = f"{self.base_url}{href}" if href.startswith('/') else href
                                description = cells[1].get_text().strip() if len(cells) > 1 else ""
                                logger.info(f"Found document URL: {document_url}")
                                return document_url, description
            
            logger.warning(f"No HTML document link found at {documents_url}")
            return None, ""
            
        except Exception as e:
            logger.error(f"Error parsing EDGAR documents page {documents_url}: {e}")
            return None, "" 