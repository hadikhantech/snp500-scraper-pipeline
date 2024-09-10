import os
import subprocess
import tempfile

def convert_wikitext_to_markdown(input_file, output_file):
    """Convert Wikitext to Markdown using Pandoc."""
    try:
        # Create a temporary file for intermediate conversion
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.wiki') as temp_file:
            # Read the input file and write to the temporary file
            with open(input_file, 'r', encoding='utf-8') as infile:
                temp_file.write(infile.read())
            temp_file_name = temp_file.name

        # Run Pandoc to convert Wikitext to Markdown
        subprocess.run([
            'pandoc',
            '--from=mediawiki',
            '--to=markdown_strict',
            temp_file_name,
            '-o', output_file
        ], check=True)

        print(f"Conversion complete. Output written to {output_file}")

    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up the temporary file
        if 'temp_file_name' in locals():
            os.unlink(temp_file_name)

def main():
    input_file = "snp-wiki.txt"
    output_file = "snp500_markdown_test_1.md"

    print("Converting Wikitext to Markdown...")
    convert_wikitext_to_markdown(input_file, output_file)

if __name__ == "__main__":
    main()