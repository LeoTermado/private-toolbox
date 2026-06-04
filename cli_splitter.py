"""Standalone command-line PDF splitter.

Preserved from the original run.py. Splits every PDF in an input folder by a
comma-separated set of page ranges.

Usage:
    python cli_splitter.py <input_folder> <output_folder> "<page_ranges>"
Example:
    python cli_splitter.py input output "1-10, 15, 20-25"
"""
import os
import sys

from core.page_range_parser import parse_single_range
from core.pdf_utils import get_page_count, write_pages


def main():
    if len(sys.argv) < 4:
        print("Error: Missing arguments!")
        print('Usage: python cli_splitter.py <input_folder> <output_folder> "<page_ranges>"')
        print('Example: python cli_splitter.py input output "1-10, 15, 20-25"')
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    range_string = sys.argv[3]

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Look for the first PDF in the input folder
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in the '{input_folder}' folder.")
        sys.exit(1)

    for file_name in pdf_files:
        input_file = os.path.join(input_folder, file_name)
        print(f"\nProcessing source file: {file_name}...\n" + "-" * 40)

        total_pages = get_page_count(input_file)

        # Split instructions by the comma
        parts = range_string.split(",")

        for part in parts:
            part = part.strip()  # Clean up any spaces
            if not part:
                continue

            try:
                target_pages = parse_single_range(part, total_pages)
            except ValueError:
                print(f"Skipping invalid format: '{part}'")
                continue

            if not target_pages:
                print(f"Skipping '{part}': No matching pages found in this PDF.")
                continue

            # Name the file exactly after the parameter range (e.g., '1-10.pdf')
            output_filename = os.path.join(output_folder, f"{part}.pdf")
            write_pages(input_file, target_pages, output_filename)

            print(f"Created: {output_filename} ({len(target_pages)} pages)")


if __name__ == "__main__":
    main()
