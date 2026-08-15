from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
import os
import warnings

# Suppress transformers warnings and progress bars
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

class VectorStore:
    def __init__(self, persist_dir: str = "vector_db"):
        """
        Initialize Chroma vector DB and embeddings model.
        """
        # Use local ChromaDB with persistence
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection_name = "medical_docs"

        # Create or get collection
        if self.collection_name in [c.name for c in self.client.list_collections()]:
            self.collection = self.client.get_collection(self.collection_name)
        else:
            self.collection = self.client.create_collection(
                name=self.collection_name
            )

        # Embeddings model (suppress output during loading)
        import sys
        from io import StringIO
        
        # Temporarily redirect stdout/stderr to suppress loading messages
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        
        try:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")  # free & lightweight
        finally:
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def document_exists(self, doc_name: str) -> bool:
        """
        Check if a document with this name already exists in the database.
        
        Args:
            doc_name: The name of the document to check
            
        Returns:
            True if document exists, False otherwise
        """
        results = self.collection.get(
            where={"doc_name": doc_name},
            limit=1
        )
        return len(results['ids']) > 0

    def delete_document(self, doc_name: str):
        """
        Delete all chunks belonging to a specific document.
        
        Args:
            doc_name: The name of the document to delete
        """
        # Get all chunks for this document
        results = self.collection.get(
            where={"doc_name": doc_name}
        )
        
        if results['ids']:
            # Delete all chunks with matching document name
            self.collection.delete(ids=results['ids'])
            return len(results['ids'])
        return 0

    def add_chunk(self, chunk: dict):
        """
        Add a single chunk to ChromaDB with metadata.
        chunk: {
            "text": str,
            "doc_name": str,
            "page_number": int
        }
        """
        text = chunk["text"]
        metadata = {
            "doc_name": chunk["doc_name"],
            "page_number": chunk["page_number"],
            "document_id": chunk.get("document_id", chunk["doc_name"])
        }
        embedding = self.model.encode(text).tolist()

        # Generate unique ID for this chunk
        chunk_id = f"{chunk['doc_name']}_page{chunk['page_number']}_{hash(text) % 10**8}"

        self.collection.add(
            ids=[chunk_id],
            documents=[text],
            metadatas=[metadata],
            embeddings=[embedding]
        )

    def similarity_search(self, query: str, top_k: int = 5):
        """
        Retrieve top-k most similar chunks for a query with document diversity.
        Ensures results include chunks from multiple documents when available.
        Returns: list of dicts with text + metadata
        """
        query_embedding = self.model.encode(query).tolist()

        # Retrieve more results initially to ensure diversity
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k * 4, 30)  # Get more results for diversity
        )

        # Build list of all candidates with their scores
        all_candidates = []
        distances = results.get('distances', [[]])[0] if results.get('distances') else []
        for index, (text, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            all_candidates.append({
                "text": text,
                "doc_name": meta["doc_name"],
                "page_number": meta["page_number"],
                "document_id": meta.get("document_id", meta["doc_name"]),
                "score": 1 / (1 + distances[index]) if index < len(distances) else 0.0
            })
        
        # Diversified selection: ensure at least one from each document
        retrieved = []
        seen_docs = set()
        
        # First pass: Get one chunk from each unique document
        for candidate in all_candidates:
            if candidate["doc_name"] not in seen_docs:
                retrieved.append(candidate)
                seen_docs.add(candidate["doc_name"])
                if len(retrieved) >= top_k:
                    break
        
        # Second pass: Fill remaining slots with best remaining matches
        for candidate in all_candidates:
            if len(retrieved) >= top_k:
                break
            if candidate not in retrieved:
                retrieved.append(candidate)
        
        return retrieved[:top_k]
