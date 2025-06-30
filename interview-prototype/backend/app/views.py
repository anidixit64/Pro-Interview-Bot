from app import app
from flask import render_template, request, jsonify
import sqlite3
import os
from config import get_openai_api_key, get_gemini_api_key

api_key = config.get_gemini_api_key()

from backend.llm_service import GeminiClient

gemini_client = GeminiClient(api_key=api_key)

@app.route('/')
def index():
    return render_template('public/home.html')

@app.route('/check-secrets')
def check_secrets_endpoint():
    try:
        # Attempt to retrieve keys - the functions handle the Secret Manager interaction
        openai_key = get_openai_api_key()
        gemini_key = get_gemini_api_key()
        # In a real app, DON'T return the keys! Just confirm success.
        return jsonify({"status": "success", "message": "API keys retrieved successfully!"})
    except Exception as e:
        # If retrieval fails, an exception is raised by get_..._key()
        return jsonify({"status": "error", "message": f"Failed to retrieve keys: {e}"}), 500

if __name__ == '__main__':
    # for local testing only
    app.run(debug=True)