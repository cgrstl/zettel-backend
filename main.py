import os
import re
import requests
import google.generativeai as genai
from io import BytesIO
from PyPDF2 import PdfReader
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Konfiguration der Gemini API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Kein GEMINI_API_KEY gefunden. Bitte in .env Datei eintragen.")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
# ------------------------------------

KNOWLEDGE_BASE_DIR = "knowledge_base"

if not os.path.exists(KNOWLEDGE_BASE_DIR):
    os.makedirs(KNOWLEDGE_BASE_DIR)

# --- VOLLSTÄNDIGE FUNKTIONEN VON VORHER ---
def save_content(url, title, content):
    """Eine zentrale Funktion zum Speichern von extrahierten Inhalten."""
    try:
        filename = re.sub(r'https?://', '', url)
        filename = re.sub(r'[^a-zA-Z0-9]', '_', filename)[:100] + ".txt"
        filepath = os.path.join(KNOWLEDGE_BASE_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Source URL: {url}\n")
            f.write(f"Title: {title}\n\n---\n\n")
            f.write(content)
        print(f"Inhalt von '{url[:50]}...' erfolgreich gespeichert.")
        return True
    except Exception as e:
        print(f"Fehler beim Speichern der Datei: {e}")
        return False

@app.route("/ingest-web", methods=["POST"])
def ingest_web_content():
    data = request.get_json()
    if not data or "url" not in data or "content" not in data or "title" not in data:
        return jsonify({"status": "error", "message": "Fehlende Daten"}), 400
    if save_content(data["url"], data["title"], data["content"]):
        return jsonify({"status": "success", "message": "Web-Inhalt gespeichert"}), 201
    else:
        return jsonify({"status": "error", "message": "Speichern fehlgeschlagen"}), 500

@app.route("/ingest-pdf", methods=["POST"])
def ingest_pdf_content():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"status": "error", "message": "Fehlende URL"}), 400
    pdf_url = data["url"]
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()
        pdf_file = BytesIO(response.content)
        reader = PdfReader(pdf_file)
        pdf_text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        title = (reader.metadata.title or "Unbenanntes PDF")
        if save_content(pdf_url, title, pdf_text):
            return jsonify({"status": "success", "message": "PDF-Inhalt gespeichert"}), 201
        else:
            return jsonify({"status": "error", "message": "Speichern fehlgeschlagen"}), 500
    except Exception as e:
        print(f"Fehler bei der PDF-Verarbeitung von {pdf_url}: {e}")
        return jsonify({"status": "error", "message": "PDF konnte nicht verarbeitet werden"}), 500
# ---------------------------------------------

# --- NEUE ENDPUNKTE ---
@app.route("/files", methods=["GET"])
def list_files():
    try:
        files = [f for f in os.listdir(KNOWLEDGE_BASE_DIR) if f.endswith('.txt')]
        return jsonify({"status": "success", "files": files})
    except Exception as e:
        return jsonify({"status": "error", "message": "Dateien konnten nicht geladen werden"}), 500

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
        print(f"!!!! Detaillierter KI-Fehler: {e} !!!!")
        return jsonify({"status": "error", "message": "Fehler bei der KI-Anfrage"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)