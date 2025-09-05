import os
import sys
import uuid
import psycopg2
from flask import Flask

def create_app():
    app = Flask(__name__)
    return app

def get_db_conn():
    host = os.environ.get("DB_HOST", "postgres")
    port = int(os.environ.get("DB_PORT", "5432"))
    db   = os.environ["DB_NAME"]
    user = os.environ["DB_USER"]
    pwd  = os.environ["DB_PASSWORD"]
    return psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pwd)

def main():
    app = create_app()
    file_name = os.environ.get("FILE_NAME")
    if not file_name:
        print("FILE_NAME not set", file=sys.stderr)
        sys.exit(1)

    file_path = os.path.join("/uploads", file_name)
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}", file=sys.stderr)
        sys.exit(2)

    with open(file_path, "rb") as f:
        data = f.read()

    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY,
                filename TEXT NOT NULL,
                uploaded_at TIMESTAMPTZ DEFAULT NOW(),
                content BYTEA NOT NULL
            )
        """)
        cur.execute(
            "INSERT INTO documents (id, filename, content) VALUES (%s, %s, %s)",
            (str(uuid.uuid4()), file_name, psycopg2.Binary(data))
        )
        conn.commit()
        print(f"Stored {file_name} into database.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
