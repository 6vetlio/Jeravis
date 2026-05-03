import chromadb
from sentence_transformers import SentenceTransformer
import os
import json

# Initialize
client = chromadb.PersistentClient(path="./jarvis_knowledge")
collection = client.get_or_create_collection("jarvis_personal")
embedder = SentenceTransformer('all-MiniLM-L6-v2')  # tiny, fast, local

def add_document(text: str, source: str, doc_id: str = None):
    """Add anything to knowledge base"""
    embedding = embedder.encode(text).tolist()
    doc_id = doc_id or f"{source}_{len(text)}"
    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{"source": source}]
    )

def search(query: str, n_results: int = 3) -> list:
    """Find relevant context for a query"""
    embedding = embedder.encode(query).tolist()
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results
    )
    if results and results['documents']:
        return results['documents'][0]
    return []

def load_memory_into_knowledge(memory_path: str = "memory.json"):
    """Import existing Jarvis memory facts"""
    try:
        with open(memory_path, 'r', encoding='utf-8') as f:
            memory = json.load(f)
        facts = memory.get('facts', [])
        for i, fact in enumerate(facts):
            if fact and len(fact) > 10:
                add_document(fact, "memory", f"memory_{i}")
        print(f"[Knowledge] Loaded {len(facts)} facts from memory")
    except Exception as e:
        print(f"[Knowledge] Failed to load memory: {e}")

def load_conversation_history(history_path: str = "conversation_history.txt"):
    """Import conversation history as searchable context"""
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            content = f.read()
        chunks = [content[i:i+500] for i in range(0, len(content), 500)]
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                add_document(chunk, "conversation", f"conv_{i}")
        print(f"[Knowledge] Loaded {len(chunks)} conversation chunks")
    except Exception as e:
        print(f"[Knowledge] Failed to load history: {e}")

def load_file(filepath: str):
    """Load any text file into knowledge base"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        filename = os.path.basename(filepath)
        chunks = [content[i:i+500] for i in range(0, len(content), 500)]
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                add_document(chunk, filename, f"{filename}_{i}")
        print(f"[Knowledge] Loaded {filename} ({len(chunks)} chunks)")
    except Exception as e:
        print(f"[Knowledge] Failed to load {filepath}: {e}")
