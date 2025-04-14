# ETL Project

This web application allows users to upload Excel or PDF timecard files and transform them into structured CSVs ready for invoicing and QuickBooks import. It's built for ease of use—no command line required.

## 🛠️ Tech Stack

- **Backend:** Python, Flask, pandas, pdfplumber  
- **Frontend:** HTML, Bootstrap  
- **Hosting:** PythonAnywhere (or any WSGI-compatible service)

## Features

- Upload Time Sheet`.xlsx`, `.xls`
- Upload PDF `.pdf`
- Extracts and transforms payroll and invoice data  
- Automatically calculates invoice amounts  
- Generates CSVs for QuickBooks and Epic data
- Takes PDF Files and creates an xlsx file for easy input into exisiting file
- Clean, simple web interface

## How to Use

1. Visit the web app in your browser.
2. Upload your Excel or PDF file.
3. Fill out invoice details (file name, invoice date, due date, etc.).
4. Submit and download your generated CSV files.

- **Main Output:** Formatted payroll and invoice data  
- **Second Output:** Separate invoices if needed  
- **Epic Output:** Epic-specific employee hour summaries
- **PDF Output:** Formatted employee infomation
