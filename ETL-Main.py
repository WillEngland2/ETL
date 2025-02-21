import argparse
import pandas as pd
import os

def process_excel(input_file, output_file):
    # Validate file extension
    if not (input_file.endswith(".xlsx") or input_file.endswith(".xls")):
        print("Error: The input file must be an Excel file (.xlsx or .xls).")
        return

    try:
        # Read Excel file
        df = pd.read_excel(input_file)

        # Process the data (for now, just copying it)
        df.to_excel(output_file, index=False)

        print(f"Processed file saved as: {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process an Excel file and generate a new one.")
    parser.add_argument("input_file", help="Path to the input Excel file")
    parser.add_argument("output_file", help="Path to save the output Excel file")

    args = parser.parse_args()

    process_excel(args.input_file, args.output_file)
