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

def clean_label(label):
    # Remove any newlines and extra spaces
    label = ' '.join(label.split())
    # Remove any trailing colons or periods
    label = label.rstrip(':.')
    # Limit the length of the label
    return label[:100] if len(label) > 100 else label

def find_table_label(table):
    label = None
    
    # Check for caption
    caption = table.find('caption')
    if caption and caption.text.strip():
        label = clean_label(caption.text)
        logging.info(f"Label found in caption: {label}")
        return label
    
    # Check for preceding paragraph with bold or strong text
    prev_p = table.find_previous('p')
    if prev_p:
        bold = prev_p.find(['b', 'strong'])
        if bold and bold.text.strip():
            label = clean_label(bold.text)
            logging.info(f"Label found in preceding bold text: {label}")
            return label
    
    # Check for preceding headings (up to 3 levels up)
    for i, heading in enumerate(table.find_all_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])):
        if heading.text.strip():
            label = clean_label(heading.text)
            logging.info(f"Label found in preceding heading: {label}")
            return label
        if i >= 2:  # Only check up to 3 levels up
            break
    
    # Check for a div with a specific class that might contain the title
    parent_div = table.find_parent('div', class_='table-title')
    if parent_div:
        label = clean_label(parent_div.text)
        logging.info(f"Label found in parent div: {label}")
        return label
    
    # Check for any preceding text within a certain distance
    prev_tags = table.find_all_previous(['p', 'span', 'div'], limit=3)
    for tag in prev_tags:
        if tag.text.strip():
            label = clean_label(tag.text)
            logging.info(f"Label found in preceding text: {label}")
            return label
    
    # If no label found, use the first row of the table if it looks like a header
    first_row = table.find('tr')
    if first_row and not first_row.find('td') and first_row.find('th'):
        label = clean_label(' '.join(th.text.strip() for th in first_row.find_all('th')))
        logging.info(f"Label constructed from table header: {label}")
        return label
    
    logging.warning("No label found for table, using default.")
    return "Unlabeled Table"

def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove hidden XBRL content
    for hidden in soup.find_all('ix:hidden'):
        hidden.decompose()
    
    # Extract visible text content with structure
    content = []
    for tag in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span']):
        if tag.name.startswith('h'):
            content.append(f"\n\n{tag.name.upper()}: {tag.text.strip()}\n")
        elif tag.name in ['p', 'div', 'span']:
            # Check if this tag is not just whitespace and not part of a table
            if tag.text.strip() and not tag.find_parent('table'):
                content.append(tag.text.strip())
    
    # Extract tables with labels
    tables = []
    for table in soup.find_all('table'):
        label = find_table_label(table)
        try:
            df = pd.read_html(io.StringIO(str(table)))[0]
            tables.append((label, df))
        except Exception as e:
            logging.warning(f"Failed to parse table: {e}")
            continue
    
    return "\n".join(content), tables


def clean_table(df):
    # Remove rows and columns with all NaN values
    df = df.dropna(how='all').dropna(axis=1, how='all')
    
    # Replace remaining NaN values with empty strings
    df = df.fillna('')
    
    # Clean column names
    df.columns = [str(col).strip() for col in df.columns]
    
    return df

def format_table(df, label):
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

def process_tables(tables):
    processed_tables = []
    for label, df in tables:
        if df.empty:
            logging.warning(f"Skipping empty table: {label}")
            continue
        df = clean_table(df)
        table_str = format_table(df, label)
        processed_tables.append(table_str)
    return processed_tables

def clean_text(text_content):
    # Remove extra whitespace within lines
    cleaned_text = re.sub(r'\s+', ' ', text_content)
    
    # Normalize spaces around punctuation
    cleaned_text = re.sub(r'\s*([.,;:!?])\s*', r'\1 ', cleaned_text)
    
    # Remove repeated newlines
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    # Remove page numbers and other common artifacts
    cleaned_text = re.sub(r'\n\s*\d+\s*\n', '\n', cleaned_text)
    
    return cleaned_text

def format_text(text_content):
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

def scrape_sec_filing(url):
    html_content = fetch_html(url)
    if not html_content:
        return None, None

    text_content, tables = parse_html(html_content)
    cleaned_text = clean_text(text_content)
    formatted_text = format_text(cleaned_text)
    processed_tables = process_tables(tables)

    return formatted_text, processed_tables

def save_text(text, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    logging.info(f"Text content saved to {filename}")

def save_tables(tables, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(tables))
    logging.info(f"Table content saved to {filename}")

def main():
    
    #MSFT 10K
    url = "https://www.sec.gov/Archives/edgar/data/789019/000095017023035122/msft-20230630.htm"
    
    #MSFT 10Q
    #url = "https://www.sec.gov/Archives/edgar/data/789019/000095017023014423/msft-20230331.htm"
    
    #NVDA 10K
    #url = "https://www.sec.gov/Archives/edgar/data/1045810/000104581022000036/nvda-20220130.htm"
    
    #AAPL 10k
    #url = "https://www.sec.gov/Archives/edgar/data/320193/000032019318000145/a10-k20189292018.htm"

    try:
        html_content = fetch_html(url)
        if html_content:
            try:
                formatted_text, processed_tables = scrape_sec_filing(url)
                save_text(formatted_text, "msft_10k_text.txt")
                save_tables(processed_tables, "msft_10k_tables.txt")
                logging.info("Scraping completed successfully")
            except Exception as e:
                logging.error(f"An error occurred during scraping: {str(e)}")
                logging.error(f"Error details: {traceback.format_exc()}")
        else:
            logging.error("Failed to fetch HTML content")
    
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        logging.error(f"Error details: {traceback.format_exc()}")

if __name__ == "__main__":
    main()