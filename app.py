import os
import logging
import traceback
from flask import Flask, render_template, send_from_directory, request, jsonify
from werkzeug.utils import secure_filename
from ETL_Main import process_excel, process_epic
import pandas as pd

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Use an absolute path for the uploads folder so it works on PythonAnywhere
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PROCESSED_FILES_DIR = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', ''}

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    logging.info(f"Form keys received: {list(request.form.keys())}")

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            temp_filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(temp_filepath)
            logging.info(f"File uploaded successfully: {temp_filepath}")

            # Extract form inputs
            try:
                output_name = request.form['output_name']
                epic_name = request.form['epic_name']
                invoice_date = request.form['invoice_date']
                due_date = request.form['due_date']
                terms = request.form['terms']
                item_tax_code = request.form['item_tax_code']
            except Exception as form_error:
                logging.error("Missing or invalid form field:")
                logging.error(traceback.format_exc())
                return jsonify({"error": "Missing or invalid form field"}), 400

            # Process the file and generate CSV outputs
            processed_files = process_data(
                temp_filepath, output_name, epic_name,
                invoice_date, due_date, terms, item_tax_code
            )

            if processed_files:
                return jsonify({
                    "message": "Files processed successfully",
                    "files": [
                        {"file_url": f"/processed-files/{processed_files['main_output']}", "name": "Main Output"},
                        {"file_url": f"/processed-files/{processed_files['second_output']}", "name": "Second Output"},
                        {"file_url": f"/processed-files/{processed_files['epic_output']}", "name": "Epic Output"}
                    ]
                }), 200
            else:
                return jsonify({"error": "File processing failed"}), 500

        except Exception as e:
            logging.error("An error occurred during file upload:")
            logging.error(traceback.format_exc())
            return jsonify({"error": "Internal server error"}), 500

    return jsonify({"error": "Invalid file format"}), 400

def process_data(file_path, file_name, epic_name, invoice_date, due_date, terms, item_tax_code):
    # Construct output filenames with .csv extension
    main_output_file = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_name}.csv")
    second_output_file = os.path.join(app.config['UPLOAD_FOLDER'], f"2{file_name}.csv")
    epic_output_file = os.path.join(app.config['UPLOAD_FOLDER'], f"{epic_name}_epic.csv")

    output_files = {
        "main_output": os.path.basename(main_output_file),
        "second_output": os.path.basename(second_output_file),
        "epic_output": os.path.basename(epic_output_file)
    }

    try:
        # Process the main data to CSV
        process_excel(file_path, main_output_file, invoice_date, due_date, terms, item_tax_code)

        # Ensure the second output file exists (create an empty file if not generated)
        if not os.path.exists(second_output_file):
            open(second_output_file, 'w').close()

        # Process the epic data to CSV
        process_epic(file_path, epic_output_file)

        logging.info("--- ETL Process Finished ---")
        logging.info(f"Returning output files: {output_files}")
        return output_files

    except Exception as e:
        logging.error("An error occurred during ETL processing:")
        logging.error(traceback.format_exc())
        return None

@app.route('/processed-files/<filename>')
def download_file(filename):
    try:
        return send_from_directory(PROCESSED_FILES_DIR, filename)
    except Exception as e:
        logging.error("Error serving file:")
        logging.error(traceback.format_exc())
        return jsonify({"error": "File not found"}), 404

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    return render_template('index.html')  # Ensure your HTML file is named 'template.html'

if __name__ == '__main__':
    app.run(debug=True)
