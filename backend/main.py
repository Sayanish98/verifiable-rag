from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from typing import List

# Import our helper modules (we'll create these next)
from ocr import extract_text_from_pdf
from chunking import chunk_text
from vectorstore import VectorStore
from rag import retrieve_and_answer

# Initialize FastAPI
app = FastAPI(title="Verifiable RAG POC")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ChromaDB Vector Store
vector_store = VectorStore("vector_db")  # local folder


@app.post("/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Upload multiple PDFs (scanned or text-based).
    Extract text per page, OCR if needed, chunk, and store embeddings.
    Checks for duplicate uploads.
    """
    processed_files = []
    skipped_files = []
    
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a PDF")

        # Check if document already exists
        if vector_store.document_exists(file.filename):
            skipped_files.append(file.filename)
            continue

        # Save temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # Extract text per page, OCR if needed
        pages = extract_text_from_pdf(temp_path, file.filename)

        # Chunk pages and store in vector DB
        for page_number, page_text in pages.items():
            chunks = chunk_text(page_text, file.filename, page_number)
            for chunk in chunks:
                vector_store.add_chunk(chunk)

        os.remove(temp_path)
        processed_files.append(file.filename)

    # Build response message
    message_parts = []
    if processed_files:
        message_parts.append(f"{len(processed_files)} file(s) uploaded successfully")
    if skipped_files:
        message_parts.append(f"{len(skipped_files)} file(s) skipped (already uploaded): {', '.join(skipped_files)}")
    
    return {
        "status": "success", 
        "message": ". ".join(message_parts),
        "processed": processed_files,
        "skipped": skipped_files
    }


from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    question: str
    conversation_history: Optional[List[dict]] = None

class DeleteDocumentRequest(BaseModel):
    doc_name: str

@app.post("/query")
async def query_question(request: QueryRequest):
    """
    Accept a user question, retrieve evidence from vector DB,
    generate answer with LLM only if evidence exists.
    Supports conversation context for follow-up questions.
    """
    try:
        answer, evidence = retrieve_and_answer(
            request.question, 
            vector_store,
            conversation_history=request.conversation_history
        )
        return JSONResponse(content={"answer": answer, "evidence": evidence})
    except Exception as e:
        # Log the actual error for debugging
        import traceback
        print(f"Error in /query: {str(e)}")
        traceback.print_exc()
        return JSONResponse(
            content={
                "answer": "An error occurred while processing your question. Please try again.",
                "evidence": []
            },
            status_code=200
        )


@app.delete("/delete-document")
async def delete_document(request: DeleteDocumentRequest):
    """
    Delete all chunks of a specific document from the vector database.
    """
    try:
        deleted_count = vector_store.delete_document(request.doc_name)
        return JSONResponse(content={
            "status": "success", 
            "message": f"Deleted {deleted_count} chunks from '{request.doc_name}'"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
