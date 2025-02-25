import argparse
import pandas as pd
from openpyxl import load_workbook

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
        columns_to_extract = ["Customer", "Employee", "REG HRS", "B/R", "OT HRS", "OT B/R"]

        # Check if all required columns exist
        missing_columns = [col for col in columns_to_extract if col not in df.columns]
        if missing_columns:
            print(f"Error: Missing columns: {missing_columns}")
            return

        # Strip any leading/trailing whitespace from column values
        df["Customer"] = df["Customer"].astype(str).str.strip()

        # Select only the required columns
        filtered_df = df[columns_to_extract].copy()

        # Add the invoice details as new columns
        filtered_df["*InvoiceNo"] = invoice_no
        filtered_df["*ItemTaxCode"] = item_tax_code
        filtered_df["*InvoiceDate"] = invoice_date
        filtered_df["*DueDate"] = due_date
        filtered_df["Terms"] = terms

        # Rename columns
        filtered_df.rename(columns={"Customer": "*Customer", "B/R": "Rate", "REG HRS": "Hours"}, inplace=True)

        # Remove rows where Hours is empty or NaN
        filtered_df = filtered_df.dropna(subset=["Hours"])

        # Ensure "Rate", "Hours", "OT HRS", and "OT B/R" are numeric
        filtered_df["Rate"] = pd.to_numeric(filtered_df["Rate"], errors="coerce")
        filtered_df["Hours"] = pd.to_numeric(filtered_df["Hours"], errors="coerce")
        filtered_df["OT HRS"] = pd.to_numeric(filtered_df["OT HRS"], errors="coerce")
        filtered_df["OT B/R"] = pd.to_numeric(filtered_df["OT B/R"], errors="coerce")

        # Drop rows where either Rate or Hours is NaN (to avoid multiplication errors)
        filtered_df = filtered_df.dropna(subset=["Rate", "Hours"])

        # Calculate total cost for regular hours
        filtered_df["Amount"] = (filtered_df["Hours"] * filtered_df["Rate"]).round(2)

        # Create a list to store new rows with overtime entries
        new_rows = []

        # Iterate through each row to add an "Overtime" row if needed
        for _, row in filtered_df.iterrows():
            new_rows.append(row)  # Add the original row

            # If OT HRS exists and is greater than 0, create an overtime row
            if row["OT HRS"] > 0:
                overtime_row = row.copy()
                overtime_row["Employee"] = "Overtime"  # Change employee name to 'Overtime'
                overtime_row["Hours"] = row["OT HRS"]  # Use overtime hours
                overtime_row["Rate"] = row["OT B/R"]   # Use overtime rate
                overtime_row["Amount"] = round(overtime_row["Hours"] * overtime_row["Rate"], 2) \
                    if pd.notnull(overtime_row["Hours"]) and pd.notnull(overtime_row["Rate"]) else None
                new_rows.append(overtime_row)  # Add new overtime row

        # Convert the list of new rows back to a DataFrame
        final_df = pd.DataFrame(new_rows)

        # Remove overtime columns since they are now separate rows
        final_df.drop(columns=["OT HRS", "OT B/R"], inplace=True)

        # Specify the desired column order
        column_order = ["*InvoiceNo", "*Customer", "*InvoiceDate", "*DueDate", "Terms", "Employee", "Hours", "Rate",
                        "*ItemTaxCode", "Amount"]

        # Reorder the DataFrame
        final_df = final_df[column_order]

        # Check if any data was found
        if final_df.empty:
            print("No records found in the input file.")
            return

        # Save the filtered and reordered data to Excel
        final_df.to_excel(output_file, index=False, sheet_name="All Companies")

        # Open the saved file using openpyxl to adjust row height and column width
        wb = load_workbook(output_file)
        ws = wb.active

        # Adjust column width based on content length
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter  # Get the column name
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except Exception as e:
                    print(f"Error adjusting column width: {e}")
                    continue
            adjusted_width = max_length + 2  # Add some padding
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
    parser.add_argument("invoice_no", help="Invoice number to add to the output data")
    parser.add_argument("invoice_date", help="Invoice date to keep track of date invoiced")
    parser.add_argument("due_date", help="Invoice due date")
    parser.add_argument("terms", help="Terms for payment or other conditions")
    parser.add_argument("item_tax_code", help="Allow for update of the tax code")

    args = parser.parse_args()

    process_excel(args.input_file, args.output_file, args.invoice_no, args.invoice_date, args.due_date, args.terms, args.item_tax_code)
