"""Recreate Pinecone index with 384 dimensions for all-MiniLM-L6-v2 embeddings."""
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import time

load_dotenv()

API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rag-index")
DIMENSION = 384
CLOUD = os.getenv("PINECONE_CLOUD", "aws")
REGION = os.getenv("PINECONE_REGION", "us-east-1")

def recreate_index():
    """Delete old index and create new one with correct dimensions."""
    print(f"Connecting to Pinecone...")
    pc = Pinecone(api_key=API_KEY)
    
    existing_indexes = pc.list_indexes().names()
    
    if INDEX_NAME in existing_indexes:
        print(f"⚠️  Found existing index '{INDEX_NAME}'")
        confirm = input(f"   Delete and recreate with {DIMENSION} dimensions? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("❌ Aborted")
            return
        
        print(f"🗑️  Deleting index '{INDEX_NAME}'...")
        pc.delete_index(INDEX_NAME)
        print("✅ Index deleted")
        time.sleep(5)
    
    print(f"🔨 Creating new index '{INDEX_NAME}' with {DIMENSION} dimensions...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(
            cloud=CLOUD,
            region=REGION
        )
    )
    
    print("⏳ Waiting for index to be ready...")
    while True:
        status = pc.describe_index(INDEX_NAME).status
        if status.get('ready'):
            break
        print("   Still initializing...")
        time.sleep(2)
    
    print(f"✅ Index '{INDEX_NAME}' created successfully!")
    print(f"   Dimension: {DIMENSION}")
    print(f"   Metric: cosine")
    print(f"   Cloud: {CLOUD}")
    print(f"   Region: {REGION}")
    print("\n📝 Next steps:")
    print("   1. Start FastAPI: cd app && python main.py")
    print("   2. Start Streamlit: streamlit run streamlit_app.py")
    print("   3. Upload your documents")

if __name__ == "__main__":
    print("=== Pinecone Index Recreation ===\n")
    try:
        recreate_index()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("   1. Check your PINECONE_API_KEY in .env")
        print("   2. Ensure you have internet connection")
        print("   3. Verify your Pinecone account is active")
