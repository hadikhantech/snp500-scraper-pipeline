import requests
import io
from bs4 import BeautifulSoup
import pandas as pd
import re
import logging
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_html(url):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
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

    try:
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        with requests.Session() as session:
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            # Add a delay to respect rate limits
            time.sleep(1) 
            
            response = session.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching URL: {e}")
        return None

def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove hidden XBRL content
    for hidden in soup.find_all('ix:hidden'):
        hidden.decompose()
    
    # Extract visible text content
    text_content = []
    for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        if tag.name.startswith('h'):
            text_content.append(f"\n\n{tag.text.strip().upper()}\n")
        else:
            text_content.append(tag.text.strip())
    
    # Extract tables with titles
    tables = []
    for table in soup.find_all('table'):
        title = ""
        prev_tag = table.find_previous(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if prev_tag:
            title = prev_tag.text.strip()
        df = pd.read_html(io.StringIO(str(table)))[0]
        tables.append((title, df))
    
    return "\n".join(text_content), tables

def clean_table(df):
    # Remove rows and columns with all NaN values
    df = df.dropna(how='all').dropna(axis=1, how='all')
    
    # Replace remaining NaN values with empty strings
    df = df.fillna('')
    
    # Clean column names
    df.columns = [str(col).strip() for col in df.columns]
    
    return df

def format_table(df, title):
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
    
    # Combine all parts
    table_str = f"{title}\n\n{header}\n{separator}\n" + '\n'.join(rows)
    
    return table_str

def process_tables(tables):
    processed_tables = []
    for title, df in tables:
        df = clean_table(df)
        table_str = format_table(df, title)
        processed_tables.append(table_str)
    return processed_tables

def clean_text(text_content):
    # Remove extra whitespace
    cleaned_text = ' '.join(text_content.split())
    
    # Remove special characters and normalize spaces
    cleaned_text = re.sub(r'[^\w\s]', ' ', cleaned_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    
    # Capitalize first letter of sentences
    cleaned_text = '. '.join(s.capitalize() for s in cleaned_text.split('. '))
    
    return cleaned_text

def scrape_sec_filing(url):
    html_content = fetch_html(url)
    if not html_content:
        return None, None

    text_content, tables = parse_html(html_content)
    cleaned_text = clean_text(text_content)
    processed_tables = process_tables(tables)

    return cleaned_text, processed_tables

def save_text(text, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    logging.info(f"Text content saved to {filename}")

def save_tables(tables, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(tables))
    logging.info(f"Table content saved to {filename}")

def main():
    url = "https://www.sec.gov/Archives/edgar/data/789019/000095017023035122/msft-20230630.htm"
    
    try:
        html_content = fetch_html(url)
        if html_content:
            text_content, tables = parse_html(html_content)
            cleaned_text = clean_text(text_content)
            processed_tables = process_tables(tables)
            
            save_text(cleaned_text, "msft_10k_text.txt")
            save_tables(processed_tables, "msft_10k_tables.txt")
            logging.info("Scraping completed successfully")
        else:
            logging.error("Failed to scrape the SEC filing")
    
    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}")

if __name__ == "__main__":
    main()