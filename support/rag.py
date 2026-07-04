import hashlib
import json
import math
import os
import re
from pathlib import Path

from pypdf import PdfReader


EMBEDDING_DIMENSION = 384
INDEX_PATH = Path("support/documents/rag_index.json")


def _tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _hash_token(token):
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % EMBEDDING_DIMENSION


def embed_text(text):
    vector = [0.0] * EMBEDDING_DIMENSION

    for token in _tokenize(text):
        vector[_hash_token(token)] += 1.0

    norm = math.sqrt(sum(value * value for value in vector))
    if norm:
        vector = [value / norm for value in vector]

    return vector


def _cosine_similarity(left, right):
    return sum(left_value * right_value for left_value, right_value in zip(left, right))


def _load_index():
    if not INDEX_PATH.exists():
        return []

    with INDEX_PATH.open("r", encoding="utf-8") as index_file:
        return json.load(index_file)


def _save_index(records):
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("w", encoding="utf-8") as index_file:
        json.dump(records, index_file, ensure_ascii=False, indent=2)


def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0

    for word in words:
        current_chunk.append(word)
        current_size += len(word) + 1

        if current_size >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_size = 0

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def load_documents():
    docs_path = Path("support/documents")

    records = []

    for filename in sorted(os.listdir(docs_path)):
        if not filename.endswith(".pdf"):
            continue

        filepath = docs_path / filename
        reader = PdfReader(str(filepath))

        raw_text = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            raw_text += page_text + "\n"

        chunks = chunk_text(raw_text, chunk_size=500)

        for index, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if not chunk:
                continue

            records.append(
                {
                    "id": f"{filename}_{index}",
                    "source": filename,
                    "text": chunk,
                    "embedding": embed_text(chunk),
                }
            )

    _save_index(records)
    print(f"Loaded {len(records)} chunks into the local RAG index")


def search_knowledge_base(query):
    records = _load_index()
    if not records:
        return "No relevant information found in company documents."

    query_embedding = embed_text(query)
    scored_chunks = sorted(
        (
            (_cosine_similarity(query_embedding, record["embedding"]), record["text"])
            for record in records
            if record.get("embedding")
        ),
        reverse=True,
    )

    matched_chunks = [chunk for score, chunk in scored_chunks[:3] if score > 0]
    if not matched_chunks:
        return "No relevant information found in company documents."

    print("DEBUG RESULTS:", matched_chunks)
    return "\n\n".join(matched_chunks)
