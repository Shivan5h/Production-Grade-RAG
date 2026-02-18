# � Production RAG System

AI-powered Retrieval-Augmented Generation system with FastAPI backend and Streamlit frontend.

## 📋 Overview

Production-grade RAG system with:
- **FastAPI** backend with lazy-loaded services (port 8000)
- **Streamlit** UI frontend (port 8502)
- **Groq Llama 3.3 70B** for intelligent responses
- **HuggingFace all-MiniLM-L6-v2** embeddings (384-dim, 80MB)
- **Pinecone** serverless vector database
- **Document comparison** and **data management** features

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=rag-index
PINECONE_DIMENSION=384
```

**Get API Keys:**
- **Groq** (Free): https://console.groq.com/keys
- **Pinecone** (Free tier): https://app.pinecone.io/

### 3. Create Pinecone Index

**Option A: Using Script (Recommended)**
```bash
python recreate_index.py
```

**Option B: Via Pinecone Website**
1. Go to https://app.pinecone.io/
2. Click "Create Index"
3. Configure settings below

**Index Settings:**
- Name: `rag-index`
- Dimensions: `384`
- Metric: `cosine`
- Cloud: `aws` / Region: `us-east-1`

### 4. Start Servers

**Terminal 1 - Start FastAPI:**
```bash
cd app
python main.py
```

**Terminal 2 - Start Streamlit:**
```bash
streamlit run streamlit_app.py
```

**Access:**
- Streamlit UI: http://localhost:8502
- FastAPI Docs: http://localhost:8000/docs

---

## 📦 Project Structure

```
prorag/
├── streamlit_app.py              # Streamlit UI (API client)
├── recreate_index.py             # Pinecone index setup
├── clear_pinecone.py             # Data cleanup utility
├── requirements.txt              # Dependencies
├── .env                          # API keys & config
│
└── app/                          # FastAPI Backend
    ├── main.py                   # FastAPI entry point
    │
    ├── config/
    │   └── settings.py           # Environment config
    │
    ├── routes/
    │   └── rag_routes.py         # API endpoints
    │
    ├── services/
    │   ├── __init__.py           # Lazy service loader
    │   │
    │   ├── rag/
    │   │   ├── embeddings/
    │   │   │   └── embedding_manager.py    # HuggingFace embeddings
    │   │   └── llm/
    │   │       └── groq_generator.py       # Groq LLM
    │   │
    │   └── vectorstore/
    │       └── pinecone_manager.py         # Pinecone ops
    │
    └── utils/
        ├── document_processor.py # PDF/DOCX processing
        └── chunking.py           # Text chunking
```

---

## �️ Architecture

This system uses a **hybrid architecture** with separated backend and frontend for optimal performance:

### **Two-Tier Design:**
1. **FastAPI Backend** (Port 8000) - Heavy processing, model hosting
2. **Streamlit Frontend** (Port 8502) - Lightweight UI, API client

### **Key Components:**
- **Document Processing**: PyPDF2, python-docx for multi-format support
- **Embedding Layer**: HuggingFace all-MiniLM-L6-v2 (384-dim, 80MB)
- **Vector Database**: Pinecone Serverless (cosine similarity)
- **LLM Generation**: Groq Llama 3.3 70B (context-grounded)

### **Data Flow:**
```
Upload: User → FastAPI → Process → Chunk → Embed → Pinecone
Query:  User → FastAPI → Embed Query → Pinecone Search → Groq LLM → Answer
```


---

## �🎯 Features

### ✅ Document Upload & Processing
- Upload PDF, DOCX, TXT, Markdown files
- Automatic chunking (1000 tokens, 200 overlap)
- Batch embedding generation (memory-efficient)
- Metadata extraction with filename tracking
- **Auto-replacement**: Re-uploading replaces old version

### ✅ Intelligent Query
- Natural language questions
- Semantic similarity search (top-k retrieval)
- Context-grounded responses with citations
- Adjustable parameters (temperature, top_p, max_tokens)
- Source attribution with similarity scores

### ✅ Document Comparison
- Compare two documents on same query
- Side-by-side analysis
- Highlights similarities and differences
- Retrieves relevant context from both documents

### ✅ Data Management
- **Clear All Data**: Delete all vectors from UI
- **Delete Individual Documents**: Per-document deletion
- **Clear Script**: Standalone `clear_pinecone.py`
- **Auto-cleanup**: Old versions deleted on re-upload

### ✅ Production Features
- **Lazy Loading**: Models load on first API call
- **Memory Optimized**: 384-dim embeddings (vs 768-dim)
- **Batch Processing**: Prevents memory overflow
- **Error Handling**: Graceful namespace/404 handling
- **CORS Enabled**: Cross-origin API access

---

## 🖥️ Usage Guide

### Upload Documents
1. Open http://localhost:8502
2. Drag & drop files or use file picker
3. Click "🚀 Upload Documents"
4. See uploaded documents list below

### Query Documents
1. Enter question in "🔍 Ask a Question" section
2. Adjust sidebar settings if needed:
   - Top K Results (1-10)
   - Temperature (0-1.0)  
   - Top P (0-1.0)
   - Max Tokens (100-2000)
3. Click "🔍 Search"
4. View answer with source citations

### Compare Documents
1. Go to "📊 Compare Documents" tab
2. Enter your question
3. Select two documents from dropdowns
4. Click "🔄 Compare"
5. View structured comparison

### Manage Data
1. Sidebar → "🗑️ Data Management"
2. Click "Clear All Data" (requires double-click)
3. Or click 🗑️ next to individual documents
4. Re-upload documents for fresh start

---

## 🔌 API Endpoints

### Health Check
```bash
GET http://localhost:8000/health
```

### Upload Document
```bash
POST http://localhost:8000/api/upload
Content-Type: multipart/form-data

