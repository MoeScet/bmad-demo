#!/usr/bin/env python3
"""
Simple test to verify ChromaDB connection and vector database functionality
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import chromadb
    import httpx
    print("✅ Required packages available")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    sys.exit(1)

async def test_chromadb_direct():
    """Test ChromaDB directly without our wrapper"""
    print("\n🔍 Testing ChromaDB Direct Connection...")

    try:
        # Test HTTP connection first
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/v1/heartbeat")
            print(f"✅ HTTP heartbeat: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ HTTP connection failed: {e}")
        return False

    try:
        # Test ChromaDB client
        client = chromadb.HttpClient(host="localhost", port=8000)
        heartbeat = client.heartbeat()
        print(f"✅ ChromaDB client heartbeat: {heartbeat}")

        # Test basic operations
        collection_name = f"test_simple_{int(asyncio.get_event_loop().time())}"

        # Create collection
        collection = client.create_collection(collection_name)
        print(f"✅ Created collection: {collection.name}")

        # Add some documents
        documents = [
            "This is a test document about FastAPI web development",
            "ChromaDB provides vector database capabilities for AI applications",
            "Docker containers enable consistent deployment across environments"
        ]

        collection.add(
            documents=documents,
            ids=[f"doc_{i}" for i in range(len(documents))],
            metadatas=[{"source": "test", "index": i} for i in range(len(documents))]
        )
        print(f"✅ Added {len(documents)} documents to collection")

        # Test search
        results = collection.query(
            query_texts=["web development framework"],
            n_results=2
        )

        print(f"✅ Search results: {len(results['documents'][0])} documents found")
        for i, doc in enumerate(results['documents'][0]):
            distance = results['distances'][0][i]
            print(f"   - Document {i+1}: {doc[:50]}... (distance: {distance:.3f})")

        # Cleanup
        client.delete_collection(collection_name)
        print(f"✅ Cleaned up test collection")

        return True

    except Exception as e:
        print(f"❌ ChromaDB operations failed: {e}")
        return False

async def main():
    print("🧪 Simple ChromaDB Test Suite")
    print("=" * 50)

    success = await test_chromadb_direct()

    if success:
        print("\n🎉 All tests passed! ChromaDB is working correctly with Rancher Desktop")
        print("\nNext steps:")
        print("- Vector database infrastructure is ready")
        print("- You can proceed with semantic search operations")
        print("- Run: python scripts/load_test_data.py (when dependencies are fixed)")
    else:
        print("\n❌ Tests failed - check ChromaDB container status")
        print("- Run: docker-compose ps")
        print("- Check logs: docker-compose logs chromadb")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)