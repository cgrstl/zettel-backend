import os
import re
import json
import sqlite3
import requests
import google.generativeai as genai
from io import BytesIO
from PyPDF2 import PdfReader
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from database import init_db, get_db_connection

# --- Setup ---
load_dotenv()
app = Flask(__name__)
CORS(app)
init_db()  # Initialize the database on startup

# --- Configuration ---
KNOWLEDGE_BASE_DIR = "knowledge_base"
if not os.path.exists(KNOWLEDGE_BASE_DIR):
    os.makedirs(KNOWLEDGE_BASE_DIR)

# --- Gemini API Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("No GEMINI_API_KEY found in .env file.")
genai.configure(api_key=GEMINI_API_KEY)
embedding_model = 'models/embedding-001'
generation_model = genai.GenerativeModel('gemini-1.5-flash')

# --- Helper Functions ---

def chunk_text(text, chunk_size=300, overlap=50):
    """Splits a text into smaller, overlapping chunks."""
    words = text.split()
    if not words: return []
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

def create_embedding(text):
    """Creates a vector embedding for a given text using the Gemini API."""
    try:
        result = genai.embed_content(model=embedding_model, content=text)
        # Store vector as a JSON string for SQLite compatibility
        return json.dumps(result['embedding'])
    except Exception as e:
        print(f"Could not create embedding for text chunk: {e}")
        return None

def generate_safe_filename(url):
    """Creates a filesystem-safe filename from a URL."""
    # Remove protocol and replace invalid characters
    filename = re.sub(r'https?://', '', url)
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    # Truncate to a reasonable length
    return filename[:150] + ".txt"

# --- Core Application Logic ---

@app.route("/ingest", methods=["POST"])
def ingest_document():
    """
    Receives a document (web page or PDF), saves the original text,
    chunks it, vectorizes the chunks, and stores everything in the database.
    """
    data = request.get_json()
    source_url = data.get("url")
    title = data.get("title")
    content = data.get("content")

    if not source_url or not title:
        return jsonify({"status": "error", "message": "Missing 'url' or 'title'"}), 400

    # If it's a PDF (no content provided), download and extract text
    if source_url.lower().endswith('.pdf') and not content:
        try:
            response = requests.get(source_url)
            response.raise_for_status()
            pdf_file = BytesIO(response.content)
            reader = PdfReader(pdf_file)
            content = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
            if not title:
                 title = reader.metadata.title or "Untitled PDF"
        except Exception as e:
            print(f"Failed to process PDF from URL {source_url}: {e}")
            return jsonify({"status": "error", "message": "Failed to process PDF"}), 500

    if not content:
        return jsonify({"status": "error", "message": "No content to ingest."}), 400

    # --- Step 1: Save original file ---
    filename = generate_safe_filename(source_url)
    filepath = os.path.join(KNOWLEDGE_BASE_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Original content saved to {filename}")
    except Exception as e:
        print(f"Error saving original file: {e}")
        return jsonify({"status": "error", "message": "Could not save original file"}), 500

    # --- Step 2: Save to database and index ---
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.cursor()
            # Insert parent document metadata
            cursor.execute(
                "INSERT INTO documents (source_url, title, filename) VALUES (?, ?, ?)",
                (source_url, title, filename)
            )
            doc_id = cursor.lastrowid
            print(f"New document added to DB with doc_id: {doc_id}")

            # Chunk text, create embeddings, and insert into DB
            text_chunks = chunk_text(content)
            for chunk_text in text_chunks:
                vector = create_embedding(chunk_text)
                cursor.execute(
                    "INSERT INTO chunks (doc_id, chunk_text, chunk_vector) VALUES (?, ?, ?)",
                    (doc_id, chunk_text, vector)
                )
            
            print(f"Ingested and chunked {len(text_chunks)} chunks for document {doc_id}.")
            
            # TODO: Add logic here to index the new chunks against all existing workspaces

    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "This document URL has already been added."}), 409
    except Exception as e:
        print(f"Error during database ingestion: {e}")
        return jsonify({"status": "error", "message": "Database error during ingestion."}), 500
    finally:
        conn.close()

    return jsonify({"status": "success", "message": f"Document '{title}' ingested.", "doc_id": doc_id}), 201


# --- Placeholder Endpoints to be built next ---

@app.route("/workspaces", methods=["GET"])
def get_workspaces():
    return jsonify({"status": "pending", "message": "Not yet implemented."})

@app.route("/workspaces", methods=["POST"])
def create_workspace():
    return jsonify({"status": "pending", "message": "Not yet implemented."})

@app.route("/chat", methods=["POST"])
def chat():
    return jsonify({"status": "pending", "message": "Not yet implemented."})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)