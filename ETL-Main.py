import argparse
import pandas as pd

def process_excel(input_file, output_file, invoice_date, due_date, terms, item_tax_code):
    if not (input_file.endswith(".xlsx") or input_file.endswith(".xls")):
        print("Error: The input file must be an Excel file (.xlsx or .xls).")
        return

    try:
        # Read Excel file
        df = pd.read_excel(input_file)

        # Define the columns to extract
        columns_to_extract = ["Customer", "Employee", "REG HRS", "B/R", "OT HRS", "OT B/R", "Inv Num"]

        # Check if all required columns exist
        missing_columns = [col for col in columns_to_extract if col not in df.columns]
        if missing_columns:
            print(f"Error: Missing columns: {missing_columns}")
            return

        # Strip any leading/trailing whitespace from column values
        for col in columns_to_extract:
            df[col] = df[col].astype(str).str.strip()

        # Remove rows where any of the required columns have NaN or empty values
        df = df.dropna(subset=columns_to_extract)
        df = df[(df["Customer"] != "") & (df["Employee"] != "")]

        # Save cleaned data to CSV before further processing
        df.to_csv(output_file, index=False)

        # Select only the required columns
        filtered_df = df[columns_to_extract].copy()

        # Initialize invoice_no from the first valid "Inv Num" if available
        valid_inv_nums = pd.to_numeric(df["Inv Num"], errors="coerce").dropna().astype(int)
        invoice_no = valid_inv_nums.min() if not valid_inv_nums.empty else 115  # Start at 115 if no valid Inv Num

        current_customer = None
        new_rows = []

        # Iterate through each row
        for _, row in filtered_df.iterrows():
            try:
                inv_num = int(row["Inv Num"]) if pd.notnull(row["Inv Num"]) else None
            except ValueError:
                inv_num = None

            if inv_num is not None:
                invoice_no = inv_num  # Use the existing invoice number directly
            elif current_customer != row["Customer"]:  # Only increment for a new customer
                current_customer = row["Customer"]
                if valid_inv_nums.empty or invoice_no not in valid_inv_nums.values:
                    invoice_no += 1  # Increment only when there are no valid invoice numbers in the data

            row["*InvoiceNo"] = invoice_no  # Assign invoice number

            row["*ItemTaxCode"] = item_tax_code
            row["*InvoiceDate"] = invoice_date
            row["*DueDate"] = due_date
            row["Terms"] = terms

            # Rename columns
            row["*Customer"] = row.pop("Customer")
            row["Rate"] = row.pop("B/R")
            row["Hours"] = row.pop("REG HRS")

            # Convert columns to numeric
            row["Rate"] = pd.to_numeric(row["Rate"], errors="coerce")
            row["Hours"] = pd.to_numeric(row["Hours"], errors="coerce")
            row["OT HRS"] = pd.to_numeric(row.get("OT HRS", 0), errors="coerce")
            row["OT B/R"] = pd.to_numeric(row.get("OT B/R", 0), errors="coerce")

            # Calculate regular amount
            row["Amount"] = round(row["Hours"] * row["Rate"], 2) if pd.notnull(row["Hours"]) \
                                                                    and pd.notnull(row["Rate"]) else None
            new_rows.append(row)

            # Handle overtime rows
            if row["OT HRS"] > 0:
                overtime_row = row.copy()
                overtime_row["Employee"] = "Overtime"
                overtime_row["Hours"] = row["OT HRS"]
                overtime_row["Rate"] = row["OT B/R"]
                overtime_row["Amount"] = round(overtime_row["Hours"] * overtime_row["Rate"], 2) \
                    if pd.notnull(overtime_row["Hours"]) and pd.notnull(overtime_row["Rate"]) else None
                new_rows.append(overtime_row)

        # Convert to DataFrame
        final_df = pd.DataFrame(new_rows)

        # Remove overtime columns
        final_df.drop(columns=["OT HRS", "OT B/R"], inplace=True)

        # Reorder columns
        column_order = ["*InvoiceNo", "*Customer", "*InvoiceDate", "*DueDate", "Terms", "Employee", "Hours", "Rate", "*ItemTaxCode", "Amount"]
        final_df = final_df[column_order]

        # Drop rows with NaN values
        final_df.dropna(inplace=True)

        if final_df.empty:
            print("No records found in the input file.")
            return

        # Save final data to CSV
        final_df.to_csv(output_file, index=False)
        print("output saved to" ,output_file)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract employees for all companies from an Excel file.")
    parser.add_argument("input_file", help="Path to the input Excel file")
    parser.add_argument("output_file", help="Path to save the extracted data")
    parser.add_argument("invoice_date", help="Invoice date to keep track of date invoiced")
    parser.add_argument("due_date", help="Invoice due date")
    parser.add_argument("terms", help="Terms for payment or other conditions")
    parser.add_argument("item_tax_code", help="Allow for update of the tax code")

    args = parser.parse_args()

    process_excel(args.input_file, args.output_file, args.invoice_date, args.due_date, args.terms, args.item_tax_code)
