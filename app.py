from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

@app.route("/")
def home():
    return jsonify({"message": "API is running!"})

@app.route("/process", methods=["GET"])
def process_data():
    value = request.args.get("value", type=int)
    if value is None:
        return jsonify({"error": "Missing 'value' parameter"}), 400

    result = value * 2  # Example computation
    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
