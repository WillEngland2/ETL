from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

@app.route("/")
def home():
    return jsonify({"message": "Hello, World!"})

@app.route("/process", methods=["GET"])
def process_data():
    value = request.args.get("value", type=int)
    if value is None:
        return jsonify({"error": "Missing 'value' parameter"}), 400

    result = value * 2  # Example computation
    return jsonify({"result": result})

# No need for app.run() as this is handled by the WSGI server
