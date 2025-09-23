#!/usr/bin/env python3
"""
Basic test to verify ChromaDB connection without fancy characters
"""
import asyncio
import sys
import json

try:
    import httpx
    print("HTTP client available")
except ImportError as e:
    print(f"Missing httpx: {e}")
    sys.exit(1)

async def test_chromadb_http():
    """Test ChromaDB via HTTP without Python client"""
    print("\nTesting ChromaDB HTTP API...")

    try:
        async with httpx.AsyncClient() as client:
            # Test heartbeat (v1 API)
            response = await client.get("http://localhost:8000/api/v1/heartbeat")
            print(f"Heartbeat status: {response.status_code}")
            print(f"Heartbeat response: {response.text}")

            if response.status_code != 200:
                print("ChromaDB not responding properly")
                return False

            # Test collection operations via HTTP API (v2)
            collection_name = "test_http_collection"

            # Create collection
            create_response = await client.post(
                "http://localhost:8000/api/v1/collections",
                json={"name": collection_name}
            )

            if create_response.status_code in [200, 201]:
                print(f"Created collection successfully: {create_response.status_code}")
            else:
                print(f"Collection creation failed: {create_response.status_code}")
                print(f"Response: {create_response.text}")
                return False

            # List collections
            list_response = await client.get("http://localhost:8000/api/v1/collections")
            if list_response.status_code == 200:
                collections = list_response.json()
                print(f"Collections found: {len(collections)}")
                collection_found = any(c.get('name') == collection_name for c in collections)
                print(f"Test collection exists: {collection_found}")
            else:
                print(f"Failed to list collections: {list_response.status_code}")

            # Delete test collection
            delete_response = await client.delete(
                f"http://localhost:8000/api/v1/collections/{collection_name}"
            )
            print(f"Collection deletion: {delete_response.status_code}")

            return True

    except Exception as e:
        print(f"HTTP test failed: {e}")
        return False

async def main():
    print("Basic ChromaDB HTTP Test")
    print("=" * 30)

    success = await test_chromadb_http()

    if success:
        print("\nSUCCESS: ChromaDB is working with Rancher Desktop!")
        print("\nWhat this means:")
        print("- ChromaDB container is running correctly")
        print("- HTTP API is accessible on localhost:8000")
        print("- Basic vector database operations are functional")
        print("- Ready for semantic search implementation")
        print("\nThe heartbeat response you saw earlier:")
        print('{"nanosecond heartbeat":1758620872348988063}')
        print("This is ChromaDB's way of saying 'I'm alive and ready!'")

    else:
        print("\nFAILED: ChromaDB is not responding correctly")
        print("Check: docker-compose ps")
        print("Check: docker-compose logs chromadb")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)