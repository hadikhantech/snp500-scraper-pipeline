import csv
import time
from openai import OpenAI

# Initialize OpenAI client with OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="your-openai-api-key"
)

def process_data_with_llm(input_data):
    prompt = f"""
    Parse the following data into a CSV format with exactly 23 columns. 
    The first 8 columns should be the original data, and the next 15 should be additional information based on the company's characteristics.

    Input data:
    {input_data}

    Format:
    Symbol,Company Name,GICS Sector,GICS Sub-Industry,Headquarters Location,Date Added to S&P500,CIK,Founded,1. Market Cap Category,2. Dividend Yield Category,3. Region,4. Country of Incorporation,5. Exchange Listed,6. Company Category,7. Employee Count Range,8. Revenue Range,9. Ownership Type,10. ESG Rating Category,11. B2B/B2C,12. Product Type,13. Top Products,14. Market Share Category,15. Number of Patents

    Rules:
    1. Use the exact column names provided.
    2. For the additional 15 columns, use these specific categories:
       1. Market Cap Category: Large, Mid, or Small
       2. Dividend Yield Category: High, Medium, Low, or None
       3. Region: North America, Europe, Asia, or Global
       4. Country of Incorporation: Full country name
       5. Exchange Listed: NYSE or NASDAQ
       6. Company Category: Startup, Established, or Legacy
       7. Employee Count Range: Small, Medium, or Large
       8. Revenue Range: Small, Medium, or Large
       9. Ownership Type: Public, Private, or Family-owned
       10. ESG Rating Category: High, Medium, or Low
       11. B2B/B2C: B2B, B2C, or B2B/B2C
       12. Product Type: Hardware, Software, Services, or a combination
       13. Top Products: Comma separated list upto 3, do not use nouns, only the category, example: "Adhesives, Abrasives, Personal Protective Equipment" (note: Make sure to output this in double inverted commmas) 
       14. Market Share Category: Leader, Challenger, or Niche
       15. Number of Patents: Estimate as a range (e.g., 100-500, 1000+)

    Example output:
    MMM,3M,Industrials,Industrial Conglomerates,Saint Paul Minnesota,1957-03-04,0000066740,1902,Large,Medium,North America,United States,NYSE,Legacy,Large,Large,Public,Medium,B2B/B2C,Hardware,"Post-it Notes, Scotch Tape, N95 Respirators",Leader,10000+
    ABT, Abbott Laboratories, Health Care, Health Care Equipment, North Chicago Illinois, 1957-03-04, 0000001800, 1888, Large, Medium, North America, USA, NYSE, Legacy, Large, Large, Public, High, B2B/B2C, Hardware Devices, "Medical Devices, Diagnostics, Nutrition Products", Leader, 10000+
    Please provide the output in exactly this format, with 23 comma-separated values, only return the csv, no additional text or explanation.
    """
    completion = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
            
    extended_row = completion.choices[0].message.content.strip()
    return extended_row

def create_extended_csv(input_file, output_file):
    input_header = ['Symbol', 'Company Name', 'GICS Sector', 'GICS Sub-Industry', 'Headquarters Location', 'Date Added to S&P500', 'CIK', 'Founded']
    output_header = input_header + [
        'Market Cap Category', 'Dividend Yield Category', 'Region', 'Country of Incorporation', 'Exchange Listed',
        'Company Category', 'Employee Count Range', 'Revenue Range', 'Ownership Type', 'ESG Rating Category',
        'B2B/B2C', 'Product Type', 'Top Products', 'Market Share Category', 'Number of Patents'
    ]

    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile, quoting=csv.QUOTE_NONNUMERIC)
        
        # Write the header
        writer.writerow(output_header)
        
        # Skip the header in the input file
        next(reader, None)
        
        for row_count, row in enumerate(reader, 1):
            input_data = ','.join(row)
            extended_data = process_data_with_llm(input_data)
            
            # Use CSV reader to parse the LLM output
            extended_row = next(csv.reader([extended_data]))
            
            writer.writerow(extended_row)
            print(f"Processed row {row_count}: {', '.join(extended_row)}")

    print(f"Total rows processed: {row_count}")

if __name__ == "__main__":
    input_file = 'snp500_data.csv'
    output_file = 'snp500_extended_data.csv'
    
    create_extended_csv(input_file, output_file)
    print(f"CSV file '{output_file}' has been created successfully.")