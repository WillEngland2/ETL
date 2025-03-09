import argparse
import pandas as pd

def process_excel(extracted_file, output_file, invoice_date, due_date, terms, item_tax_code):
    """
    Reads the extracted employee data, assigns invoice numbers,
    processes overtime, and saves the final formatted output.
    """
    try:
        df = pd.read_excel(extracted_file)

        # Initialize invoice numbers
        df["Inv Num"] = pd.to_numeric(df["Inv Num"], errors="coerce")
        invoice_no = df["Inv Num"].min() - 2 if df["Inv Num"].notna().any() else 115

        new_rows = []
        current_customer = None

        for _, row in df.iterrows():
            if pd.isna(row["Customer"]) or row["Customer"] == "":
                continue

            inv_num = row["Inv Num"] if pd.notna(row["Inv Num"]) else None
            if inv_num is not None:
                invoice_no = int(inv_num)
            elif current_customer != row["Customer"]:
                current_customer = row["Customer"]
                invoice_no += 1

            row["*InvoiceNo"] = invoice_no
            row["*ItemTaxCode"] = item_tax_code
            row["*InvoiceDate"] = invoice_date
            row["*DueDate"] = due_date
            row["Terms"] = terms
            row["*Customer"] = row["Customer"]
            row["Rate"] = pd.to_numeric(row["B/R"], errors="coerce")
            row["Hours"] = pd.to_numeric(row["REG HRS"], errors="coerce")
            row["Amount"] = round(row["Hours"] * row["Rate"], 2) if pd.notna(row["Hours"]) and pd.notna(row["Rate"]) else None

            new_rows.append(row)

            if row.get("OT HRS", 0) > 0:
                overtime_row = row.copy()
                overtime_row["Employee"] = "Overtime"
                overtime_row["Hours"] = row["OT HRS"]
                overtime_row["Rate"] = row["OT B/R"]
                overtime_row["Amount"] = round(overtime_row["Hours"] * overtime_row["Rate"], 2) if pd.notna(overtime_row["Hours"]) and pd.notna(overtime_row["Rate"]) else None
                new_rows.append(overtime_row)

        final_df = pd.DataFrame(new_rows).drop(columns=["OT HRS", "OT B/R"], errors="ignore")
        column_order = ["*InvoiceNo", "*Customer", "*InvoiceDate", "*DueDate", "Terms", "Employee", "Hours", "Rate", "*ItemTaxCode", "Amount"]
        final_df = final_df[column_order].dropna()

        if not final_df.empty:
            final_df.to_csv(output_file, index=False)
            print(f"Final formatted output saved to {output_file}")
        else:
            print("No records found in the extracted file.")
    except Exception as e:
        print(f"An error occurred in process_excel: {e}")

def process_epic(input_file, co_code_output):
    """
    Reads the input Excel file, extracts Co Code, EE ID, Reg Hours, and OT Hours,
    removes invalid EE IDs, fills missing Co Code values, and saves the cleaned data.
    """
    try:
        # Read Excel and standardize column names
        df = pd.read_excel(input_file, dtype={"EE ID": str})
        df.columns = df.columns.str.strip().str.upper()  # Standardize column names

        # Debugging: Print column names to verify correctness
        print("Columns in Excel file:", df.columns)

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
        df["OT HRS"] = df["OT HRS"].fillna(0)

        # Ensure correct column order
        df = df[["CO CODE", "EE ID", "REG HRS", "OT HRS"]]

        # Print all relevant data
        print("Processed Data:")
        for _, row in df.iterrows():
            print(f"Co Code: {row['CO CODE']}, EE ID: {row['EE ID']}, Reg HRS: {row['REG HRS']}, OT HRS: {row['OT HRS']}")

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