file=@document.pdf
```

### Query Documents
```bash
POST http://localhost:8000/api/query
Content-Type: application/json

{
  "query": "What are the main findings?",
  "top_k": 5,
  "temperature": 0.3,
  "top_p": 0.95,
  "max_tokens": 1000
}
```

### Compare Documents
```bash
POST http://localhost:8000/api/compare
Content-Type: application/json

{
  "query": "Compare GDP growth",
  "doc1_name": "report1.pdf",
  "doc2_name": "report2.pdf",
  "top_k": 3,
  "temperature": 0.3,
  "top_p": 0.95,
  "max_tokens": 1500
}
```

### Delete Document
```bash
DELETE http://localhost:8000/api/documents/{filename}
```

### Delete All Documents
```bash
DELETE http://localhost:8000/api/documents
```

**Full API Documentation**: http://localhost:8000/docs

---

## ⚙️ Configuration

All settings in `.env`:

### Core Settings
```env
# Main LLM
GROQ_MODEL=llama-3.3-70b-versatile

# Embeddings (384 dimensions)
HUGGINGFACE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Vector Database
PINECONE_INDEX_NAME=rag-index
PINECONE_DIMENSION=384

# Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Retrieval
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.5
```

### Tuning Tips

**For precise answers:**
```env
TOP_K_RESULTS=3
SIMILARITY_THRESHOLD=0.7
LLM_TEMPERATURE=0.2
```

**For creative exploration:**
```env
TOP_K_RESULTS=8
SIMILARITY_THRESHOLD=0.4
LLM_TEMPERATURE=0.7
```

---

## 🛠️ Utilities

### Recreate Pinecone Index
```bash
python recreate_index.py
```
- Deletes old index (if exists)
- Creates new index with 384 dimensions
- Interactive confirmation required
- **Alternative**: Create index manually at https://app.pinecone.io/

### Clear All Data
```bash
python clear_pinecone.py
```
- Deletes all vectors from Pinecone
- Keeps index structure intact
- Requires 'yes' confirmation

---

## 📊 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI |
| Frontend | Streamlit |
| LLM | Groq Llama 3.3 70B |
| Embeddings | HuggingFace all-MiniLM-L6-v2 (384-dim) |
| Vector DB | Pinecone Serverless |
| Document Parser | PyPDF, python-docx |
| Architecture | Lazy Loading with Service Registry |

---

## 🏗️ Architecture

### System Flow
```
┌─────────────────────────────────────────┐
│   Streamlit UI (Port 8502)              │
│   - Upload documents                     │
│   - Query interface                      │
│   - Compare documents                    │
│   - Data management                      │
└──────────┬──────────────────────────────┘
           │ HTTP REST API
