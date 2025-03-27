import os
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import logging
from ETL_Main import process_excel, process_epic

# Initialize the Flask application
app = Flask(__name__)

# Configure file upload and processing directories
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'csv'}

# Configure app settings
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Check if the uploaded file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to handle file upload
@app.route('/')
def index():
    return """
        <html>
        <body>
            <h1>Welcome to ETL Converter</h1>
            <form action="/upload" method="POST" enctype="multipart/form-data">
                <input type="file" name="file" required>
                <input type="text" name="output_name" placeholder="Output Name" required>
                <input type="text" name="epic_name" placeholder="Epic Name">
                <input type="text" name="invoice_date" placeholder="Invoice Date">
                <input type="text" name="due_date" placeholder="Due Date">
                <input type="text" name="terms" placeholder="Terms">
                <input type="text" name="item_tax_code" placeholder="Item Tax Code">
                <button type="submit">Upload</button>
            </form>
        </body>
        </html>
    """

# Route to handle the upload and process the file
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    
    # Check if the file is valid
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    # Get additional form data
    output_name = request.form.get('output_name', 'Unknown Output')  # Changed to match input field name
    epic_name = request.form.get('epic_name', 'Unknown Epic')
    invoice_date = request.form.get('invoice_date', 'Unknown Date')
    due_date = request.form.get('due_date', 'Unknown Due Date')
    terms = request.form.get('terms', 'N/A')
    item_tax_code = request.form.get('item_tax_code', 'N/A')

    # Secure filename and save the file temporarily
    filename = secure_filename(file.filename)
    original_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(original_filepath)

    # Process the file and generate the processed file
    processed_filename = process_data(original_filepath, filename, output_name, epic_name, invoice_date, due_date, terms, item_tax_code)

    if not processed_filename:
        return jsonify({'error': 'Failed to process file'}), 500

    # Return the processed file for download
    return send_from_directory(app.config['PROCESSED_FOLDER'], processed_filename, as_attachment=True)

# Function to process the file
def process_data(filepath, filename, output_name, epic_name, invoice_date, due_date, terms, item_tax_code):
    """
    Process the uploaded file using the provided input data,
    invoking the ETL_main.py functions.
    """
    # Use the provided output_name for the processed file
    processed_filename = f"{output_name}.xlsx"  # Save the processed file with the desired name
    processed_filepath = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)

    # Call the relevant ETL processing function
    try:
        if "epic" in filename.lower():
            # Process the epic file
            process_epic(filepath, processed_filepath, epic_name, invoice_date, due_date, terms, item_tax_code)
        else:
            # Process the Excel file
            process_excel(filepath, processed_filepath, invoice_date, due_date, terms, item_tax_code)

        return processed_filename
    except Exception as e:
        logging.error(f"Error in processing data: {e}")
        return None

# Main entry point to run the app
if __name__ == '__main__':
    # Ensure upload and processed directories exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(PROCESSED_FOLDER):
        os.makedirs(PROCESSED_FOLDER)

    # Run the Flask app
    app.run(debug=True)
