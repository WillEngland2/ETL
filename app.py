import os
import logging
import traceback
from flask import Flask, render_template, send_from_directory, request, jsonify, redirect, url_for
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from ETL_Main import process_excel, process_epic
import pandas as pd

# Load environment variables from .env
load_dotenv()

# Get login credentials from .env
VALID_USERNAME = os.getenv("ETL_USERNAME")
VALID_PASSWORD = os.getenv("ETL_PASSWORD")

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PROCESSED_FILES_DIR = os.path.join(BASE_DIR, 'processed-files')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FILES_DIR, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', ''}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    user_input = request.form.get("username")
    pass_input = request.form.get("password")
    product = request.form.get("product")

    if user_input == VALID_USERNAME and pass_input == VALID_PASSWORD:
        if product == 'etl':
            return redirect(url_for('upload_page'))
    return "Invalid login. <a href='/'>Try again</a>", 401

@app.route('/upload-page')
def upload_page():
    return render_template('template.html')  # Your upload form page

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
            except Exception as form_error:
                logging.error("Missing or invalid form field:")
                logging.error(traceback.format_exc())
                return jsonify({"error": "Missing or invalid form field"}), 400

            # Process the file and generate CSV outputs
            processed_files = process_data(temp_filepath, output_name, epic_name, invoice_date)

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

def process_data(file_path, file_name, epic_name, invoice_date):
    main_output_file = os.path.join(PROCESSED_FILES_DIR, f"{file_name}.csv")
    second_output_file = os.path.join(PROCESSED_FILES_DIR, f"2{file_name}.csv")
    epic_output_file = os.path.join(PROCESSED_FILES_DIR, f"{epic_name}_epic.csv")

    output_files = {
        "main_output": os.path.basename(main_output_file),
        "second_output": os.path.basename(second_output_file),
        "epic_output": os.path.basename(epic_output_file)
    }

    try:
        process_excel(file_path, main_output_file, invoice_date)
        if not os.path.exists(second_output_file):
            open(second_output_file, 'w').close()
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
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
