"""Clear all vectors from Pinecone index while keeping index structure."""
import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rag-index")

print("=== Clear Pinecone Index ===\n")
print(f"⚠️  This will delete ALL vectors from index: '{INDEX_NAME}'")
confirm = input("Are you sure? Type 'yes' to confirm: ")

if confirm.lower() != 'yes':
    print("❌ Cancelled")
    exit(0)

try:
    pc = Pinecone(api_key=API_KEY)
    index = pc.Index(INDEX_NAME)
    
    # Get current stats
    try:
        stats = index.describe_index_stats()
        total_vectors = stats.get('total_vector_count', 0)
    except Exception as e:
        # Handle namespace not found (no data uploaded yet)
        if "Namespace not found" in str(e) or "404" in str(e):
            print("\n✅ Index is already empty (no namespace created yet)")
            print("   This is normal if you haven't uploaded any documents.")
            exit(0)
        raise
    
    print(f"\n📊 Current vectors in index: {total_vectors}")
    
    if total_vectors == 0:
        print("✅ Index is already empty")
        exit(0)
    
    # Delete all vectors
    print(f"🗑️  Deleting all vectors...")
    index.delete(delete_all=True)
    
    print("✅ Successfully cleared all data from Pinecone!")
    print(f"   Deleted {total_vectors} vectors")
    print("\n📝 Next steps:")
    print("   1. Restart your FastAPI server")
    print("   2. Re-upload your documents")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("   1. Check PINECONE_API_KEY in .env")
    print("   2. Verify index name is correct")
    print("   3. Check internet connection")
