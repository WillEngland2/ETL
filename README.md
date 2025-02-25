# **ETL - Spreadsheet Processing Program**

## **Version**
- Python **3.9**

## **How to Use the Program**

1. **Clone the repository** to your local directory:
   ```sh
   git clone <repo-url>
   ```
2. **Navigate** to the cloned directory:
   ```sh
   cd <repo-directory>
   ```
3. **Run the program** using the following command:
   ```sh
   python ETL-Main.py input.xlsx output.xlsx 2433 1/4/2025 2/3/2025 "Net 30"
   ```
   **Where:**
    - `input.xlsx` → The input spreadsheet containing the data.
    - `output.xlsx` → The name of the generated output file.
    - `2433` → The **invoice number**.
    - `1/4/2025` → The **invoice date**.
    - `2/3/2025` → The **due date**.
    - `"Net 30"` → The **payment terms**.
    - `"""` → The **Item Tax Code**.

4. **Output:**
    - Once the program completes execution, a file named **output.xlsx** will be created in the same directory.
    - This file will contain all relevant processed data, including company and employee details, organized into a single sheet.  
