import argparse
import pandas as pd


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
        df = df[df["Customer"].notna() & (df["Customer"] != "")]

        # Save cleaned data to CSV before further processing
        df.to_csv(output_file, index=False)

        # Select only the required columns
        filtered_df = df[columns_to_extract].copy()

        # Initialize invoice_no from the first valid "Inv Num" if available
        valid_inv_nums = pd.to_numeric(df["Inv Num"], errors="coerce").dropna().astype(int)
        invoice_no = valid_inv_nums.min() - 2 if not valid_inv_nums.empty else 115  # Start at 115 if no valid Inv Num

        current_customer = None
        new_rows = []

        # Iterate through each row
        for _, row in filtered_df.iterrows():
            if pd.isna(row["Customer"]) or row["Customer"] == "":
                continue  # Skip rows with no customer

            # Check if customer has changed, and increment invoice number only if so
            if row["Customer"] != current_customer:
                current_customer = row["Customer"]
                # Only increment the invoice number if it's a new customer
                invoice_no += 1

            try:
                inv_num = int(row["Inv Num"]) if pd.notnull(row["Inv Num"]) else None
            except ValueError:
                inv_num = None

            if inv_num is not None:
                invoice_no = inv_num  # Use the existing invoice number directly

            row["*InvoiceNo"] = invoice_no  # Assign invoice number

            # Add new fields
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
            row["Amount"] = round(row["Hours"] * row["Rate"], 2) if pd.notnull(row["Hours"]) and pd.notnull(row["Rate"]) else None
            new_rows.append(row)

            # Handle overtime rows
            if row["OT HRS"] > 0:
                overtime_row = row.copy()
                overtime_row["Employee"] = "Overtime"
                overtime_row["Hours"] = row["OT HRS"]
                overtime_row["Rate"] = row["OT B/R"]
                overtime_row["Amount"] = round(overtime_row["Hours"] * overtime_row["Rate"], 2) if pd.notnull(overtime_row["Hours"]) and pd.notnull(overtime_row["Rate"]) else None
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
        print("Output saved to", output_file)

    except Exception as e:
        print(f"An error occurred: {e}")

def process_epic(input_file, co_code_output):
    """
    Reads the input Excel file, extracts Co Code, EE ID, Reg Hours, and OT Hours,
    removes invalid EE IDs, fills missing Co Code values, and saves the cleaned data.
    """
    try:
        # Read Excel and standardize column names
        df = pd.read_excel(input_file, dtype={"EE ID": str})
        df.columns = df.columns.str.strip().str.upper()  # Standardize column names

        # Ensure required columns exist
        required_columns = {"CO CODE", "EE ID", "REG HRS", "OT HRS"}
        if not required_columns.issubset(df.columns):
            missing_cols = required_columns - set(df.columns)
            raise ValueError(f"Missing columns in input file: {missing_cols}")

        # Select necessary columns
        df = df[["CO CODE", "EE ID", "REG HRS", "OT HRS"]]

        # Drop fully empty rows
        df.dropna(how="all", inplace=True)

        # Convert EE ID to numeric, setting errors='coerce' will convert invalid entries to NaN
        df["EE ID"] = pd.to_numeric(df["EE ID"], errors="coerce")

        # Drop rows where EE ID is NaN (invalid/missing values)
        df.dropna(subset=["EE ID"], inplace=True)
        df["EE ID"] = df["EE ID"].astype(int)

        # Fill Co Code downward
        df["CO CODE"] = df["CO CODE"].ffill()

        # Fill missing hours with 0
        df["REG HRS"] = df["REG HRS"].fillna(0)
        df["OT HRS"] = pd.to_numeric(df["OT HRS"], errors="coerce").fillna(0)


        # Ensure correct column order
        df = df[["CO CODE", "EE ID", "REG HRS", "OT HRS"]]

        # Save to CSV, appending if the file exists
        df.to_csv(co_code_output, mode='a', header=not pd.io.common.file_exists(co_code_output), index=False)
        print(f"Data saved to {co_code_output}")

    except Exception as e:
        print(f"An error occurred in process_epic: {e}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract employees and Co Code from an Excel file.")
    parser.add_argument("input_file", help="Path to the input Excel file (e.g., inputMain.xlsx)")
    parser.add_argument("output_file", help="Path to save the extracted employee data")
    parser.add_argument("co_code_output", help="Path to save the Co Code extracted data")
    parser.add_argument("invoice_date", help="Invoice date (e.g., 1/4/2025)")
    parser.add_argument("due_date", help="Invoice due date (e.g., 2/3/2025)")
    parser.add_argument("terms", help="Payment terms (e.g., 'Net 30')")
    parser.add_argument("item_tax_code", nargs="?", default="", help="Tax code (optional, default is empty)")

    args = parser.parse_args()
    process_excel(args.input_file, args.output_file, args.invoice_date, args.due_date, args.terms, args.item_tax_code)
    process_epic(args.input_file, args.co_code_output)
