from pathlib import Path
import psycopg
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag_graph import EMBEDDINGS, store, PG_CONN

PDF = Path("data/hipaa.pdf").resolve()
assert PDF.exists(), "Поместите PDF в data/hipaa.pdf"

with psycopg.connect(PG_CONN.replace("+psycopg", "")) as conn:
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()

loader = PyPDFLoader(str(PDF))
docs = loader.load()
chunks = RecursiveCharacterTextSplitter(
    chunk_size=1024, chunk_overlap=128
).split_documents(docs)

print(f"Ingest {len(chunks)} chunks …")
_ = store().add_documents(chunks)
print("Done.")
