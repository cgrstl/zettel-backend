import sqlite3
import os

DATABASE_FILE = "zettel_hub.db"

def get_db_connection():
    """Establishes a connection to the database and enables foreign key support."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.execute("PRAGMA foreign_keys = ON") # Essential for cascading deletes
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database, creating all tables if they don't exist.
    This function is designed to be run once when the application starts.
    """
    if os.path.exists(DATABASE_FILE):
        print("Database already exists.")
        return

    print("Creating new database and tables...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Documents Table
    cursor.execute("""
    CREATE TABLE documents (
        doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_url TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Workspaces Table
    cursor.execute("""
    CREATE TABLE workspaces (
        workspace_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        custom_prompt TEXT,
        search_themes TEXT, -- Stored as a JSON string
        prompt_vector BLOB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Chunks Table
    cursor.execute("""
    CREATE TABLE chunks (
        chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id INTEGER NOT NULL,
        chunk_text TEXT NOT NULL,
        chunk_vector BLOB,
        FOREIGN KEY (doc_id) REFERENCES documents (doc_id) ON DELETE CASCADE
    );
    """)

    # 4. FTS Table for fast lexical search
    cursor.execute("""
    CREATE VIRTUAL TABLE chunks_fts USING fts5(
        chunk_text,
        content='chunks',
        content_rowid='chunk_id'
    );
    """)
    # Triggers to keep the search index synchronized with the chunks table
    cursor.execute("CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN INSERT INTO chunks_fts(rowid, chunk_text) VALUES (new.chunk_id, new.chunk_text); END;")
    cursor.execute("CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN INSERT INTO chunks_fts(chunks_fts, rowid, chunk_text) VALUES ('delete', old.chunk_id, old.chunk_text); END;")

    # 5. Mapping Table to link workspaces and chunks
    cursor.execute("""
    CREATE TABLE workspace_chunk_mapping (
        workspace_id INTEGER NOT NULL,
        chunk_id INTEGER NOT NULL,
        PRIMARY KEY (workspace_id, chunk_id),
        FOREIGN KEY (workspace_id) REFERENCES workspaces (workspace_id) ON DELETE CASCADE,
        FOREIGN KEY (chunk_id) REFERENCES chunks (chunk_id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    # This allows you to create the database by running 'python3 database.py'
    init_db()