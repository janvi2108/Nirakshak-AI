import logging
import pickle
import numpy as np
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.index = None
        self.chunks = []
        self.embedder = None
        self._load()

    def _load(self):
        index_path = Path(settings.ml_artifacts_path) / "faiss_index" / "index.faiss"
        chunks_path = Path(settings.ml_artifacts_path) / "faiss_index" / "chunks.pkl"
        if not index_path.exists() or not chunks_path.exists():
            logger.warning("FAISS index not found. Run ml/pipelines/ingest_docs.py first.")
            return
        try:
            import faiss
            self.index = faiss.read_index(str(index_path))
            with open(chunks_path, "rb") as f:
                self.chunks = pickle.load(f)
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            logger.info(f"RAG loaded: {len(self.chunks)} chunks")
        except Exception as e:
            logger.error(f"RAG load failed: {e}")

    def ensure_loaded(self):
        if self.index is None or self.embedder is None:
            self._load()

    def _chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
        chunks = []
        start = 0
        text = text.strip()
        while start < len(text):
            chunk = text[start:start + chunk_size].strip()
            if chunk:
                chunks.append(chunk)
            start += chunk_size - overlap
        return chunks

    def search(self, query: str, k: int = 5) -> list:
        self.ensure_loaded()
        if self.index is None or self.embedder is None:
            return []
        try:
            query_vec = self.embedder.encode([query]).astype(np.float32)
            scores, indices = self.index.search(query_vec, k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.chunks):
                    chunk = self.chunks[idx]
                    results.append({"chunk_text": chunk["text"], "source_doc": chunk.get("source", "unknown"),
                                    "score": float(score)})
            return results
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return []

    def answer_query(self, query: str, language: str = "en", session_history: list = None) -> dict:
        retrieved = self.search(query, k=5)
        if not retrieved:
            return {
                "answer": "I don't have enough information to answer that. Please contact your district office.",
                "sources": [], "language": language,
            }
        context = "\n\n".join([f"[{r['source_doc']}]: {r['chunk_text']}" for r in retrieved[:3]])
        lang_instruction = "Answer in Hindi (हिंदी)." if language == "hi" else "Answer in English."
        prompt = f"""You are a helpful Indian government service assistant.
Answer using ONLY the provided context. Do not add unsupported facts.
If the user asks how to apply for a certificate, give step-by-step instructions.
If the user asks what documents are needed, list them clearly.
Cite the source documents in brackets at the end of the answer.

Answer in Hindi if language is hi, otherwise answer in English.

Context:
{context}

Question: {query}
Answer:"""
        try:
            from app.services.llm_adapter import chat_completion
            answer = chat_completion(prompt, model="groq/compound-mini", max_tokens=500, temperature=0)
        except Exception as e:
            logger.warning(f"LLM call failed: {e}. Using retrieval summary.")
            answer = f"Based on available documents: {retrieved[0]['chunk_text'][:300]}..."
        return {
            "answer": answer,
            "sources": [{"source_doc": r["source_doc"], "chunk_text": r["chunk_text"][:200], "score": r["score"]}
                        for r in retrieved[:3]],
            "language": language,
        }

    def add_documents(self, texts: list[str] | str, source_name: str) -> int:
        if self.embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            except Exception as e:
                logger.error(f"Cannot load embedder: {e}")
                return 0

        if isinstance(texts, str):
            texts = [texts]

        chunks = []
        for text in texts:
            if not isinstance(text, str):
                continue
            for chunk_text in self._chunk_text(text):
                chunks.append({"text": chunk_text, "source": source_name})

        if not chunks:
            return 0

        embeddings = self.embedder.encode([c["text"] for c in chunks]).astype(np.float32)
        try:
            import faiss
            if self.index is None:
                self.index = faiss.IndexFlatL2(embeddings.shape[1])
            self.index.add(embeddings)
            self.chunks.extend(chunks)
            index_dir = Path(settings.ml_artifacts_path) / "faiss_index"
            index_dir.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(index_dir / "index.faiss"))
            with open(index_dir / "chunks.pkl", "wb") as f:
                pickle.dump(self.chunks, f)
            return len(chunks)
        except Exception as e:
            logger.error(f"Add documents failed: {e}")
            return 0


rag_service = RAGService()