┌──────────▼──────────────────────────────┐
│   FastAPI Backend (Port 8000)           │
│   ┌─────────────────────────────────┐   │
│   │ Lazy Service Loader             │   │
│   │ (Initialize on first call)      │   │
│   └─────────────────────────────────┘   │
│                                          │
│   ┌─────────────────────────────────┐   │
│   │ Document Processing             │   │
│   │ PDF → Text → Chunks             │   │
│   └──────────┬──────────────────────┘   │
│              ▼                           │
│   ┌─────────────────────────────────┐   │
│   │ Embedding Manager               │   │
│   │ all-MiniLM-L6-v2 (384-dim)      │   │
│   └──────────┬──────────────────────┘   │
│              ▼                           │
│   ┌─────────────────────────────────┐   │
│   │ Pinecone Vector DB              │   │
│   │ Cosine similarity search        │   │
│   └──────────┬──────────────────────┘   │
│              ▼                           │
│   ┌─────────────────────────────────┐   │
│   │ Groq LLM (Llama 3.3 70B)        │   │
│   │ Context + Citations             │   │
│   └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### Data Flow

**Upload:**
1. User uploads document → FastAPI
2. Parse PDF/DOCX → Extract text
3. Chunk text (1000 tokens, 200 overlap)
4. Generate embeddings (batch 8 chunks)
5. Store in Pinecone with metadata

**Query:**
1. User enters question → Streamlit
2. API embeds query → 384-dim vector
3. Pinecone similarity search → Top-k chunks
4. Context + Query → Groq LLM
5. Answer with citations → User

---

## 🚨 Troubleshooting

### Memory Issues
- ✅ Already using lightweight model (384-dim)
- ✅ Lazy loading prevents startup memory spike
- ✅ Batch processing (8 chunks at a time)
- If still issues: Reduce `CHUNK_SIZE` to 500

### Pinecone Errors
**"Namespace not found"**
- Normal if no documents uploaded yet
- Upload a document to create namespace

**Dimension mismatch**
```bash
python recreate_index.py
# Recreates index with 384 dimensions
```

### API Connection Failed
```bash
# Check FastAPI is running
curl http://localhost:8000/health

# Check Streamlit backend URL
# Should be: http://localhost:8000/api
```

### Duplicate Documents
- System auto-replaces on re-upload
- Or use "Clear All Data" in sidebar
- Or run: `python clear_pinecone.py`

---

## 🎓 Key Design Decisions

### Why Lazy Loading?
- **Prevents memory overflow** at startup
- Models load only when first needed
- FastAPI starts instantly
- Production-optimized approach

### Why all-MiniLM-L6-v2?
- **384 dimensions** (vs 768 in all-mpnet-base-v2)
- **80MB model** (vs 420MB)
- 81% smaller, minimal quality loss
- Ideal for production deployment

### Why Groq Llama 3.3 70B?
- **Fast inference** on Groq's LPU infrastructure
- Free tier with generous limits
- Excellent reasoning capabilities
- 70B parameter model for complex tasks

### Why Hybrid Architecture?
- **FastAPI**: Heavy processing, model hosting
- **Streamlit**: Lightweight UI, no models loaded
- Clear separation of concerns
- Easy to scale independently

### Hallucination Prevention
1. Context-only responses (no external knowledge)
2. Similarity threshold filtering
3. Mandatory source citations [Source N]
4. Low temperature (0.3 default)
5. Controlled context windows

---

## 📝 Example Workflow

```bash
# 1. Setup
pip install -r requirements.txt
python recreate_index.py  # Create Pinecone index

# 2. Start servers (2 terminals)
# Terminal 1
cd app && python main.py

# Terminal 2  
streamlit run streamlit_app.py

# 3. Use system
# - Open http://localhost:8502
# - Upload PDF documents
# - Ask questions
# - Compare documents
# - Manage data

# 4. Clean up (if needed)
python clear_pinecone.py  # Clear all data
```

---

## 📄 License

MIT License

---

## 🤝 Support

**Common Issues:**
1. Check API keys in `.env`
2. Ensure Pinecone index exists (384 dimensions)
3. Verify both servers running (ports 8000 & 8502)
4. Check internet connection for API calls

**Need help?**
- Check FastAPI logs in Terminal 1
- Check Streamlit logs in Terminal 2
- Visit http://localhost:8000/docs for API testing

---

**Ready to build intelligent document search!** 🚀
- **Document statistics** showing uploaded chunks and files

### ✅ Document Processing
- Upload **PDF**, **DOCX**, **TXT**, **Markdown** files
- Intelligent semantic chunking (preserves context)
- Automatic metadata extraction

### ✅ Smart Search
- **HuggingFace Sentence Transformers** embeddings (all-mpnet-base-v2)
- **Pinecone** vector database (fast, scalable)
- Top-k retrieval with similarity threshold

### ✅ AI Analysis
- **Groq Llama 3.3 70B** for intelligent answers
- Grounded generation (context-only answers)
- Mandatory source citations
- Hallucination reduction strategies

