# Enterprise AI Employee Assistant 🤖

An AI-powered employee assistant built with **FastAPI, React, Sentence Transformers, and ChromaDB**. The application helps employees retrieve information from uploaded PDF documents and access basic HR-related information through a simple chat interface.

## 🚀 Features

* **Interactive Chat Interface:** React-based frontend for communicating with the assistant.
* **Employee HR Queries:** Handles supported employee queries, such as checking leave balances.
* **PDF Upload:** Upload PDF documents for text extraction and knowledge retrieval.
* **Semantic Search:** Uses Sentence Transformers embeddings and ChromaDB to retrieve relevant information.
* **REST API:** FastAPI backend with interactive API documentation.
* **Cross-Origin Support:** Configured CORS to allow communication between the frontend and backend.

## 🛠️ Tech Stack

**Frontend**

* React
* Vite
* JavaScript
* CSS

**Backend**

* Python
* FastAPI
* Uvicorn
* Sentence Transformers
* ChromaDB

## 📁 Project Structure

```text
enterprise-ai-chatbot-rag/
├── app.py
├── req.txt
├── readme.md
├── .gitignore
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── documents/
└── chroma_db/
```

*Note: `documents/` and `chroma_db/` are runtime data directories and may be created locally when the application runs.*

## ⚙️ Prerequisites

* Python installed
* Node.js and npm installed
* Git

## 💻 Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Gowthampakkala/enterprise-ai-chatbot-rag.git
cd enterprise-ai-chatbot-rag
```

### 2. Set Up the Backend

Create and activate a virtual environment from the project root.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the Python dependencies:

```powershell
pip install -r req.txt
```

Start the backend server:

```powershell
python -m uvicorn app:app --reload
```

Backend URL: http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

### 3. Set Up the Frontend

Open a **second terminal** in the project root and run:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL shown in the terminal, usually:

http://localhost:5173/

Keep both servers running while using the application.

## 🔍 How It Works

1. The user interacts with the assistant through the React interface.
2. The frontend sends requests to the FastAPI backend.
3. The backend processes supported employee queries or retrieves relevant information from indexed documents.
4. The response is returned to the frontend and displayed in the chat interface.

## 🔮 Future Improvements

* Integrate a large language model for more natural, context-aware responses.
* Improve retrieval-augmented generation (RAG) and answer quality.
* Add Docker support for easier deployment.
* Introduce employee authentication and role-based access.
* Deploy the application to a cloud platform.

## 👨‍💻 Author

**Gowtham Pakkala**

GitHub: https://github.com/Gowthampakkala

---

*This project is being developed as a learning project focused on AI, document retrieval, and full-stack application development.*
