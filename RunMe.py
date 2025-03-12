import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess

def on_button_click():
    input_file = entry_input_file.get()
    output_file = entry_output_file.get()
    co_code_output = entry_co_code_output.get()
    invoice_date = entry_invoice_date.get()
    due_date = entry_due_date.get()
    terms = entry_terms.get()
    item_tax_code = entry_item_tax_code.get()

    # Check if all fields are filled
    if not all([input_file, output_file, co_code_output, invoice_date, due_date, terms]):
        messagebox.showwarning("Input Error", "Please fill in all required fields!")
        return

    try:
        # Run the main script with the provided inputs
        subprocess.run(
            ["python", "ETL-Main.py", input_file, output_file, co_code_output, invoice_date, due_date, terms, item_tax_code],
            check=True
        )
        messagebox.showinfo("Success", "Process completed successfully!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def browse_input_file():
    filename = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xls")])
    if filename:
        entry_input_file.delete(0, tk.END)
        entry_input_file.insert(0, filename)

# Create the main window
root = tk.Tk()
root.title("Excel Processing GUI")
root.geometry("600x600")

# Create a frame for the input file with the Browse button next to it
frame_input_file = tk.Frame(root)
frame_input_file.pack(pady=5)

# Create widgets for file paths and other inputs
label_input_file = tk.Label(frame_input_file, text="Input File:")
label_input_file.pack(side=tk.LEFT,pady=5)

entry_input_file = tk.Entry(frame_input_file)
entry_input_file.pack(side=tk.LEFT, padx=5)

button_browse_input = tk.Button(frame_input_file, text="Browse", command=browse_input_file)
button_browse_input.pack(side=tk.LEFT,pady=5)

label_output_file = tk.Label(root, text="Output File:")
label_output_file.pack(pady=5)
entry_output_file = tk.Entry(root)
entry_output_file.pack(pady=5)

label_co_code_output = tk.Label(root, text="Epic File Name:")
label_co_code_output.pack(pady=5)
entry_co_code_output = tk.Entry(root)
entry_co_code_output.pack(pady=5)

label_invoice_date = tk.Label(root, text="Invoice Date:")
label_invoice_date.pack(pady=5)
entry_invoice_date = tk.Entry(root)
entry_invoice_date.pack(pady=5)

label_due_date = tk.Label(root, text="Due Date:")
label_due_date.pack(pady=5)
entry_due_date = tk.Entry(root)
entry_due_date.pack(pady=5)

label_terms = tk.Label(root, text="Terms:")
label_terms.pack(pady=5)
entry_terms = tk.Entry(root)
entry_terms.pack(pady=5)

label_item_tax_code = tk.Label(root, text="Item Tax Code (optional):")
label_item_tax_code.pack(pady=5)
entry_item_tax_code = tk.Entry(root)
entry_item_tax_code.pack(pady=5)

# Create a submit button
button = tk.Button(root, text="Generate Files", command=on_button_click)
button.pack(pady=20)

# Run the application
root.mainloop()