### ✅ Interactive Streamlit UI
- Single-page interface with Upload and Query sections
- Drag-and-drop file upload
- Real-time document processing feedback
- Source citations with similarity scores
- Adjustable query parameters (temperature, top_k, max_tokens)

---

## 🖥️ Usage Guide

### Upload Documents
1. Open **http://localhost:8501** (Streamlit app)
2. Drag & drop files or click **"Browse files"**
3. Supported formats: PDF, DOCX, TXT, Markdown
4. Click **"🚀 Process Documents"**
5. Wait for processing (progress bar shows status)
6. View uploaded documents list below

### Ask Questions
1. Scroll down to **"🔍 Query Documents"** section
2. Enter your question in the text area
3. Adjust settings in the sidebar:
   - Top K Results (1-10)
   - Temperature (0-1.0)
   - Top P (0-1.0)
   - Max Tokens (100-2000)
4. Click **"🔍 Search"**
5. View answer with source citations and similarity scores

---

## 🔌 API Endpoints

The backend provides REST API endpoints at `http://localhost:8000/api`:

### `GET /health`
Health check endpoint
```bash
curl http://localhost:8000/health
```

### `POST /api/upload`
Upload and process documents
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@report.pdf"
```

### `POST /api/query`
Query documents with natural language
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main inflation forecasts?",
    "top_k": 5,
    "temperature": 0.3,
    "top_p": 0.95,
    "max_tokens": 1000
  }'
```
  "top_k": 5,
  "similarity_threshold": 0.7
}
```

### `POST /compare`
Compare two documents
```json
{
  "topic": "GDP growth",
  "document1": "WEO_2023.pdf",
  "document2": "WEO_2024.pdf"
}
```

### `POST /evaluate`
Evaluate RAG response quality
```json
{
  "question": "...",
  "answer": "...",
  "context_chunks": [...],
  "citations": [...]
}
```

Full API docs: http://localhost:8000/docs

---

## ⚙️ Configuration

All settings are in `.env`:

### Key Settings
```env
# LLM
GROQ_MODEL=llama-3.3-70b-versatile

# Embeddings
HUGGINGFACE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Vector Database
PINECONE_INDEX_NAME=rag-index

# Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Retrieval
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.7
```

### Tuning Retrieval

**For precise factual queries:**
```env
TOP_K_RESULTS=3
SIMILARITY_THRESHOLD=0.8
```

**For exploratory analysis:**
```env
TOP_K_RESULTS=8
SIMILARITY_THRESHOLD=0.6
```

---

## 🛠️ Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Try different port
# Edit .env: API_PORT=8001
```

### UI not loading
```bash
# Ensure FastAPI backend is running
cd app
python main.py
# Should see: Uvicorn running on http://0.0.0.0:8000

# Ensure Streamlit is running
streamlit run streamlit_app.py
# Should open browser to: http://localhost:8502
```

### Pinecone errors
- Verify API key in `.env`
- Check index exists (dimension=384, metric=cosine)
- Ensure cloud/region matches (e.g., "aws" / "us-east-1")

### Out of memory
- Reduce `CHUNK_SIZE` to 500
- Reduce `TOP_K_RESULTS` to 3
- Close other applications

### Slow responses
- Check internet connection (API calls)
- Verify Groq API is not rate-limited
- Disable evaluation for faster queries

---

## 📊 Tech Stack

| Component | Technology |
|-----------|-----------|
| UI Framework | Streamlit |
| Embeddings | HuggingFace Sentence Transformers (all-mpnet-base-v2) |
| Vector DB | Pinecone (Serverless) |
| LLM | Groq DeepSeek-R1 Distill Llama 70B |
| Document Processing | PyPDF, python-docx, markdown |
| Architecture | Modular RAG Pipeline |

---

## 🎓 System Architecture & Approach

### Problem-Solving Architecture

The system is built using a **modular, production-grade RAG pipeline**. Document ingestion begins with parsing uploaded files (PDF, DOCX, TXT, Markdown) using appropriate loaders, followed by preprocessing and intelligent chunking with configurable chunk size and overlap to preserve semantic continuity. Each chunk is converted into vector embeddings using HuggingFace Sentence Transformers and stored in Pinecone vector database for scalable retrieval.

For the **`/api/query`** endpoint, user queries are embedded and used to retrieve top-k relevant chunks using similarity search with a defined threshold. Retrieved context is validated and injected into a structured LLM prompt to generate grounded responses with citations.

The **`/api/compare`** endpoint performs parallel retrieval across two documents on a specified topic, then prompts the LLM to generate a structured comparison highlighting key similarities and differences.

