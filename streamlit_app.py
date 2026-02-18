import streamlit as st
import requests
import logging

# API Configuration
API_BASE_URL = "http://localhost:8000/api"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="AI RAG System",
    page_icon="📊",
    layout="wide"
)

# Check API health
def check_api_health():
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        logger.info(f"Health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False

# Initialize session state
if 'uploaded_docs' not in st.session_state:
    st.session_state.uploaded_docs = []
if 'api_checked' not in st.session_state:
    st.session_state.api_checked = False

# Header
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>📊 AI RAG System</h1>
    <p>Production-Grade Document Analysis with Llama 3.3 70B</p>
</div>
""", unsafe_allow_html=True)

# Check if API is available (show warning but don't block)
if 'last_check' not in st.session_state or st.button("🔄 Refresh Connection", key="refresh_api"):
    api_available = check_api_health()
    st.session_state.last_check = api_available
    
if st.session_state.get('last_check', False):
    st.success("✅ FastAPI backend is connected")
else:
    st.warning("⚠️ Cannot connect to FastAPI backend")
    st.info("**Start the backend**: Open a terminal and run: `cd app && python main.py`")
    st.info("**API URL**: http://localhost:8000")
    st.info("**Click 'Refresh Connection' above after starting the backend**")

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("Query Settings")
    top_k = st.slider("Top K Results", 1, 10, 5)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1)
    top_p = st.slider("Top P", 0.0, 1.0, 0.95, 0.05)
    max_tokens = st.slider("Max Tokens", 100, 2000, 1000, 100)
    
    st.divider()
    st.subheader("🗑️ Data Management")
    
    if st.button("🗑️ Clear All Data", type="secondary", use_container_width=True):
        if st.session_state.get('confirm_delete', False):
            try:
                response = requests.delete(f"{API_BASE_URL}/documents", timeout=10)
                if response.status_code == 200:
                    st.success("✅ All data cleared!")
                    st.session_state.uploaded_docs = []
                    st.session_state.confirm_delete = False
                    st.rerun()
                else:
                    st.error(f"Failed: {response.text}")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.session_state.confirm_delete = True
            st.warning("⚠️ Click again to confirm deletion")
    
    if st.session_state.get('confirm_delete', False):
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.confirm_delete = False
            st.rerun()

# Main content
st.header("📤 Upload & Query Documents")

# Upload Section
st.subheader("📄 Upload Documents")
st.info("📝 **Note:** Re-uploading a document with the same name will automatically replace the old version (prevents duplicates)")

uploaded_files = st.file_uploader(
    "Choose files",
    type=['pdf', 'docx', 'txt', 'md'],
    accept_multiple_files=True,
    help="Select documents to upload"
)

if uploaded_files:
    if st.button("🚀 Upload & Process", type="primary"):
        progress_bar = st.progress(0)
        status = st.empty()
        
        for idx, file in enumerate(uploaded_files):
            status.text(f"Uploading {file.name}...")
            
            try:
                # Send file to FastAPI
                files = {'file': (file.name, file.getvalue(), file.type)}
                response = requests.post(
                    f"{API_BASE_URL}/upload",
                    files=files,
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Uploaded {file.name}: {data.get('chunks_created', 0)} chunks")
                    if file.name not in st.session_state.uploaded_docs:
                        st.session_state.uploaded_docs.append(file.name)
                else:
                    st.error(f"Failed to upload {file.name}: {response.text}")
                
            except Exception as e:
                st.error(f"Error uploading {file.name}: {str(e)}")
            
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        status.text("✅ All documents processed!")
        st.success(f"Successfully uploaded {len(uploaded_files)} document(s)")
        st.balloons()

# Show uploaded documents
if st.session_state.uploaded_docs:
    st.divider()
    st.subheader(f"📑 Uploaded Documents ({len(st.session_state.uploaded_docs)})")
    
    for doc in st.session_state.uploaded_docs:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.info(f"📄 {doc}")
        with col2:
            if st.button("🗑️", key=f"delete_{doc}", help=f"Delete {doc}"):
                try:
                    response = requests.delete(
                        f"{API_BASE_URL}/documents/{doc}",
                        timeout=10
                    )
                    if response.status_code == 200:
                        st.session_state.uploaded_docs.remove(doc)
                        st.success(f"Deleted {doc}")
                        st.rerun()
                    else:
                        st.error(f"Failed: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

# Query Section
st.divider()
st.subheader("🔍 Query Documents")

query = st.text_area(
    "Enter your question:",
    placeholder="e.g., What are the main findings?",
    height=100
)

if st.button("🔍 Search", type="primary", use_container_width=True):
    if not query:
        st.warning("Please enter a question")
    else:
        with st.spinner("🤔 Searching and generating answer..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/query",
                    json={
                        "query": query,
                        "top_k": top_k,
                        "temperature": temperature,
                        "top_p": top_p,
                        "max_tokens": max_tokens
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    st.success("✅ Answer Generated")
                    st.markdown("### 💡 Answer")
                    st.markdown(f"**Model:** {data.get('model', 'Unknown')}")
                    st.markdown(data.get('answer', 'No answer'))
                    
                    # Display source mapping (which source # = which document)
                    source_mapping = data.get('source_mapping', {})
                    if source_mapping:
                        st.markdown("---")
                        st.markdown("**📚 Source Documents:**")
                        for source_num, filename in source_mapping.items():
                            st.markdown(f"- **{source_num}:** {filename}")
                    
                else:
                    st.error(f"❌ API Error: {response.status_code}")
                    st.error(response.text)
                
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API server")
                st.info("Make sure FastAPI is running on port 8000")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Compare Documents Section
st.divider()
st.subheader("⚖️ Compare Documents")

# Get list of documents from API
try:
    docs_response = requests.get(f"http://localhost:8000/api/documents", timeout=5)
    if docs_response.status_code == 200:
        available_docs = docs_response.json().get('documents', [])
    else:
        available_docs = st.session_state.uploaded_docs
except:
    available_docs = st.session_state.uploaded_docs

if len(available_docs) >= 2:
    col1, col2 = st.columns(2)
    
    with col1:
        doc1 = st.selectbox(
            "📄 Select First Document",
            options=available_docs,
            key="doc1_select"
        )
    
    with col2:
        doc2 = st.selectbox(
            "📄 Select Second Document",
            options=[d for d in available_docs if d != doc1],
            key="doc2_select"
        )
    
    compare_query = st.text_area(
        "What would you like to compare?",
        placeholder="e.g., Compare the key findings, methodologies, or conclusions",
        height=80,
        key="compare_query"
    )
    
    if st.button("⚖️ Compare Documents", type="primary", use_container_width=True):
        if not compare_query:
            st.warning("Please enter what you want to compare")
        elif doc1 == doc2:
            st.warning("Please select two different documents")
        else:
            with st.spinner("🔄 Analyzing and comparing documents..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/compare",
                        json={
                            "query": compare_query,
                            "doc1_name": doc1,
                            "doc2_name": doc2,
                            "top_k": top_k,
                            "temperature": temperature,
                            "top_p": top_p,
                            "max_tokens": max_tokens * 1.5  # More tokens for comparison
                        },
                        timeout=90
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        st.success("✅ Comparison Complete")
                        
                        # Display comparison metadata
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Document 1 Chunks", data.get('doc1_chunks_found', 0))
                        with col_b:
                            st.metric("Document 2 Chunks", data.get('doc2_chunks_found', 0))
                        with col_c:
                            st.metric("Model", data.get('model', 'Unknown').split('-')[0])
                        
                        # Display comparison result
                        st.markdown("### ⚖️ Comparison Analysis")
                        st.markdown(f"**Comparing:** `{doc1}` vs `{doc2}`")
                        st.markdown(data.get('comparison', 'No comparison generated'))
                        
                    else:
                        st.error(f"❌ API Error: {response.status_code}")
                        st.error(response.text)
                    
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API server")
                    st.info("Make sure FastAPI is running on port 8000")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
elif len(available_docs) == 1:
    st.info("📌 Upload at least one more document to enable comparison")
else:
    st.info("📌 Upload at least two documents to enable comparison")

