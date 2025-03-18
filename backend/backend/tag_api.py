from flask import Blueprint, request, jsonify, make_response
from flask_cors import CORS
import requests
import io
from pdfminer.high_level import extract_text
import sys
import subprocess
import importlib

def install_and_import(package):
    try:
        importlib.import_module(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    finally:
        globals()[package] = importlib.import_module(package)

install_and_import('pdfminer')
install_and_import('nltk')
install_and_import('PyPDF2')
from pdfminer.high_level import extract_text

import nltk
import PyPDF2
from typing import Dict, Any
# Import the SyllabusTagger class from your existing file
from .nlpautotagging import SyllabusTagger

# Create a blueprint instead of an app
tags = Blueprint('tags', __name__)

# Enable CORS for this blueprint
CORS(tags, resources={r"/*": {"origins": "*"}})

nltk.download('punkt')

@tags.before_request
def handle_preflight():
    """Handles CORS preflight OPTIONS requests for all endpoints under /tags."""
    if request.method == "OPTIONS":
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

@tags.route('/generate-tags', methods=['POST'])
def generate_tags():
    data = request.json
    file_url = data.get('fileUrl')
    if not file_url:
        return jsonify({"error": "No file URL provided"}), 400
    try:
        response = requests.get(file_url)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to download file: {response.status_code}"}), 400
        
        pdf_bytes = io.BytesIO(response.content)
        try:
            text = extract_text(pdf_bytes)
            if not text or len(text.strip()) == 0:
                pdf_reader = PyPDF2.PdfReader(pdf_bytes)
                text = "".join([pdf_reader.pages[i].extract_text() for i in range(len(pdf_reader.pages))])
        except Exception as e:
            return jsonify({"error": f"Error extracting text: {str(e)}"}), 500

        tagger = SyllabusTagger()
        tags_list = tagger.generate_tags(text)
        reasoning = tagger.get_tag_reasoning(text)
        
        return jsonify({
            "tags": tags_list,
            "reasoning": reasoning
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500







'''

# Download NLTK data
nltk.download('punkt')

# Specific handler for OPTIONS requests
@tags.route('/autotagging', methods=['OPTIONS'])
def options_autotagging():
    """Handle CORS preflight requests for /autotagging"""
    response = make_response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@tags.route('/generate-tags', methods=['OPTIONS'])
def options_generate_tags():
    """Handle CORS preflight requests for /generate-tags"""
    response = make_response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@tags.route('/generate-tags', methods=['POST'])
def generate_tags():
    data = request.json
    file_url = data.get('fileUrl')
    if not file_url:
        return jsonify({"error": "No file URL provided"}), 400
    try:
        # Download the PDF from the URL
        response = requests.get(file_url)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to download file: {response.status_code}"}), 400
        # Extract text from PDF
        pdf_bytes = io.BytesIO(response.content)
        try:
            text = extract_text(pdf_bytes)
            if not text or len(text.strip()) == 0:
                # Try PyPDF2 as fallback
                pdf_reader = PyPDF2.PdfReader(pdf_bytes)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text()
        except Exception as e:
            return jsonify({"error": f"Error extracting text: {str(e)}"}), 500
        # Initialize tagger and generate tags
        tagger = SyllabusTagger()
        tags_list = tagger.generate_tags(text)
        reasoning = tagger.get_tag_reasoning(text)
        return jsonify({
            "tags": tags_list,
            "reasoning": reasoning
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

@tags.route('/autotagging', methods=['POST'])
def autotagging():
    """Process uploaded file and generate tags"""
    data = request.json
    file_url = data.get('fileUrl')
    upload_id = data.get('uploadId')
    course_subject = data.get('courseSubject')
    course_number = data.get('courseNumber')
    
    if not file_url or not upload_id:
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        # Download and process the file
        response = requests.get(file_url)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to download file: {response.status_code}"}), 400
        
        # Extract text
        pdf_bytes = io.BytesIO(response.content)
        try:
            text = extract_text(pdf_bytes)
            if not text or len(text.strip()) == 0:
                pdf_reader = PyPDF2.PdfReader(pdf_bytes)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text()
        except Exception as e:
            return jsonify({"error": f"Error extracting text: {str(e)}"}), 500
        
        # Generate tags (assuming SyllabusTagger has this method)
        tagger = SyllabusTagger()
        tags_list = tagger.generate_tags(text)
        
        # Here you would typically save the tags to your database
        # For now, we'll just return them
        return jsonify({
            "tags": tags_list,
            "count": len(tags_list)
        }), 200
    except Exception as e:
        return jsonify({"error": f"Error in autotagging: {str(e)}"}), 500
'''
'''
# Import the SyllabusTagger class from your existing file
from nlpautotagging import SyllabusTagger

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

nltk.download('punkt')

@app.route('/generate-tags', methods=['OPTIONS'])
def options_preflight():
    """Handle CORS preflight requests for /generate-tags"""
    response = make_response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.route('/generate-tags', methods=['POST'])
def generate_tags():
    data = request.json
    file_url = data.get('fileUrl')
    
    if not file_url:
        return jsonify({"error": "No file URL provided"}), 400
    
    try:
        # Download the PDF from the URL
        response = requests.get(file_url)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to download file: {response.status_code}"}), 400
        
        # Extract text from PDF
        pdf_bytes = io.BytesIO(response.content)
        try:
            text = extract_text(pdf_bytes)
            if not text or len(text.strip()) == 0:
                # Try PyPDF2 as fallback
                pdf_reader = PyPDF2.PdfReader(pdf_bytes)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text()
        except Exception as e:
            return jsonify({"error": f"Error extracting text: {str(e)}"}), 500
        
        # Initialize tagger and generate tags
        tagger = SyllabusTagger()
        tags = tagger.generate_tags(text)
        reasoning = tagger.get_tag_reasoning(text)
        
        return jsonify({
            "tags": tags,
            "reasoning": reasoning
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
# Ensure NLTK resources are downloaded
nltk.download('punkt')
'''

'''
nltk.download('punkt')

@app.route('/generate-tags', methods=['OPTIONS'])
def options_preflight():
    """Handle CORS preflight requests for /generate-tags"""
    response = make_response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.route('/generate-tags', methods=['POST'])
def generate_tags():
    data = request.json
    file_url = data.get('fileUrl')
    
    if not file_url:
        return jsonify({"error": "No file URL provided"}), 400
    
    try:
        # Download the PDF from the URL
        response = requests.get(file_url)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to download file: {response.status_code}"}), 400
        
        # Extract text from PDF
        pdf_bytes = io.BytesIO(response.content)
        try:
            text = extract_text(pdf_bytes)
            if not text or len(text.strip()) == 0:
                # Try PyPDF2 as fallback
                pdf_reader = PyPDF2.PdfReader(pdf_bytes)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text()
        except Exception as e:
            return jsonify({"error": f"Error extracting text: {str(e)}"}), 500
        
        # Initialize tagger and generate tags
        tagger = SyllabusTagger()
        tags = tagger.generate_tags(text)
        reasoning = tagger.get_tag_reasoning(text)
        
        return jsonify({
            "tags": tags,
            "reasoning": reasoning
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
'''

'''
@app.route('/generate-tags', methods=['OPTIONS'])
def options_preflight():
    """Handles CORS preflight requests."""
    response = make_response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.route('/generate-tags', methods=['POST'])
def generate_tags():
    data = request.json
    file_url = data.get('fileUrl')
    
    if not file_url:
        return jsonify({"error": "No file URL provided"}), 400
    
    try:
        # Download the PDF from the URL
        response = requests.get(file_url)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to download file: {response.status_code}"}), 400
        
        # Extract text from PDF
        pdf_bytes = io.BytesIO(response.content)
        try:
            text = extract_text(pdf_bytes)
            if not text or len(text.strip()) == 0:
                # Try PyPDF2 as fallback
                pdf_reader = PyPDF2.PdfReader(pdf_bytes)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text()
        except Exception as e:
            return jsonify({"error": f"Error extracting text: {str(e)}"}), 500
        
        # Initialize tagger and generate tags
        tagger = SyllabusTagger()
        tags = tagger.generate_tags(text)
        reasoning = tagger.get_tag_reasoning(text)
        
        return jsonify({
            "tags": tags,
            "reasoning": reasoning
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
'''