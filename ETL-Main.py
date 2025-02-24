import argparse
import pandas as pd
import os
from openpyxl import load_workbook

def process_excel(input_file, output_file, invoice_No, invoice_date, due_date, terms):
    # Validate file extension
    if not (input_file.endswith(".xlsx") or input_file.endswith(".xls")):
        print("Error: The input file must be an Excel file (.xlsx or .xls).")
        return

    try:
        # Read Excel file
        df = pd.read_excel(input_file)

        # Print all column names for debugging
        print("Columns in the file:", df.columns)

        # Define the columns to extract
        columns_to_extract = ["Customer", "Employee", "REG HRS"]  # Ensure "REG HRS" is the actual column name

        # Check if all required columns exist
        missing_columns = [col for col in columns_to_extract if col not in df.columns]
        if missing_columns:
            print(f"Error: Missing columns: {missing_columns}")
            return

        # Strip any leading/trailing whitespace from column values
        df["Customer"] = df["Customer"].str.strip()

        # Select only the required columns
        filtered_df = df[columns_to_extract]

        # Add the invoice number as a new column
        filtered_df["*InvoiceNo"] = invoice_No

        # Add the invoice date
        filtered_df["*InvoiceDate"] = invoice_date

        # Add the Due Date
        filtered_df["*DueDate"] = due_date

        # Add the Terms
        filtered_df["Terms"] = terms

        # Rename Company Column to *Customer
        filtered_df["*Customer"] = filtered_df["Customer"]

        # Rename the REG HRS column to *Hours
        filtered_df["Hours"] = filtered_df["REG HRS"]

        # Remove rows where *Hours is empty or NaN
        filtered_df = filtered_df.dropna(subset=["Hours"])

        # Specify the desired column order
        column_order = ["*InvoiceNo", "*Customer", "*InvoiceDate", "*DueDate", "Terms", "Employee", "Hours"]

        # Drop the original 'Customer' and 'REG HRS' columns
        filtered_df = filtered_df.drop(columns=["Customer", "REG HRS"])

        # Reorder the DataFrame based on the specified order
        filtered_df = filtered_df[column_order]

        # Check if any data was found
        if filtered_df.empty:
            print("No records found in the input file.")
            return

        # Save the filtered and reordered data to Excel in a single sheet
        filtered_df.to_excel(output_file, index=False, sheet_name="All Companies")

        # Open the saved file using openpyxl to adjust row height and column width
        wb = load_workbook(output_file)
        ws = wb.active

        # Adjust column width for all columns based on the content length
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter  # Get the column name
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)  # Add some padding to the content width
            ws.column_dimensions[column].width = adjusted_width

        # Save the adjusted Excel file
        wb.save(output_file)

        print(f"Processed file saved as: {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract employees for all companies from an Excel file.")
    parser.add_argument("input_file", help="Path to the input Excel file")
    parser.add_argument("output_file", help="Path to save the extracted data")
    parser.add_argument("invoice_No", help="Invoice number to add to the output data")
    parser.add_argument("invoice_date", help="Invoice date to keep track of date invoiced")
    parser.add_argument("due_date", help="Invoice date to keep track of due date")
    parser.add_argument("terms", help="Terms for payment or other conditions")

    args = parser.parse_args()

    process_excel(args.input_file, args.output_file, args.invoice_No, args.invoice_date, args.due_date, args.terms)
