from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, StringConstraints
from typing import Annotated
from pathlib import Path
from uuid import uuid4
import shutil

from test import process_doc

from vector_store import search_chunks
from llm_service import generate_answer

from s3_service import upload_pdf_to_s3

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to RAG PDF Chat"}

@app.get("/about")
def about():
    return {
        "project": "RAG PDF Chat",
        "backend": "FastAPI",
        "version": "1.0"
    }

class ChatRequest(BaseModel):
    question: Annotated[
        str,
        StringConstraints(
            min_length=1,
            strip_whitespace=True
        )
    ]
    doc_id: str | None = None

@app.post("/chat")
def chat(request: ChatRequest):
    documents = search_chunks(
        question=request.question,
        doc_id=request.doc_id
    )

    if not documents:
        return {
            "answer": "No relevant document content found."
        }

    for index, doc in enumerate(documents, start=1):
        print(f"\n===== Retrieved Chunk {index} =====")
        print("Metadata:", doc.metadata)
        print("Content:", doc.page_content)

    answer = generate_answer(
        question=request.question,
        documents=documents
    )

    return {"answer": answer[0]["text"]}


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/documents")
def upload_document(file: UploadFile = File(...)):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    document_id = str(uuid4())
    file_path = UPLOAD_DIR / f"{document_id}.pdf"

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    # Upload PDF to AWS S3
    s3_key = upload_pdf_to_s3(str(file_path), document_id)

    process_doc(document_id)

    return {
        "document_id": document_id,
        "filename": file.filename,
        "s3_key": s3_key,
        "message": "PDF saved successfully"
    }
