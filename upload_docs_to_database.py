"""
One-time script to upload legal documents to database
Run this locally before deploying to Streamlit Cloud
"""

import psycopg2
import PyPDF2
import os
from datetime import datetime

# TODO: Replace with your Supabase connection URL
# Get this from: Supabase Dashboard > Project Settings > Database > Connection string
DB_URL = "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT].supabase.co:5432/postgres"

def extract_pdf_text(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def upload_document(conn, doc_name, doc_type, file_path, version="1.0"):
    """Upload document to database"""
    print(f"\n📄 Processing: {doc_name}")
    print(f"   File: {file_path}")

    if not os.path.exists(file_path):
        print(f"   ❌ File not found: {file_path}")
        return False

    # Extract text from PDF
    print(f"   📖 Extracting text...")
    content = extract_pdf_text(file_path)

    if not content:
        print(f"   ❌ Could not extract text")
        return False

    word_count = len(content.split())
    print(f"   ✓ Extracted {word_count} words")

    # Insert or update in database
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO legal_documents (document_name, document_type, content, version, metadata)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (document_name)
            DO UPDATE SET
                content = EXCLUDED.content,
                last_updated = NOW(),
                version = EXCLUDED.version,
                metadata = EXCLUDED.metadata
        """, (
            doc_name,
            doc_type,
            content,
            version,
            {'word_count': word_count, 'file_name': os.path.basename(file_path)}
        ))

        conn.commit()
        print(f"   ✅ Uploaded successfully to database!")
        return True

    except Exception as e:
        print(f"   ❌ Database error: {e}")
        conn.rollback()
        return False

def main():
    print("=" * 70)
    print("LEGAL DOCUMENTS DATABASE UPLOAD")
    print("=" * 70)
    print()

    # Check DB_URL is configured
    if "[YOUR-PASSWORD]" in DB_URL or "[YOUR-PROJECT]" in DB_URL:
        print("❌ ERROR: Please configure DB_URL in this script first!")
        print()
        print("Steps:")
        print("1. Go to supabase.com")
        print("2. Create account and new project")
        print("3. Get connection string from: Settings > Database")
        print("4. Update DB_URL variable at the top of this script")
        print()
        return

    # Connect to database
    print("🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(DB_URL)
        print("✅ Connected successfully!")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print()
        print("Make sure:")
        print("1. Supabase project is running")
        print("2. Connection URL is correct")
        print("3. Password is correct")
        print("4. pip install psycopg2-binary is installed")
        return

    # Check if table exists
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'legal_documents'
            );
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            print("❌ Table 'legal_documents' does not exist!")
            print()
            print("Please run this SQL in Supabase SQL Editor first:")
            print()
            print("""
CREATE TABLE legal_documents (
    id SERIAL PRIMARY KEY,
    document_name VARCHAR(255) NOT NULL UNIQUE,
    document_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    last_updated TIMESTAMP DEFAULT NOW(),
    version VARCHAR(20),
    metadata JSONB
);

CREATE INDEX idx_document_name ON legal_documents(document_name);
CREATE INDEX idx_document_type ON legal_documents(document_type);
            """)
            print()
            conn.close()
            return

        print("✅ Table 'legal_documents' exists")
        print()

    except Exception as e:
        print(f"❌ Error checking table: {e}")
        conn.close()
        return

    # Upload documents
    print("📚 Uploading documents...")
    print()

    documents = [
        {
            'name': 'priority_deed',
            'type': 'legal_agreement',
            'path': 'Priority Deed/priority_deed.pdf',  # Adjust path as needed
            'version': '1.0'
        },
        {
            'name': 'fca_redress_scheme',
            'type': 'regulatory',
            'path': 'FCA redress scheme/Redress Scheme.pdf',  # Adjust path as needed
            'version': '1.0'
        },
        {
            'name': 'milberg_agreement',
            'type': 'legal_agreement',
            'path': 'Milberg Lawfirm Agreement/agreement.pdf',  # Adjust path as needed
            'version': '1.0'
        }
    ]

    success_count = 0
    for doc in documents:
        if upload_document(conn, doc['name'], doc['type'], doc['path'], doc['version']):
            success_count += 1

    # Summary
    print()
    print("=" * 70)
    print("UPLOAD SUMMARY")
    print("=" * 70)
    print(f"Total documents: {len(documents)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(documents) - success_count}")
    print()

    if success_count == len(documents):
        print("✅ All documents uploaded successfully!")
        print()
        print("Next steps:")
        print("1. Add database credentials to Streamlit Secrets")
        print("2. Update pcp_funding_agent.py to use database")
        print("3. Deploy to Streamlit Cloud")
    else:
        print("⚠️  Some documents failed to upload")
        print("Check the file paths and try again")

    print()

    # Verify uploads
    print("🔍 Verifying uploads...")
    cursor.execute("SELECT document_name, document_type, version, last_updated FROM legal_documents")
    rows = cursor.fetchall()

    if rows:
        print()
        print("Documents in database:")
        for row in rows:
            print(f"  • {row[0]} ({row[1]}) - v{row[2]} - Updated: {row[3]}")
    else:
        print("  No documents found in database")

    conn.close()
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()
