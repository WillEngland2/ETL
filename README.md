# **ETL - Spreadsheet Processing Program**

## **Version**
- Python **3.9**

## **Not Familiar running a program?**
1. A directory is a file location. When a directory contains the files needed we call that a file location
2. Navigate to the directory where we want to install the code.
   2. For example if we want the files in our c drive.My file location is
   ```sh
   /c/Users/wengl/Will England/Projects/ETL
   ```
3. From there we want to clone the repo. (Step One)
4. If problems running python. For example python not found error try this from the terminal.
   4. winget install Python.Python
   5. pip install pandas

## **How to Use the Program**

1. **Clone the repository** to your local directory: (If no github account please make one so they can be added as a collaborator for easier code sharing)
   ```sh
   git clone https://github.com/WillEngland2/ETL.git
   ```
2. **Navigate** to the cloned directory:
   ```sh
   cd <repo-directory>
   ```
3. **Run the program** using the following command:
   ```sh
   python3 RunMe.py
   ```
   **Where:**
    - `Input File` → The input spreadsheet containing the data.
    - `OutputFule` → The name of the generated output file.
    - `Epic File Name` → The name of the epic generated output file.
    - `Invoice Date` → The **invoice date**.
    - `Due Date` → The **due date**.
    - `Terms` → The **payment terms**.
    - `Item Tax Code` → The **Item Tax Code**.

4. **Output:**
    - Once the program completes execution, a file named **output.csv** will be created in the same directory.
    - This file will contain all relevant processed data, including company and employee details, organized into a single sheet.  

5. **Additional Notes:**
   - When updating sheets need to make sure each employee has the customer in first row.
   - If pay correction is needed please add all needed information in the row so the parser knows who its for.
   - If a worker did not input hours in reg or ot, mark as zero. If not marked the parser will consider this an empty 
   row and throw it out.

6. **Run EXE:**
   - Download the exe that has been provided
   - Run the program and input data
   - all created files will be saved to desktop 
