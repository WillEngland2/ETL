import argparse
import pandas as pd

def process_excel(input_file, output_file, invoice_date, due_date, terms, item_tax_code):
    if not (input_file.endswith(".xlsx") or input_file.endswith(".xls")):
        print("Error: The input file must be an Excel file (.xlsx or .xls).")
        return

    try:
        # Read Excel file
        df = pd.read_excel(input_file)

        # Find index of "Separate Invoice"
        separate_invoice_index = df.apply(
            lambda row: row.astype(str).str.contains("Separate Invoice", na=False, case=False)
        ).any(axis=1).idxmax()

        # Separate data into before and after "Separate Invoice"
        if df.apply(
                lambda row: row.astype(str).str.contains("Separate Invoice", na=False, case=False)
        ).any().any():
            df_before = df.iloc[:separate_invoice_index]
            df_after = df.iloc[separate_invoice_index:]  # Data after "Separate Invoice"
        else:
            df_before = df
            df_after = pd.DataFrame()  # If no "Separate Invoice", leave this empty

        # Drop rows where the 'Customer' column contains 'Separate Invoice' before processing
        df_before = df_before[~df_before['Customer'].str.contains("Separate Invoice", na=False, case=False)]
        df_after = df_after[~df_after['Customer'].str.contains("Separate Invoice", na=False, case=False)]

        # Define the columns to extract
        columns_to_extract = ["Customer", "Employee", "REG HRS", "B/R", "OT HRS", "OT B/R", "Inv Num"]

        # Check if all required columns exist in both dataframes
        missing_columns_before = [
            col for col in columns_to_extract if col not in df_before.columns
        ]
        missing_columns_after = [
            col for col in columns_to_extract if col not in df_after.columns
        ]
        if missing_columns_before or missing_columns_after:
            print(f"Error: Missing columns in data: {missing_columns_before + missing_columns_after}")
            return

        # Initialize invoice_no for both dataframes, using the first valid "Inv Num"
        valid_inv_nums = pd.to_numeric(df["Inv Num"], errors="coerce").dropna().astype(int)
        invoice_no = valid_inv_nums.min() - 2 if not valid_inv_nums.empty else 115  # Initialize

        # Process both before and after data
        for data, output in [(df_before, output_file), (df_after, "2" + output_file)]:
            # Strip any leading/trailing whitespace from column values
            for col in columns_to_extract:
                data = data.copy()
                data[col] = data[col].astype(str).str.strip()

            # Remove rows where any of the required columns have NaN or empty values
            data = data.dropna(subset=columns_to_extract)
            data = data[data["Customer"].notna() & (data["Customer"] != "")]  # Remove rows where Customer is NaN or empty

            # Save cleaned data to CSV before further processing
            data.to_csv(output, index=False)

            # Select only the required columns
            filtered_df = data[columns_to_extract].copy()

            # Remove rows with NaN values before assigning invoice number
            filtered_df = filtered_df.dropna(subset=["Customer", "REG HRS", "B/R"])

            current_customer = ""
            new_rows = []

            # Iterate through each row
            for _, row in filtered_df.iterrows():
                customer_name = row["Customer"]

                # Skip rows with "Separate Invoice" in customer name
                if "Separate Invoice" in str(customer_name):
                    print(f"Skipping customer with 'Separate Invoice': {customer_name}")
                    continue  # Skip rows with "Separate Invoice"

                print(f"Checking customer: {customer_name}")

                if pd.isna(customer_name) or customer_name is None or not str(customer_name).strip():
                    print("Skipping row with missing customer.")
                    continue  # Skip rows with no customer

                print(f"Processing customer: {customer_name}")

                # Check if customer has changed, and increment invoice number only if so
                if customer_name != current_customer:
                    current_customer = row["Customer"]
                    invoice_no += 1  # Increment invoice number only if it's a new customer

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
            final_df.to_csv(output, index=False)
            print(f"Output saved to {output}")

    except Exception as e:
        print(f"An error occurred: {e}")

def process_epic(input_file, co_code_output):
    """
    Reads the input Excel file, extracts Co Code, EE ID, Reg Hours, and OT Hours,
    removes invalid EE IDs, removes rows where 'REG HRS' contains 'OFF',
    removes rows where both 'REG HRS' and 'OT HRS' are 0, fills missing Co Code values,
    and saves the cleaned data.
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

        # Remove rows where 'REG HRS' contains 'OFF'
        df = df[~df["REG HRS"].astype(str).str.contains("OFF", case=False, na=False)]

        # Convert EE ID to numeric, setting errors='coerce' will convert invalid entries to NaN
        df["EE ID"] = pd.to_numeric(df["EE ID"], errors="coerce")

        # Drop rows where EE ID is NaN (invalid/missing values)
        df.dropna(subset=["EE ID"], inplace=True)
        df["EE ID"] = df["EE ID"].astype(int)

        # Fill Co Code downward
        df["CO CODE"] = df["CO CODE"].ffill()

        # Convert hours to numeric and fill missing values with 0
        df["REG HRS"] = pd.to_numeric(df["REG HRS"], errors="coerce").fillna(0)
        df["OT HRS"] = pd.to_numeric(df["OT HRS"], errors="coerce").fillna(0)

        # Remove rows where both REG HRS and OT HRS are 0
        df = df[~((df["REG HRS"] == 0) & (df["OT HRS"] == 0))]

        # Ensure correct column order
        df = df[["CO CODE", "EE ID", "REG HRS", "OT HRS"]]

        # Save to CSV, appending if the file exists
        df.to_csv(co_code_output, mode='a', header=not pd.io.common.file_exists(co_code_output), index=False)
        print(f"Data saved to {co_code_output}")

    except Exception as e:
        print(f"An error occurred in process_epic: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract employees and Co Code from an Excel file.")
    parser.add_argument("input_file", help="Path to the input Excel file")
    parser.add_argument("output_file", help="Path to save the extracted employee data")
    parser.add_argument("co_code_output", help="Path to save the Co Code extracted data")
    parser.add_argument("invoice_date", help="Invoice date")
    parser.add_argument("due_date", help="Invoice due date")
    parser.add_argument("terms", help="Payment terms")
    parser.add_argument("item_tax_code", nargs="?", default="", help="Tax code")

    args = parser.parse_args()
    process_excel(args.input_file, args.output_file, args.invoice_date, args.due_date, args.terms, args.item_tax_code)
    process_epic(args.input_file, args.co_code_output)
