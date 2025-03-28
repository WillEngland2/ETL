import pandas as pd
import os

def process_excel(input_file, output_file, invoice_date, due_date, terms, item_tax_code):
    if not (input_file.endswith(".xlsx") or input_file.endswith(".xls")):
        print("Error: The input file must be an Excel file (.xlsx or .xls).")
        return

    try:
        df = pd.read_excel(input_file)

        separate_invoice_index = df.apply(
            lambda row: row.astype(str).str.contains("Separate Invoice", na=False, case=False)
        ).any(axis=1).idxmax()

        if df.apply(lambda row: row.astype(str).str.contains("Separate Invoice", na=False, case=False)).any().any():
            df_before = df.iloc[:separate_invoice_index]
            df_after = df.iloc[separate_invoice_index:]
        else:
            df_before = df
            df_after = pd.DataFrame()

        df_before = df_before[~df_before['Customer'].str.contains("Separate Invoice", na=False, case=False)]
        df_after = df_after[~df_after['Customer'].str.contains("Separate Invoice", na=False, case=False)]

        columns_to_extract = ["Customer", "Employee", "REG HRS", "B/R", "OT HRS", "OT B/R", "Inv Num"]

        missing_columns_before = [col for col in columns_to_extract if col not in df_before.columns]
        missing_columns_after = [col for col in columns_to_extract if col not in df_after.columns]
        if missing_columns_before or missing_columns_after:
            print(f"Error: Missing columns in data: {missing_columns_before + missing_columns_after}")
            return

        valid_inv_nums = pd.to_numeric(df["Inv Num"], errors="coerce").dropna().astype(int)
        invoice_no = valid_inv_nums.min() - 2 if not valid_inv_nums.empty else 115

        second_output_file = os.path.join(os.path.dirname(output_file), "2" + os.path.basename(output_file))
        
        for data, output in [(df_before, output_file), (df_after, second_output_file)]:

            for col in columns_to_extract:
                data = data.copy()
                data[col] = data[col].astype(str).str.strip()

            data = data.dropna(subset=columns_to_extract)
            data = data[data["Customer"].notna() & (data["Customer"] != "")]
            data.to_csv(output, index=False)

            filtered_df = data[columns_to_extract].copy()
            filtered_df = filtered_df.dropna(subset=["Customer", "REG HRS", "B/R"])

            current_customer = ""
            new_rows = []

            for _, row in filtered_df.iterrows():
                customer_name = row["Customer"]

                if "Separate Invoice" in str(customer_name):
                    continue
                if pd.isna(customer_name) or customer_name is None or not str(customer_name).strip():
                    continue

                if customer_name != current_customer:
                    current_customer = row["Customer"]
                    invoice_no += 1

                try:
                    inv_num = int(row["Inv Num"]) if pd.notnull(row["Inv Num"]) else None
                except ValueError:
                    inv_num = None

                if inv_num is not None:
                    invoice_no = inv_num

                row["*InvoiceNo"] = invoice_no
                row["*ItemTaxCode"] = item_tax_code
                row["*InvoiceDate"] = invoice_date
                row["*DueDate"] = due_date
                row["Terms"] = terms

                row["*Customer"] = row.pop("Customer")
                row["Rate"] = row.pop("B/R")
                row["Hours"] = row.pop("REG HRS")

                row["Rate"] = pd.to_numeric(row["Rate"], errors="coerce")
                row["Hours"] = pd.to_numeric(row["Hours"], errors="coerce")
                row["OT HRS"] = pd.to_numeric(row.get("OT HRS", 0), errors="coerce")
                row["OT B/R"] = pd.to_numeric(row.get("OT B/R", 0), errors="coerce")

                row["Amount"] = round(row["Hours"] * row["Rate"], 2) if pd.notnull(row["Hours"]) and pd.notnull(row["Rate"]) else None
                new_rows.append(row)

                if row["OT HRS"] > 0:
                    overtime_row = row.copy()
                    overtime_row["Employee"] = "Overtime"
                    overtime_row["Hours"] = row["OT HRS"]
                    overtime_row["Rate"] = row["OT B/R"]
                    overtime_row["Amount"] = round(overtime_row["Hours"] * overtime_row["Rate"], 2) if pd.notnull(overtime_row["Hours"]) and pd.notnull(overtime_row["Rate"]) else None
                    new_rows.append(overtime_row)

            final_df = pd.DataFrame(new_rows)
            final_df.drop(columns=["OT HRS", "OT B/R"], inplace=True)

            column_order = ["*InvoiceNo", "*Customer", "*InvoiceDate", "*DueDate", "Terms", "Employee", "Hours", "Rate", "*ItemTaxCode", "Amount"]
            final_df = final_df[column_order]
            final_df.dropna(inplace=True)

            if final_df.empty:
                print("No records found in the input file.")
                return

            output_file_path = os.path.join('/home/will-england/ETL',output_file)
            final_df.to_csv(output, index=False)
            print(f"Output saved to {output}")

    except Exception as e:
        print(f"An error occurred: {e}")

def process_epic(input_file, co_code_output):
    try:
        df = pd.read_excel(input_file, dtype={"EE ID": str})
        df.columns = df.columns.str.strip().str.upper()

        required_columns = {"CO CODE", "EE ID", "REG HRS", "OT HRS"}
        if not required_columns.issubset(df.columns):
            missing_cols = required_columns - set(df.columns)
            raise ValueError(f"Missing columns in input file: {missing_cols}")

        df = df[["CO CODE", "EE ID", "REG HRS", "OT HRS"]]
        df.dropna(how="all", inplace=True)
        df = df[~df["REG HRS"].astype(str).str.contains("OFF", case=False, na=False)]
        df["EE ID"] = pd.to_numeric(df["EE ID"], errors="coerce")
        df.dropna(subset=["EE ID"], inplace=True)
        df["EE ID"] = df["EE ID"].astype(int)
        df["CO CODE"] = df["CO CODE"].ffill()
        df["REG HRS"] = pd.to_numeric(df["REG HRS"], errors="coerce").fillna(0)
        df["OT HRS"] = pd.to_numeric(df["OT HRS"], errors="coerce").fillna(0)
        df = df[~((df["REG HRS"] == 0) & (df["OT HRS"] == 0))]
        df = df[["CO CODE", "EE ID", "REG HRS", "OT HRS"]]
        df.to_csv(co_code_output, mode='a', header=not pd.io.common.file_exists(co_code_output), index=False)
        print(f"Data saved to {co_code_output}")

    except Exception as e:
        print(f"An error occurred in process_epic: {e}")
