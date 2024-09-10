import re

def clean_wikitext(text):
    """Clean and strip wikitext formatting while preserving table structure."""
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

def process_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        in_table = False
        for line in infile:
            if '{{Import style|sticky' in line:
                in_table = True
                continue
            if in_table:
                cleaned_line = clean_wikitext(line)
                if cleaned_line.startswith('|'):
                    outfile.write(cleaned_line + '\n')

    print(f"Processing complete. Output written to {output_file}")

def main():
    input_file = "snp-wiki.txt"
    output_file = "snp500_cleaned.txt"

    print("Processing wikitext...")
    process_file(input_file, output_file)

if __name__ == "__main__":
    main()