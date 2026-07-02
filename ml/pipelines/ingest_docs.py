"""
RAG document ingestion pipeline.
Run: python ml/pipelines/ingest_docs.py
Place .txt or .pdf files in ml/data/raw/ before running.
"""
import os, pickle
import numpy as np

RAW_DIR = "ml/data/raw"
INDEX_DIR = "ml/artifacts/faiss_index"
os.makedirs(INDEX_DIR, exist_ok=True)


def load_text_files(directory):
    docs = []
    for fname in os.listdir(directory):
        path = os.path.join(directory, fname)
        if fname.endswith(".txt"):
            with open(path, encoding="utf-8") as f:
                docs.append({"text": f.read(), "source": fname})
        elif fname.endswith(".pdf"):
            try:
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    text = " ".join([page.extract_text() or "" for page in pdf.pages])
                docs.append({"text": text, "source": fname})
            except Exception as e:
                print(f"Skipping {fname}: {e}")
    return docs


def semantic_chunk(text, max_chars=512, overlap=64):
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i + max_chars]
        chunks.append(chunk)
        i += max_chars - overlap
    return chunks


def main():
    print("Loading documents...")
    docs = load_text_files(RAW_DIR)
    if not docs:
        print(f"No documents found in {RAW_DIR}. Add .txt or .pdf files there first.")
        return

    print(f"Loaded {len(docs)} documents. Chunking...")
    all_chunks = []
    for doc in docs:
        chunks = semantic_chunk(doc["text"])
        for c in chunks:
            if len(c.strip()) > 20:
                all_chunks.append({"text": c.strip(), "source": doc["source"]})

    print(f"Created {len(all_chunks)} chunks. Embedding...")
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = embedder.encode([c["text"] for c in all_chunks], show_progress_bar=True).astype(np.float32)

    print("Building FAISS index...")
    import faiss
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, f"{INDEX_DIR}/index.faiss")
    with open(f"{INDEX_DIR}/chunks.pkl", "wb") as f:
        pickle.dump(all_chunks, f)

    print(f"Done. Index has {index.ntotal} vectors, saved to {INDEX_DIR}")


if __name__ == "__main__":
    main()
