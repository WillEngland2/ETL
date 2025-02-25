import argparse
import pandas as pd
from openpyxl import load_workbook
import numpy as np


def process_excel(input_file, output_file, invoice_no, invoice_date, due_date, terms, item_tax_code):
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
        columns_to_extract = ["Customer", "Employee", "REG HRS", "B/R"]  # Ensure "REG HRS" is the actual column name

        # Check if all required columns exist
        missing_columns = [col for col in columns_to_extract if col not in df.columns]
        if missing_columns:
            print(f"Error: Missing columns: {missing_columns}")
            return

        # Strip any leading/trailing whitespace from column values
        df["Customer"] = df["Customer"].str.strip()

        # Select only the required columns
        filtered_df = df[columns_to_extract]

        # Add the invoice details as new columns
        filtered_df["*InvoiceNo"] = invoice_no
        filtered_df["*ItemTaxCode"] = item_tax_code
        filtered_df["*InvoiceDate"] = invoice_date
        filtered_df["*DueDate"] = due_date
        filtered_df["Terms"] = terms

        # Rename columns
        filtered_df["*Customer"] = filtered_df["Customer"]  # Rename "Customer" to "*Customer"
        filtered_df["Rate"] = filtered_df["B/R"]  # Rename "B/R" to "Rate"
        filtered_df["Hours"] = filtered_df["REG HRS"]  # Rename "REG HRS" to "Hours"

        # Remove rows where Hours is empty or NaN
        filtered_df = filtered_df.dropna(subset=["Hours"])

        # Drop unnecessary columns including "B/R"
        filtered_df = filtered_df.drop(columns=["Customer", "REG HRS", "B/R"])

        # Ensure "Rate" and "Hours" are numeric
        filtered_df["Rate"] = pd.to_numeric(filtered_df["Rate"], errors="coerce")
        filtered_df["Hours"] = pd.to_numeric(filtered_df["Hours"], errors="coerce")

        # Drop rows where either Rate or Hours is NaN (to avoid multiplication errors)
        filtered_df = filtered_df.dropna(subset=["Rate", "Hours"])

        # Calculate total cost
        filtered_df["*Total"] = (filtered_df["Hours"] * filtered_df["Rate"]).round(2)

        # Specify the desired column order
        column_order = ["*InvoiceNo", "*Customer", "*InvoiceDate", "*DueDate", "Terms", "Employee", "Hours", "Rate", "*ItemTaxCode", "*Total"]

        # Reorder the DataFrame
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
    parser.add_argument("item_tax_code", help="Allow for update of the tax code")

    args = parser.parse_args()

    process_excel(args.input_file, args.output_file, args.invoice_No, args.invoice_date, args.due_date, args.terms, args.item_tax_code)
