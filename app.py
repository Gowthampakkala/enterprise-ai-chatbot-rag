from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
import os
import shutil
import uuid
import re


# --------------------------------------------------
# APPLICATION SETUP
# --------------------------------------------------

app = FastAPI(
    title="Enterprise AI Employee Assistant",
    description=(
        "Enterprise assistant with document RAG, "
        "HR, leave management, and payroll request routing."
    ),
    version="2.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)


# --------------------------------------------------
# EMBEDDING MODEL AND CHROMADB
# --------------------------------------------------

print("Loading embedding model...")

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding model loaded successfully.")

chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

collection = chroma_client.get_or_create_collection(
    name="enterprise_documents"
)


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class ChatRequest(BaseModel):
    question: str


class AgentRequest(BaseModel):
    question: str


# --------------------------------------------------
# DEMONSTRATION EMPLOYEE DATA
# --------------------------------------------------
# These are sample records, NOT real company information.
# Replace them with an authorized employee database later.

DEMO_EMPLOYEES = {
    "EMP001": {
        "leave_balance": 12
    },
    "EMP002": {
        "leave_balance": 8
    },
    "EMP003": {
        "leave_balance": 15
    }
}


# --------------------------------------------------
# BASIC ENDPOINTS
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Enterprise AI Employee Assistant Running",
        "status": "success",
        "version": "2.0.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# --------------------------------------------------
# PDF PROCESSING
# --------------------------------------------------

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

    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Chunk size must be positive, and overlap "
            "must be between zero and chunk size."
        )

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


# --------------------------------------------------
# DOCUMENT RETRIEVAL TOOL
# --------------------------------------------------

def search_documents(question: str):
    question_embedding = embedding_model.encode(
        question
    ).tolist()

    total_chunks = collection.count()

    if total_chunks == 0:
        return {
            "answer": (
                "No documents have been uploaded yet. "
                "Upload relevant HR, payroll, or company "
                "documents first."
            ),
            "sources": []
        }

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(5, total_chunks)
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        return {
            "answer": (
                "I could not find relevant information "
                "in the uploaded documents."
            ),
            "sources": []
        }

    context_parts = []
    sources = []

    for index, document in enumerate(documents):
        context_parts.append(
            f"Source {index + 1}:\n{document}"
        )

        metadata = (
            metadatas[index]
            if index < len(metadatas)
            else None
        )

        if metadata:
            sources.append({
                "filename": metadata.get("filename"),
                "chunk_index": metadata.get("chunk_index")
            })

    context = "\n\n".join(context_parts)

    answer = (
        "Relevant information retrieved from your "
        "uploaded documents:\n\n"
        + context
    )

    return {
        "answer": answer,
        "sources": sources
    }


# --------------------------------------------------
# PDF UPLOAD ENDPOINT
# --------------------------------------------------

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    original_filename = os.path.basename(file.filename)
    file_id = str(uuid.uuid4())

    safe_filename = f"{file_id}_{original_filename}"

    file_path = os.path.join(
        DOCUMENTS_DIR,
        safe_filename
    )

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text = extract_text_from_pdf(file_path)

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

        ids = [
            f"{file_id}_{index}"
            for index in range(len(chunks))
        ]

        metadatas = [
            {
                "filename": original_filename,
                "file_id": file_id,
                "chunk_index": index
            }
            for index in range(len(chunks))
        ]

        collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas
        )

        return {
            "message": "PDF uploaded successfully",
            "filename": original_filename,
            "file_id": file_id,
            "pages": len(PdfReader(file_path).pages),
            "chunks_created": len(chunks),
            "embeddings_created": len(embeddings)
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        await file.close()


# --------------------------------------------------
# LIST UPLOADED DOCUMENTS
# --------------------------------------------------

@app.get("/documents")
def get_documents():
    try:
        pdf_files = [
            file
            for file in os.listdir(DOCUMENTS_DIR)
            if file.lower().endswith(".pdf")
        ]

        return {
            "total_documents": len(pdf_files),
            "documents": pdf_files
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# EXISTING RAG CHAT ENDPOINT
# --------------------------------------------------

@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:
        result = search_documents(question)

        return {
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# LEAVE MANAGEMENT TOOL
# --------------------------------------------------

def get_leave_balance(employee_id: str):
    employee_id = employee_id.upper().strip()

    employee = DEMO_EMPLOYEES.get(employee_id)

    if employee is None:
        return {
            "success": False,
            "message": (
                "Employee not found in the demonstration "
                "employee records."
            )
        }

    return {
        "success": True,
        "employee_id": employee_id,
        "leave_balance": employee["leave_balance"],
        "message": (
            f"{employee_id} has "
            f"{employee['leave_balance']} leave days remaining."
        )
    }


# --------------------------------------------------
# AGENT INTENT CLASSIFICATION
# --------------------------------------------------

def classify_intent(question: str) -> str:
    text = question.lower()

    # Leave-related requests
    leave_keywords = [
        "leave balance",
        "remaining leave",
        "leaves left",
        "leave days",
        "how many leaves",
        "how much leave",
        "check leave",
        "my leave"
    ]

    if any(keyword in text for keyword in leave_keywords):
        return "leave"

    # Payroll-related requests
    payroll_keywords = [
        "payroll",
        "salary",
        "payslip",
        "pay slip",
        "deduction",
        "net pay",
        "gross pay",
        "salary slip"
    ]

    if any(keyword in text for keyword in payroll_keywords):
        return "payroll"

    # HR-related requests
    hr_keywords = [
        "human resources",
        "hr policy",
        "company policy",
        "onboarding",
        "benefits",
        "employee handbook",
        "workplace policy"
    ]

    if any(keyword in text for keyword in hr_keywords):
        return "hr"

    # Other questions are sent to document retrieval.
    return "documents"


# --------------------------------------------------
# ENTERPRISE AI EMPLOYEE ASSISTANT AGENT
# --------------------------------------------------

@app.post("/agent")
def employee_assistant(request: AgentRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:
        intent = classify_intent(question)

        # Tool 1: Leave Management
        if intent == "leave":
            employee_ids = re.findall(
                r"\bEMP\d{3}\b",
                question,
                re.IGNORECASE
            )

            if not employee_ids:
                return {
                    "question": question,
                    "agent": "Leave Management Agent",
                    "tool": "get_leave_balance",
                    "answer": (
                        "Please include an employee ID, "
                        "for example: EMP001. "
                        "This prototype uses demonstration data."
                    ),
                    "sources": []
                }

            result = get_leave_balance(employee_ids[0])

            return {
                "question": question,
                "agent": "Leave Management Agent",
                "tool": "get_leave_balance",
                "answer": result["message"],
                "employee_data": result,
                "sources": []
            }

        # Tool 2: Payroll requests use uploaded documents.
        if intent == "payroll":
            result = search_documents(question)

            return {
                "question": question,
                "agent": "Payroll Agent",
                "tool": "search_documents",
                "answer": result["answer"],
                "sources": result["sources"]
            }

        # Tool 3: HR requests use uploaded documents.
        if intent == "hr":
            result = search_documents(question)

            return {
                "question": question,
                "agent": "HR Agent",
                "tool": "search_documents",
                "answer": result["answer"],
                "sources": result["sources"]
            }

        # Tool 4: General document questions use RAG.
        result = search_documents(question)

        return {
            "question": question,
            "agent": "Document Assistant",
            "tool": "search_documents",
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# PROJECT STATISTICS
# --------------------------------------------------

@app.get("/stats")
def get_stats():
    try:
        return {
            "collection": "enterprise_documents",
            "total_chunks": collection.count()
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )