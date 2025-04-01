import pandas as pd
import os
from datetime import datetime, timedelta

def process_excel(input_file, output_file, invoice_date):
    try:
        invoice_date_obj = datetime.strptime(invoice_date, '%Y-%m-%d')
    except ValueError:
        try:
            invoice_date_obj = datetime.strptime(invoice_date, '%d %m %Y')
        except ValueError:
            print("Error: Invoice date must be in either yyyy-mm-dd or d m y format.")
            return

    due_date_obj = invoice_date_obj + timedelta(days=30)
    invoice_date_formatted = f"{invoice_date_obj.month}/{invoice_date_obj.day}/{invoice_date_obj.year}"
    due_date_formatted = f"{due_date_obj.month}/{due_date_obj.day}/{due_date_obj.year}"

    if not (input_file.endswith(".xlsx") or input_file.endswith(".xls")):
        print("Error: The input file must be an Excel file (.xlsx or .xls).")
        return

    try:
        df = pd.read_excel(input_file)

        has_department = "Department" in df.columns

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

        valid_inv_nums = pd.to_numeric(df["Inv Num"], errors="coerce").dropna().astype(int)
        invoice_no = valid_inv_nums.min() - 2 if not valid_inv_nums.empty else 115

        second_output_file = os.path.join(os.path.dirname(output_file), "2" + os.path.basename(output_file))

        for i, (data, output) in enumerate([(df_before, output_file), (df_after, second_output_file)]):
            is_second_invoice = (i == 1)

            columns_to_extract = ["Customer", "Employee", "REG HRS", "B/R", "OT HRS", "OT B/R", "Inv Num"]
            if has_department:
                columns_to_extract.append("Department")

            data = data.copy()
            for col in columns_to_extract:
                if col in data.columns:
                    data[col] = data[col].astype(str).str.strip()

            data = data.dropna(subset=["Customer", "Employee", "REG HRS", "B/R"])
            data = data[data["Customer"].notna() & (data["Customer"] != "")]
            data = data[columns_to_extract].copy()

            current_customer = ""
            new_rows = []

            for _, row in data.iterrows():
                customer_name = row["Customer"]

                if "Separate Invoice" in str(customer_name):
                    continue
                if pd.isna(customer_name) or not str(customer_name).strip():
                    continue

                if customer_name != current_customer:
                    current_customer = customer_name
                    invoice_no += 1

                try:
                    inv_num = int(row["Inv Num"]) if pd.notnull(row["Inv Num"]) else None
                    if inv_num is not None:
                        invoice_no = inv_num
                except ValueError:
                    pass

                row["*InvoiceNo"] = invoice_no
                row["*ItemTaxCode"] = " "
                row["*InvoiceDate"] = invoice_date_formatted
                row["*DueDate"] = due_date_formatted
                row["Terms"] = "Net 30"
                row["*Customer"] = row.pop("Customer")
                row["Rate"] = pd.to_numeric(row.pop("B/R"), errors="coerce")
                row["Hours"] = pd.to_numeric(row.pop("REG HRS"), errors="coerce")
                row["OT HRS"] = pd.to_numeric(row.get("OT HRS", 0), errors="coerce")
                row["OT B/R"] = pd.to_numeric(row.get("OT B/R", 0), errors="coerce")

                if not is_second_invoice or "Department" not in row:
                    row.pop("Department", None)

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
            final_df.drop(columns=["OT HRS", "OT B/R"], inplace=True, errors='ignore')

            # Drop rows with any missing important values
            final_df = final_df.dropna(subset=["*Customer", "Employee", "Hours", "Rate", "Amount"])

            # Build final column order
            column_order = ["*InvoiceNo", "*Customer", "*InvoiceDate", "*DueDate", "Terms", "Employee"]
            if is_second_invoice and has_department:
                column_order.append("Department")
            column_order += ["Hours", "Rate", "*ItemTaxCode", "Amount"]

            for col in column_order:
                if col not in final_df.columns:
                    final_df[col] = ""

            final_df = final_df[column_order]

            if final_df.empty:
                print(f"No records found for {'second' if is_second_invoice else 'first'} invoice.")
                continue

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
