import re

def process_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        # Write the table header
        outfile.write("| Symbol | Security | GICS Sector | GICS Sub-Industry | Headquarters Location | Date added | CIK | Founded |\n")
        outfile.write("|--------|----------|-------------|-------------------|------------------------|------------|-----|----------|\n")

        current_row = []
        for line in infile:
            line = line.strip()
            if line.startswith('|'):
                parts = line.split('|')
                parts = [part.strip() for part in parts if part.strip()]
                current_row.extend(parts)

                if len(current_row) >= 8:
                    outfile.write(f"| {' | '.join(current_row[:8])} |\n")
                    current_row = current_row[8:]
            elif line == '|-':
                if current_row:
                    outfile.write(f"| {' | '.join(current_row)} |\n")
                current_row = []

    print(f"Processing complete. Output written to {output_file}")

def main():
    input_file = "snp500_cleaned.txt"
    output_file = "snp500_formatted.md"
    process_file(input_file, output_file)

if __name__ == "__main__":
    main()