import os
import time
import re

def clean_wikitext(text):
    """Clean and strip wikitext formatting."""
    # Remove table formatting
    text = re.sub(r'^\|\-', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\|', '', text, flags=re.MULTILINE)
    
    # Remove {{NyseSymbol|}} and {{NasdaqSymbol|}} tags
    text = re.sub(r'\{\{(?:Nyse|Nasdaq)Symbol\|([^}]+)\}\}', r'\1', text)
    
    # Extract content from [[]] tags, keeping only the text before the | if present
    text = re.sub(r'\[\[([^]|]+)(?:\|[^]]+)?\]\]', lambda m: m.group(1).split('|')[0], text)
    
    # Remove any remaining {{ }} tags
    text = re.sub(r'\{\{[^}]+\}\}', '', text)
    
    # Remove any HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def chunk_wikitext(file_path, chunk_size=50):
    """Generator to yield chunks of wikitext."""
    with open(file_path, 'r', encoding='utf-8') as file:
        chunk = []
        for line in file:
            if line.strip() == '|-':
                if len(chunk) == chunk_size:
                    yield ''.join(chunk)
                    chunk = []
                chunk.append(line)
            else:
                chunk.append(line)
        if chunk:
            yield ''.join(chunk)

def convert_to_markdown(wikitext):
    """Convert wikitext chunk to markdown table."""
    lines = wikitext.strip().split('\n')
    markdown_lines = []
    
    # Table header
    markdown_lines.append("| Symbol | Security | GICS Sector | GICS Sub-Industry | Headquarters Location | Date added | CIK | Founded |")
    markdown_lines.append("|--------|----------|-------------|-------------------|------------------------|------------|-----|---------|")
    
    for line in lines:
        if line.strip() == '|-':
            continue
        cells = line.strip('|').split('||')
        cells = [cell.strip().replace('{{NyseSymbol|', '').replace('{{NasdaqSymbol|', '').replace('}}', '') for cell in cells]
        markdown_lines.append(f"| {' | '.join(cells)} |")
    
    return '\n'.join(markdown_lines)

def analyze_input_file(input_file, num_lines=20):
    with open(input_file, 'r', encoding='utf-8') as infile:
        print(f"First {num_lines} lines of the input file:")
        for i, line in enumerate(infile):
            if i >= num_lines:
                break
            print(f"{i+1}: {line.strip()}")

def process_chunks(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write("| Symbol | Security | GICS Sector | GICS Sub-Industry | Headquarters Location | Date added | CIK | Founded |\n")
        outfile.write("|--------|----------|-------------|-------------------|------------------------|------------|-----|----------|\n")

        in_table = False
        for line in infile:
            cleaned_line = clean_wikitext(line)
            if '{{Import style|sticky' in cleaned_line:
                in_table = True
                continue
            if in_table and cleaned_line.startswith('|'):
                parts = re.split(r'\s*\|\s*', cleaned_line.strip('|'))
                if len(parts) >= 8:
                    outfile.write(f"| {' | '.join(parts[:8])} |\n")

    print(f"Processing complete. Output written to {output_file}")

def main():
    input_file = "snp-wiki.txt"
    output_file = "snp500_markdown_test_1.md"

    print("Analyzing input file...")
    analyze_input_file(input_file)

    print("\nProcessing wikitext...")
    process_chunks(input_file, output_file)

if __name__ == "__main__":
    main()