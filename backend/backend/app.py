from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import os

app = Flask(__name__)
CORS(app)

# Supabase credentials
SUPABASE_URL = "https://tsbrojrazwcsjqzvnopi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzYnJvanJhendjc2pxenZub3BpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk3MTc1ODMsImV4cCI6MjA1NTI5MzU4M30.5gdS__fSoNQkyrqfuG6WPQPZCEqhPmJKyxlAevemIQw"

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    file_path = f"pdfs/{file.filename}"  # Store file in 'pdfs' bucket
    response = supabase.storage.from_("pdfs").upload(file_path, file)

    if response.get("error"):
        return jsonify({"error": response["error"]}), 400

    file_url = f"{SUPABASE_URL}/storage/v1/object/public/{file_path}"
    
    return jsonify({"message": "File uploaded successfully", "fileURL": file_url}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
