import csv
from openai import OpenAI

# Initialize OpenAI client with OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

def process_data_with_llm(input_data):
    prompt = f"""
    Parse the following data into a CSV format with these columns:
    Symbol, Company Name, GICS Sector, GICS Sub-Industry, Headquarters Location, Date Added to S&P500, CIK, Founded

    Then, add the following columns and populate them based on the company's characteristics:
    Market Cap Category (Large, Mid, Small), Dividend Yield Category (High, Medium, Low, None), Region (North America, Europe, Asia, Global etc.), Country of Incorporation, Exchange Listed (NYSE, NASDAQ), Company Category (Startup, Established, Legacy), Employee Count Range (Small, Medium, Large), Revenue Range (Small, Medium, Large), Ownership Type (Public, Private, Family-owned), ESG Rating Category, B2B/B2C, Product Type (Hardware, Software, Services, etc.), Top Products (comma-separated list), Market Share Category (Leader, Challenger, Niche), Number of Patents

    Here's the data:
    {input_data}

    Please return only the CSV data for this single entry, including both the original and new fields, without any header or additional text or explanation.
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
    return completion.choices[0].message.content.strip()

def create_extended_csv(input_file, output_file, max_rows=20):  # Changed max_rows to 20
    input_header = ['Symbol', 'Company Name', 'GICS Sector', 'GICS Sub-Industry', 'Headquarters Location', 'Date Added to S&P500', 'CIK', 'Founded']
    output_header = input_header + [
        'Market Cap Category', 'Dividend Yield Category', 'Region', 'Country of Incorporation', 'Exchange Listed',
        'Company Category', 'Employee Count Range', 'Revenue Range', 'Ownership Type', 'ESG Rating Category',
        'B2B/B2C', 'Product Type', 'Top Products', 'Market Share Category', 'Number of Patents'
    ]

    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # Write the header
        writer.writerow(output_header)
        
        # Skip the header in the input file
        next(reader, None)
        
        for row_count, row in enumerate(reader, 1):
            if row_count > max_rows:
                break
            
            input_data = ','.join(row)
            extended_data = process_data_with_llm(input_data)
            
            for extended_row in csv.reader([extended_data]):
                if len(extended_row) == len(output_header):
                    writer.writerow(extended_row)
                    print(f"Processed row {row_count}: {', '.join(extended_row)}")
                else:
                    print(f"Skipped row {row_count} due to incorrect number of columns")

    print(f"Total rows processed: {row_count - 1}")  # Subtract 1 to account for the header

if __name__ == "__main__":
    input_file = 'snp500_data.csv'
    output_file = 'snp500_extended_data.csv'
    
    create_extended_csv(input_file, output_file, max_rows=20)  # Changed max_rows to 20
    print(f"CSV file '{output_file}' has been created successfully.")