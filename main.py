import os
import re
import requests
import google.generativeai as genai
from io import BytesIO
from PyPDF2 import PdfReader
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus der .env Datei (für den API-Schlüssel)
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Konfiguration der Gemini API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Kein GEMINI_API_KEY gefunden. Bitte in .env Datei eintragen.")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')
# ------------------------------------

KNOWLEDGE_BASE_DIR = "knowledge_base"

# ... (Ihre ingest-Funktionen bleiben exakt gleich) ...
def save_content(url, title, content):
    # ... (keine Änderungen hier)
@app.route("/ingest-web", methods=["POST"])
def ingest_web_content():
    # ... (keine Änderungen hier)
@app.route("/ingest-pdf", methods=["POST"])
def ingest_pdf_content():
    # ... (keine Änderungen hier)


# --- NEU: Endpunkt, um alle gespeicherten Dateien aufzulisten ---
@app.route("/files", methods=["GET"])
def list_files():
    """Listet alle Dateien in der Knowledge Base auf."""
    try:
        files = [f for f in os.listdir(KNOWLEDGE_BASE_DIR) if f.endswith('.txt')]
        return jsonify({"status": "success", "files": files})
    except Exception as e:
        return jsonify({"status": "error", "message": "Dateien konnten nicht geladen werden"}), 500


# --- NEU: Der Chat-Endpunkt ---
@app.route("/chat", methods=["POST"])
def chat_with_document():
    data = request.get_json()
    if not data or "question" not in data or "filename" not in data:
        return jsonify({"status": "error", "message": "Fehlende 'question' oder 'filename'"}), 400

    question = data["question"]
    filename = data["filename"]
    filepath = os.path.join(KNOWLEDGE_BASE_DIR, filename)

    if not os.path.exists(filepath):
        return jsonify({"status": "error", "message": "Datei nicht gefunden"}), 404

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            document_content = f.read()

        prompt = f"""
        Beantworte die Frage nur basierend auf dem folgenden Kontext.
        Wenn die Antwort nicht im Kontext zu finden ist, sage das.

        Kontext:
        ---
        {document_content}
        ---

        Frage: {question}
        """

        response = model.generate_content(prompt)
        return jsonify({"status": "success", "answer": response.text})

    except Exception as e:
        return jsonify({"status": "error", "message": "Fehler bei der KI-Anfrage"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)