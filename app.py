import os
import logging
import traceback
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from PDF_Parser import parse_timecard_pdf  # Make sure this matches your file name

# Load .env variables
load_dotenv()
VALID_USERNAME = os.getenv("ETL_USERNAME")
VALID_PASSWORD = os.getenv("ETL_PASSWORD")

app = Flask(__name__)

# Folder config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PROCESSED_FOLDER = os.path.join(BASE_DIR, 'processed-files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}

@app.route('/')
def index():
    return render_template('index.html')  # Login form lives here

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    product = request.form.get("product")

    if username == VALID_USERNAME and password == VALID_PASSWORD:
        if product == "etl":
            return redirect(url_for('upload_page'))
        elif product == "pdf_parser":
            return redirect(url_for('pdf_parser_page'))
    return "Invalid login or product. <a href='/'>Try again</a>", 401

@app.route('/upload-page')
def upload_page():
    return render_template('ETL_Template.html')  # Use this for ETL file uploads

@app.route('/pdf-parser-page')
def pdf_parser_page():
    return render_template('PDF_Template.html')  # This one is for PDF uploads

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid PDF file"}), 400

    try:
        filename = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(temp_path)

        output_filename = f"parsed_{os.path.splitext(filename)[0]}.xlsx"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)

        # Parse and generate Excel
        parse_timecard_pdf(temp_path, output_path)

        return jsonify({
            "message": "PDF processed successfully",
            "download_link": url_for('download_file', filename=output_filename)
        }), 200

    except Exception as e:
        logging.error("Error during PDF parsing:")
        logging.error(traceback.format_exc())
        return jsonify({"error": "Internal server error"}), 500

@app.route('/processed-files/<filename>')
def download_file(filename):
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
