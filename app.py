from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
import os
import shutil
import uuid



app = FastAPI(
    title="Enterprise AI Chatbot",
    description="RAG-based Enterprise AI Chatbot using FastAPI, Sentence Transformers and ChromaDB",
    version="1.0.0"
)




DOCUMENTS_DIR = "documents"
CHROMA_DIR = "chroma_db"

os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)




print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Embedding model loaded successfully.")



chroma_client = chromadb.PersistentClient(
    path=CHROMA_DIR
)

collection = chroma_client.get_or_create_collection(
    name="enterprise_documents"
)




class ChatRequest(BaseModel):
    question: str




@app.get("/")
def home():
    return {
        "message": "Enterprise AI Chatbot Running",
        "status": "success"
    }



@app.get("/health")
def health():
    return {
        "status": "healthy"
    }



def extract_text_from_pdf(pdf_path: str) -> str:

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text



def create_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100
):

    text = text.strip()

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks




def generate_embeddings(chunks):

    embeddings = embedding_model.encode(
        chunks,
        convert_to_numpy=True
    )

    return embeddings.tolist()



@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    file_id = str(uuid.uuid4())

    safe_filename = f"{file_id}_{file.filename}"

    file_path = os.path.join(
        DOCUMENTS_DIR,
        safe_filename
    )

    try:

        with open(file_path, "wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

       

        text = extract_text_from_pdf(
            file_path
        )

        if not text.strip():

            raise HTTPException(
                status_code=400,
                detail="Could not extract text from the PDF."
            )


        chunks = create_chunks(text)

        if not chunks:

            raise HTTPException(
                status_code=400,
                detail="No text chunks were created."
            )

        

        embeddings = generate_embeddings(chunks)

       

        ids = []

        for index in range(len(chunks)):

            ids.append(
                f"{file_id}_{index}"
            )

        metadatas = []

        for index in range(len(chunks)):

            metadatas.append(
                {
                    "filename": file.filename,
                    "file_id": file_id,
                    "chunk_index": index
                }
            )

        collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas
        )

        return {
            "message": "PDF uploaded successfully",
            "filename": file.filename,
            "file_id": file_id,
            "pages": len(PdfReader(file_path).pages),
            "chunks_created": len(chunks),
            "embeddings_created": len(embeddings)
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )




@app.get("/documents")
def get_documents():

    try:

        files = os.listdir(DOCUMENTS_DIR)

        pdf_files = [
            file
            for file in files
            if file.lower().endswith(".pdf")
        ]

        return {
            "total_documents": len(pdf_files),
            "documents": pdf_files
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



@app.post("/chat")
def chat(request: ChatRequest):

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:

       

        question_embedding = embedding_model.encode(
            question
        ).tolist()

        

        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=5
        )

        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        if not documents:

            return {
                "question": question,
                "answer": "I could not find relevant information in the uploaded documents.",
                "sources": []
            }

       

        context_parts = []

        for index, document in enumerate(documents):

            context_parts.append(
                f"Source {index + 1}:\n{document}"
            )

        context = "\n\n".join(
            context_parts
        )

        
        answer = (
            "Based on the uploaded documents, "
            "the most relevant information is:\n\n"
            + context
        )

     
        sources = []

        for metadata in metadatas:

            if metadata:

                sources.append(
                    {
                        "filename": metadata.get(
                            "filename"
                        ),
                        "chunk_index": metadata.get(
                            "chunk_index"
                        )
                    }
                )

        return {
            "question": question,
            "answer": answer,
            "sources": sources
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



@app.get("/stats")
def get_stats():

    try:

        count = collection.count()

        return {
            "collection": "enterprise_documents",
            "total_chunks": count
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )