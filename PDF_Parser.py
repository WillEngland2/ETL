# Author: Will England
import pdfplumber
import re
import pandas as pd

def parse_timecard_pdf(pdf_path, output_excel_path):
    all_final_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            # Extract header info
            header_info = {}
            header_patterns = {
                "Employee": r"EE:\s+Flex Force\s*,\s*(.+)",
                "EEID": r"EEID:\s+(\d+)",
                "TCID": r"TCID:\s+(\d+)",
                "Supervisor": r"Supervisor:\s+(.+)",
                "Manager": r"Manager:\s+(.+)",
                "Policy Group": r"Policy Group:\s+(.+)",
                "Pay Group": r"Pay Group:\s+(.+)",
                "Hire Date": r"Hire Date:\s+(\d{1,2}/\d{1,2}/\d{4})",
                "Date Range": r"Time Card Report\s*-\s*(\d{1,2}/\d{1,2}/\d{4}\s+to\s+\d{1,2}/\d{1,2}/\d{4})"
            }

            for key, pattern in header_patterns.items():
                match = re.search(pattern, text)
                if match:
                    header_info[key] = match.group(1).strip()

            # Smart employee & customer name parsing
            employee_line_match = re.search(r"EE:\s+Flex Force\s*,\s*(.*?)\s+Supervisor:", text)
            if employee_line_match:
                raw_employee_line = employee_line_match.group(1).strip()
            else:
                raw_employee_line = header_info.get("Employee", "").strip()

            words = raw_employee_line.split()
            employee_name = " ".join(words[:-5]) if len(words) >= 6 else raw_employee_line
            customer_name = " ".join(words[-5:]) if len(words) >= 6 else ""

            # Find all occurrences in the entire document
            reg_matches = re.findall(r"Temp\s+Hours\s+Memo\s+(\d+\.\d+)", text) or re.findall(r"Hourly\s+(\d+\.\d+)", text)
            ot_matches = re.findall(r"Temp\s+OT\s+Memo\s+(\d+\.\d+)", text) or re.findall(r"Overtime\s+(\d+\.\d+)", text)

            # Take only the LAST occurrence (assumed to be the final summary total)
            reg = float(reg_matches[-1]) if reg_matches else 0.0
            ot = float(ot_matches[-1]) if ot_matches else 0.0

            # Add to final rows only if valid hours exist
            if reg > 0 or ot > 0:
                all_final_rows.append({
                    "Customer": customer_name,
                    "Employee": employee_name,
                    "REG HRS": reg,
                    "OT HRS": ot,
                    "TOTAL HRS": reg + ot
                })

    # Build final DataFrame
    final_df = pd.DataFrame(all_final_rows)

    if final_df.empty:
        # Create an empty Excel file if nothing valid was extracted
        with pd.ExcelWriter(output_excel_path, engine='xlsxwriter') as writer:
            pd.DataFrame(columns=["Customer", "Employee", "REG HRS", "OT HRS", "TOTAL HRS"]).to_excel(
                writer, index=False, sheet_name="Payroll Ready"
            )
        print("⚠️ No valid REG or OT hours found. Empty Excel file created.")
        return

    # Group and sort the extracted rows
    # final_df = final_df.groupby(["Customer", "Employee"], as_index=False).sum()
    # final_df = final_df.sort_values(by="Employee")

    # Compute total hours for pay period
    pay_period_total = final_df["TOTAL HRS"].sum()

    # Write to Excel
    with pd.ExcelWriter(output_excel_path, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False, sheet_name="Payroll Ready")
        workbook = writer.book
        worksheet = writer.sheets["Payroll Ready"]
        row = len(final_df) + 2
        worksheet.write(row, 0, "TOTAL PAY PERIOD HOURS")
        worksheet.write(row, 1, pay_period_total)

    print(f"✅ Excel file created: {output_excel_path}")
