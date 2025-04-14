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
            employee_name = " ".join(words[:-5])
            customer_name = " ".join(words[-5:])

            # Extract daily entries
            daily_entries = []
            daily_matches = re.findall(
                r"(Thursday|Friday|Saturday)\s+(\d{1,2}/\d{1,2}/\d{4})(.*?)\n\s*(\d+\.\d+)\s+0\.00\s+(\d+\.\d+)",
                text,
                re.DOTALL
            )

            for match in daily_matches:
                day, date, block, daily_total, paid_total = match
                time_blocks = re.findall(
                    r"(\d{2}:\d{2}\s[AP]M|\(\d{2}:\d{2}\s[AP]M\))\s*(\d{2}:\d{2}\s[AP]M|\(\d{2}:\d{2}\s[AP]M\))\s+100\s+(.*?)\s+(\d+\.\d+)\s+(\d+\.\d+)",
                    block
                )
                for tb in time_blocks:
                    start, end, earning_type, hours, paid = tb
                    daily_entries.append({
                        "Earning Type": earning_type.strip(),
                        "Hours": hours
                    })

            # Add Total Hours if present
            total_hours_match = re.search(r"Total Hours\s+(\d+\.\d+)", text)
            if total_hours_match:
                total_hours = float(total_hours_match.group(1))
                daily_entries.append({
                    "Earning Type": "Total Hours",
                    "Hours": total_hours
                })

            # Only use Total Hours if present, else sum block entries
            total_entry = next((e for e in daily_entries if e["Earning Type"].lower() == "total hours"), None)

            if total_entry:
                total_hours = float(total_entry["Hours"])
                if total_hours > 40:
                    reg = 40.0
                    ot = total_hours - 40.0
                else:
                    reg = total_hours
                    ot = 0.0

                all_final_rows.append({
                    "Customer": customer_name,
                    "Employee": employee_name,
                    "REG HRS": reg,
                    "OT HRS": ot,
                    "TOTAL HRS": reg + ot
                })
            else:
                for entry in daily_entries:
                    earning_type = entry["Earning Type"].lower()
                    if "hours" not in earning_type:
                        continue
                    reg_hours = float(entry["Hours"])
                    all_final_rows.append({
                        "Customer": customer_name,
                        "Employee": employee_name,
                        "REG HRS": reg_hours,
                        "OT HRS": 0.0,
                        "TOTAL HRS": reg_hours
                    })

    # Group entries across all pages
    final_df = pd.DataFrame(all_final_rows)
    final_df = final_df.groupby(["Customer", "Employee"], as_index=False).sum()

    final_df = final_df.sort_values(by= "Employee")

    # Compute total only once
    pay_period_total = final_df["TOTAL HRS"].sum()

    # ✅ Write everything to Excel
    with pd.ExcelWriter(output_excel_path, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False, sheet_name="Payroll Ready")

        # Add TOTAL PAY PERIOD HOURS row below table
        workbook = writer.book
        worksheet = writer.sheets["Payroll Ready"]
        row = len(final_df) + 2
        worksheet.write(row, 0, "TOTAL PAY PERIOD HOURS")
        worksheet.write(row, 1, pay_period_total)

    print(f"Excel file created: {output_excel_path}")
