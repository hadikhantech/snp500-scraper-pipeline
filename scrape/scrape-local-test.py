import os
import requests
from bs4 import BeautifulSoup
import re
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Check if CUDA is available and set the device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logging.info(f"Using device: {device}")

# Initialize the model and tokenizer
checkpoint = "jinaai/reader-lm-1.5b"
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
model = AutoModelForCausalLM.from_pretrained(checkpoint).to(device)

def fetch_and_preprocess_html(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Company Name [email protected]) Company Name Research Project',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        logging.info(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        logging.info("Preprocessing HTML content")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for tag in soup(['script', 'style', 'meta', 'svg']):
            tag.decompose()
        
        text_content = soup.get_text(separator=' ', strip=True)
        cleaned_content = re.sub(r'\s+', ' ', text_content).strip()
        
        logging.info(f"Preprocessed content length: {len(cleaned_content)} characters")
        return cleaned_content
    except Exception as e:
        logging.error(f"Error fetching and preprocessing HTML content from URL {url}: {e}")
        return None

def html_to_markdown(html_content, max_chunk_length=1000):
    try:
        chunks = [html_content[i:i+max_chunk_length] for i in range(0, len(html_content), max_chunk_length)]
        logging.info(f"Split content into {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            logging.info(f"Processing chunk {i+1}/{len(chunks)}")
            inputs = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            logging.info(f"Generating markdown for chunk {i+1}")
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.7,
                    do_sample=True,
                    repetition_penalty=1.08
                )
            
            markdown_chunk = tokenizer.decode(outputs[0], skip_special_tokens=True)
            logging.info(f"Chunk {i+1} processed. Output length: {len(markdown_chunk)} characters")
            yield markdown_chunk
    except Exception as e:
        logging.error(f"Error converting HTML to Markdown: {e}")
        yield None

def process_url(url):
    html_content = fetch_and_preprocess_html(url)
    if html_content:
        return html_to_markdown(html_content)
    return None

def main():
    url = "https://www.sec.gov/Archives/edgar/data/789019/000095017023035122/msft-20230630.htm"
    logging.info("Starting URL processing")
    
    markdown_chunks = process_url(url)
    if markdown_chunks:
        logging.info("Markdown conversion in progress")
        with open("msft-10k.md", "w", encoding="utf-8") as f:
            for i, chunk in enumerate(markdown_chunks):
                if chunk:
                    print(f"\nChunk {i+1}:")
                    print(chunk[:100])  # Print first 100 characters of each chunk
                    print("...")
                    f.write(chunk + "\n")
                    logging.info(f"Chunk {i+1} written to file")
                else:
                    logging.warning(f"Chunk {i+1} processing failed")
        logging.info("Markdown conversion completed and saved to msft-10k.md")
    else:
        logging.info("Failed to process the URL")

if __name__ == "__main__":
    main()