**Hallucination is minimized** through strict retrieval grounding, similarity filtering, controlled context windows, and citation-enforced prompting. Configuration is environment-driven for production flexibility and scalability.

### Technical Architecture

```
┌─────────────────────────────────────────────────┐
│     Web UI (HTML/CSS/JS) - Port 8000            │
│  Upload │ Query │ Compare │ Evaluation          │
└────────────────┬────────────────────────────────┘
                 │ HTTP REST API (/api/*)
┌────────────────▼────────────────────────────────┐
│         FastAPI Backend (app/main.py)           │
│  ┌──────────────────────────────────────────┐   │
│  │ Document Processor (utils/)              │   │
│  │ PDF → DOCX → TXT → MD                    │   │
│  └──────────┬───────────────────────────────┘   │
│             ▼                                    │
│  ┌──────────────────────────────────────────┐   │
│  │ Semantic Chunker (utils/chunking.py)     │   │
│  │ 1000 tokens/chunk, 200 overlap           │   │
│  └──────────┬───────────────────────────────┘   │
│             ▼                                    │
│  ┌──────────────────────────────────────────┐   │
│  │ HuggingFace Embeddings (384-dim)         │   │
│  │ services/rag/embeddings/                 │   │
│  └──────────┬───────────────────────────────┘   │
│             ▼                                    │
│  ┌──────────────────────────────────────────┐   │
│  │ Pinecone Vector Database                 │   │
│  │ services/vectorstore/                    │   │
│  │ Semantic Search + Storage                │   │
│  └──────────┬───────────────────────────────┘   │
│             ▼                                    │
│  ┌──────────────────────────────────────────┐   │
│  │ Groq Llama 3.3 70B                       │   │
│  │ services/rag/llm/groq_generator.py       │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### Data Flow

1. **Document Upload** → Parse → Chunk → Embed → Store in Pinecone
2. **Query** → Embed query → Similarity search → Retrieve top-k → Generate answer with citations

---

## 🚨 Important Notes

1. **API Keys Required**: System won't work without valid API keys in `.env`
2. **Pinecone Index**: Must create index manually (dimension=384, metric=cosine)
3. **Single Server**: Everything runs on port 8000 (no separate frontend)
4. **Internet Required**: LLM APIs need internet connection
5. **Python 3.11+**: Ensure compatible Python version

---

## 📝 Example Workflow

```bash
# 1. Setup
pip install -r requirements.txt
# Edit .env with your API keys

# 2. Start Backend (Terminal 1)
cd app
python main.py
# Server starts on http://0.0.0.0:8000

# 3. Start Frontend (Terminal 2)
streamlit run streamlit_app.py
# Opens browser at http://localhost:8502

# 4. Use System
# Upload: Upload PDF/DOCX/TXT files
# Query: "What are the main findings?"
# Compare: Compare two documents
# Manage: Clear data or delete specific documents
```

---

## 🎯 Key Design Decisions

### Why Groq Llama 3.3 70B?
- High-quality language model with 70B parameters
- Ultra-fast inference on Groq's LPU infrastructure
- Superior RAG performance with context awareness
- Free tier with generous limits
- Excellent for complex question answering with citations

### Why Pinecone?
- Serverless (no infrastructure management)
- Free tier sufficient for testing
- Scales to production seamlessly
- Fast similarity search with cosine metric

### Why HuggingFace all-MiniLM-L6-v2?
- Local inference (no API costs)
- Compact embeddings (384-dim vs 768-dim)
- 80MB model size (vs 420MB for larger models)
- No rate limits
- Privacy-preserving (on-premise)
- 81% smaller than all-mpnet-base-v2

### Hallucination Reduction Strategy
1. **Grounded generation** - Context-only answers
2. **Similarity filtering** - Threshold-based retrieval
3. **Controlled context** - Window size limits
4. **Citation enforcement** - Mandatory source references per document
5. **Source mapping** - Clear document-to-source attribution
6. **Low temperature** - Deterministic outputs (0.3 default)
7. **Configurable parameters** - Temperature, top-p, max tokens

---

## 📄 License

MIT License

---

## 🤝 Support

Issues? Check:
1. API keys in `.env` are valid
2. Pinecone index exists with correct dimensions (384)
3. FastAPI backend running on port 8000
4. Streamlit frontend running on port 8502
5. Internet connection is stable
6. Python 3.11+ installed

---

**Ready to analyze documents? Start now!** 🚀

```bash
python start.py
# Then open: http://localhost:8000
```
