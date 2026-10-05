# Enterprise AI Chatbot - RAG

An Enterprise AI Chatbot backend built using FastAPI, Sentence Transformers, ChromaDB, and Retrieval-Augmented Generation (RAG).

This project allows users to upload PDF documents, extract their text, generate semantic embeddings, store the embeddings in ChromaDB, and retrieve relevant information through a chat API.

## Features

- PDF document upload
- PDF text extraction
- Text chunking
- Semantic embeddings
- Sentence Transformers
- ChromaDB vector database
- Semantic document search
- Retrieval-Augmented Generation (RAG) workflow
- FastAPI REST APIs
- Swagger API documentation
- Source document tracking

## Technology Stack

- Python
- FastAPI
- Uvicorn
- PyPDF
- Sentence Transformers
- ChromaDB

## RAG Workflow

```text
PDF Document
     |
     v
Text Extraction
     |
     v
Text Chunking
     |
     v
Sentence Transformer
     |
     v
Embeddings
     |
     v
ChromaDB
     |
     v
User Question
     |
     v
Question Embedding
     |
     v
Semantic Search
     |
     v
Relevant Document Chunks
     |
     v
Chat API Response