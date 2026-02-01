import re

# Optional: estimate tokens roughly for small LLMs
def estimate_tokens(text: str) -> int:
    """
    Rough token estimation: 1 token ~ 4 characters
    """
    return max(1, len(text) // 4)

def chunk_text(text: str, doc_name: str, page_number: int, max_tokens: int = 500, overlap: int = 50):
    """
    Break a page's text into chunks with metadata.
    
    Args:
        text: Full text of a page
        doc_name: PDF filename
        page_number: 1-indexed page
        max_tokens: Approximate tokens per chunk
        overlap: Number of tokens to overlap between chunks
    
    Returns:
        List of dicts:
        [
            {
                "text": "...",
                "doc_name": "...",
                "page_number": ...
            },
            ...
        ]
    """
    chunks = []

    # Clean text
    clean_text = re.sub(r'\s+', ' ', text).strip()
    if not clean_text:
        return chunks

    words = clean_text.split(' ')
    start_idx = 0
    while start_idx < len(words):
        end_idx = start_idx + max_tokens
        chunk_words = words[start_idx:end_idx]
        chunk_text = ' '.join(chunk_words)

        chunk_data = {
            "text": chunk_text,
            "doc_name": doc_name,
            "page_number": page_number
        }
        chunks.append(chunk_data)

        # Move start index with overlap
        start_idx = end_idx - overlap

    return chunks
