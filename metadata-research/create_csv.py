import csv
from openai import OpenAI

# Initialize OpenAI client with OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="your-openai-api-key"  # Replace with your actual API key
)

def process_data_with_llm(input_data):
    prompt = f"""
    Parse the following data into a CSV format with these columns:
    Symbol, Company Name, GICS Sector, GICS Sub-Industry, Headquarters Location, Date Added to S&P500, CIK, Founded

    Here's the data:
    {input_data}

    Please return only the CSV data for this single entry, without any header or additional text or explanation.
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

def count_rows(input_file):
    count = 0
    with open(input_file, 'r') as file:
        for line in file:
            if line.strip() == '|-':
                count += 1
    return count

def create_csv(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['Symbol', 'Company Name', 'GICS Sector', 'GICS Sub-Industry', 'Headquarters Location', 'Date Added to S&P500', 'CIK', 'Founded'])
        
        current_row = ""
        row_count = 0
        for line in infile:
            if line.startswith('|') and not line.startswith('|-'):
                current_row += line
            elif line.strip() == '|-':
                if current_row:
                    csv_data = process_data_with_llm(current_row)
                    for row in csv.reader(csv_data.splitlines()):
                        if len(row) == 8:  # Ensure we have the correct number of columns
                            writer.writerow(row)
                            row_count += 1
                            print(f"Processed row {row_count}: {', '.join(row)}")
                    current_row = ""
        
        # Process any remaining data
        if current_row:
            csv_data = process_data_with_llm(current_row)
            for row in csv.reader(csv_data.splitlines()):
                if len(row) == 8:
                    writer.writerow(row)
                    row_count += 1
                    print(f"Processed row {row_count}: {', '.join(row)}")

    print(f"Total rows processed: {row_count}")

if __name__ == "__main__":
    input_file = 'snp500_cleaned.txt'
    output_file = 'snp500_data.csv'
    
    total_rows = count_rows(input_file)
    print(f"Total rows to process: {total_rows}")
    
    create_csv(input_file, output_file)
    print(f"CSV file '{output_file}' has been created successfully.")