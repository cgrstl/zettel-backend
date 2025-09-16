import os
import re
import requests
from io import BytesIO
from PyPDF2 import PdfReader
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

KNOWLEDGE_BASE_DIR = "knowledge_base"

if not os.path.exists(KNOWLEDGE_BASE_DIR):
    os.makedirs(KNOWLEDGE_BASE_DIR)

def save_content(url, title, content):
    """Eine zentrale Funktion zum Speichern von extrahierten Inhalten."""
    try:
        # Erstellt einen sicheren Dateinamen aus der URL
        filename = re.sub(r'https?://', '', url)
        filename = re.sub(r'[^a-zA-Z0-9]', '_', filename)[:100] + ".txt" # Gekürzt auf 100 Zeichen
        filepath = os.path.join(KNOWLEDGE_BASE_DIR, filename)
        
        # Speichert den Inhalt in einer UTF-8-codierten Datei
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
    """Empfängt sauberen Webinhalt von der Erweiterung."""
    data = request.get_json()
    if not data or "url" not in data or "content" not in data or "title" not in data:
        return jsonify({"status": "error", "message": "Fehlende Daten"}), 400
    
    if save_content(data["url"], data["title"], data["content"]):
        return jsonify({"status": "success", "message": "Web-Inhalt gespeichert"}), 201
    else:
        return jsonify({"status": "error", "message": "Speichern fehlgeschlagen"}), 500

@app.route("/ingest-pdf", methods=["POST"])
def ingest_pdf_content():
    """Empfängt eine PDF-URL, lädt sie herunter und extrahiert den Text."""
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"status": "error", "message": "Fehlende URL"}), 400

    pdf_url = data["url"]
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()

        pdf_file = BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        pdf_text = "\n".join(page.extract_text() for page in reader.pages)
        title = (reader.metadata.title or "Unbenanntes PDF")
        
        if save_content(pdf_url, title, pdf_text):
            return jsonify({"status": "success", "message": "PDF-Inhalt gespeichert"}), 201
        else:
            return jsonify({"status": "error", "message": "Speichern fehlgeschlagen"}), 500

    except Exception as e:
        print(f"Fehler bei der PDF-Verarbeitung von {pdf_url}: {e}")
        return jsonify({"status": "error", "message": "PDF konnte nicht verarbeitet werden"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)