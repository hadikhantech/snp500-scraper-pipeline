import os
import time
from huggingface_hub import InferenceClient
import requests
from bs4 import BeautifulSoup
import re
import logging
import time
import random
from playwright.sync_api import sync_playwright

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize the Inference Client
api_key = os.environ.get("HUGGINGFACE_API_KEY")
client = InferenceClient("jinaai/reader-lm-1.5b", token=api_key)

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import logging
import re
import time
import random

def fetch_and_preprocess_html(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Company Name [email protected]) Company Name Research Project',
                'Accept-Language': 'en-US,en;q=0.9',
            })
            
            # Add a random delay between requests
            time.sleep(random.uniform(1, 3))
            
            page.goto(url, wait_until="networkidle")
            html_content = page.content()
            browser.close()
        
        # Preprocess the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted tags
        for tag in soup(['meta', 'script', 'svg']):
            tag.decompose()
        
        # Extract text content
        text_content = soup.get_text(separator=' ', strip=True)
        
        # Remove extra whitespace
        cleaned_content = re.sub(r'\s+', ' ', text_content).strip()
        
        return cleaned_content
    except Exception as e:
        logging.error(f"Error fetching and preprocessing HTML content from URL {url}: {e}")
        return None
    
def html_to_markdown(html_content):
    try:
        response = client.text_generation(
            html_content,
            max_new_tokens=131072,
            temperature=0,
            do_sample=False,
            repetition_penalty=1.08
        )
        return response
    except Exception as e:
        logging.error(f"Error converting HTML to Markdown: {e}")
        return None

def process_url(url):
    html_content = fetch_and_preprocess_html(url)
    if html_content:
        markdown_content = html_to_markdown(html_content)
        return markdown_content
    return None

# Example usage
url = "https://www.sec.gov/Archives/edgar/data/789019/000095017023035122/msft-20230630.htm"
markdown_result = process_url(url)

if markdown_result:
    print(markdown_result)
    # Optionally, save to file
    with open("msft-10k.md", "w") as f:
        f.write(markdown_result)
else:
    print("Failed to process the URL")

# Implement a delay to respect rate limits
time.sleep(1)