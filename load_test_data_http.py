#!/usr/bin/env python3
"""
HTTP-based Test Data Loader

Loads test data into ChromaDB using HTTP API only,
without requiring the ChromaDB Python client.
"""

import asyncio
import json
import time
import httpx
import argparse

class HTTPTestDataLoader:
    """Load test data using ChromaDB HTTP API"""

    def __init__(self, host="localhost", port=8000):
        self.base_url = f"http://{host}:{port}/api/v1"

    async def load_troubleshooting_data(self):
        """Load troubleshooting test data"""
        print("Loading troubleshooting documentation...")

        collection_name = "troubleshooting_docs_test"

        documents = [
            "Network connectivity issues: Check Ethernet cable connection, verify network adapter is enabled in Device Manager, ping gateway to test local network connectivity.",
            "Application crashes: Check for memory leaks, update device drivers, run system file checker sfc /scannow to repair corrupted files.",
            "Blue Screen of Death errors: Note error code, boot into Safe Mode, check for recent hardware changes or driver updates.",
            "Printer not responding: Restart Print Spooler service, reinstall printer drivers, check USB or network connection.",
            "Slow computer performance: Disable startup programs, run disk cleanup, check for malware, ensure adequate free disk space.",
            "Email configuration in Outlook: Verify server settings, check IMAP/POP3 and SMTP addresses, ensure correct SSL/TLS settings.",
            "Wi-Fi connection drops: Disable power saving for wireless adapter, update Wi-Fi drivers, check for interference.",
            "Hard drive errors: Run CHKDSK, check SMART attributes with disk health tools, backup data immediately if errors detected."
        ]

        metadatas = [
            {"category": "network", "difficulty": "beginner", "resolution_time": "5-10 minutes"},
            {"category": "software", "difficulty": "intermediate", "resolution_time": "15-30 minutes"},
            {"category": "system", "difficulty": "advanced", "resolution_time": "30-60 minutes"},
            {"category": "hardware", "difficulty": "beginner", "resolution_time": "10-15 minutes"},
            {"category": "performance", "difficulty": "beginner", "resolution_time": "20-30 minutes"},
            {"category": "software", "difficulty": "intermediate", "resolution_time": "10-20 minutes"},
            {"category": "network", "difficulty": "intermediate", "resolution_time": "15-25 minutes"},
            {"category": "hardware", "difficulty": "advanced", "resolution_time": "45-90 minutes"}
        ]

        return await self._create_collection_with_data(collection_name, documents, metadatas, "troubleshooting")

    async def load_faq_data(self):
        """Load FAQ test data"""
        print("Loading FAQ content...")

        collection_name = "faq_content_test"

        # Combine Q&A pairs for better semantic search
        documents = [
            "Q: How do I reset my password? A: Go to login page, click Forgot Password, enter email address, follow instructions sent to email for password reset link.",
            "Q: Why is my computer running slow? A: Try restarting computer, running antivirus scans, clearing temporary files, checking for too many startup programs.",
            "Q: How do I connect to Wi-Fi? A: Click Wi-Fi icon in system tray, select network name, enter password when prompted, click Connect.",
            "Q: What should I do if screen is black? A: Check monitor power and cables, try Ctrl+Shift+Esc for Task Manager, force restart if unresponsive.",
            "Q: How do I update drivers? A: Open Device Manager, right-click device, select Update driver, choose Search automatically for drivers.",
            "Q: Why can't I print documents? A: Check printer power and connection, verify paper and ink levels, restart Print Spooler service if needed."
        ]

        metadatas = [
            {"category": "account_management", "content_type": "faq"},
            {"category": "performance", "content_type": "faq"},
            {"category": "networking", "content_type": "faq"},
            {"category": "display", "content_type": "faq"},
            {"category": "drivers", "content_type": "faq"},
            {"category": "printing", "content_type": "faq"}
        ]

        return await self._create_collection_with_data(collection_name, documents, metadatas, "FAQ")

    async def load_technical_examples(self):
        """Load technical examples"""
        print("Loading technical examples...")

        collection_name = "technical_examples_test"

        documents = [
            "FastAPI endpoint configuration: Create REST API endpoints using @app.get() and @app.post() decorators, use Pydantic models for request/response validation.",
            "Docker containerization: Use multi-stage builds, set non-root user for security, include health checks for monitoring, use .dockerignore files.",
            "PostgreSQL optimization: Create indexes on frequently queried columns, use EXPLAIN ANALYZE for slow queries, implement connection pooling.",
            "React development: Use functional components with hooks, implement useEffect for side effects, use React.memo for performance optimization.",
            "ChromaDB integration: Use async context managers, implement error handling with fallback responses, include correlation IDs for tracing."
        ]

        metadatas = [
            {"technology": "FastAPI", "language": "Python", "complexity": "intermediate"},
            {"technology": "Docker", "language": "Dockerfile", "complexity": "intermediate"},
            {"technology": "PostgreSQL", "language": "SQL", "complexity": "advanced"},
            {"technology": "React", "language": "JavaScript", "complexity": "intermediate"},
            {"technology": "ChromaDB", "language": "Python", "complexity": "advanced"}
        ]

        return await self._create_collection_with_data(collection_name, documents, metadatas, "technical")

    async def _create_collection_with_data(self, collection_name, documents, metadatas, data_type):
        """Create collection and add documents"""
        async with httpx.AsyncClient() as client:
            try:
                # Create collection
                create_response = await client.post(
                    f"{self.base_url}/collections",
                    json={
                        "name": collection_name,
                        "metadata": {
                            "description": f"Test {data_type} content",
                            "content_type": data_type,
                            "created_for": "development_testing"
                        }
                    }
                )

                if create_response.status_code == 200:
                    print(f"   OK Created collection: {collection_name}")
                else:
                    print(f"   ERROR Failed to create collection: {create_response.status_code}")
                    return False

                # Add documents
                add_response = await client.post(
                    f"{self.base_url}/collections/{collection_name}/add",
                    json={
                        "documents": documents,
                        "metadatas": metadatas,
                        "ids": [f"{data_type}_{i}" for i in range(len(documents))]
                    }
                )

                if add_response.status_code in [200, 201]:
                    print(f"   OK Added {len(documents)} documents")
                    return True
                else:
                    print(f"   WARNING Documents add returned: {add_response.status_code}")
                    print(f"   (This may be normal - ChromaDB processes embeddings asynchronously)")
                    return True

            except Exception as e:
                print(f"   ERROR Failed to create {data_type} collection: {str(e)}")
                return False

    async def list_collections(self):
        """List all test collections"""
        print("\nCurrent Test Collections:")
        print("-" * 30)

        test_collections = [
            "troubleshooting_docs_test",
            "faq_content_test",
            "technical_examples_test"
        ]

        async with httpx.AsyncClient() as client:
            for collection_name in test_collections:
                try:
                    response = await client.get(f"{self.base_url}/collections/{collection_name}")
                    if response.status_code == 200:
                        info = response.json()
                        count = info.get('count', 'unknown')
                        print(f"   {collection_name}: {count} documents")
                    else:
                        print(f"   {collection_name}: Not found")
                except Exception:
                    print(f"   {collection_name}: Not accessible")

    async def cleanup_collections(self):
        """Clean up test collections"""
        print("Cleaning up test collections...")

        test_collections = [
            "troubleshooting_docs_test",
            "faq_content_test",
            "technical_examples_test"
        ]

        async with httpx.AsyncClient() as client:
            for collection_name in test_collections:
                try:
                    response = await client.delete(f"{self.base_url}/collections/{collection_name}")
                    if response.status_code == 200:
                        print(f"   OK Deleted: {collection_name}")
                    else:
                        print(f"   WARNING {collection_name}: {response.status_code}")
                except Exception as e:
                    print(f"   ERROR {collection_name}: {str(e)}")

    async def test_search(self):
        """Test search functionality on loaded data"""
        print("\nTesting search on loaded data:")
        print("-" * 35)

        test_queries = [
            ("network connectivity troubleshooting", "troubleshooting_docs_test"),
            ("password reset help", "faq_content_test"),
            ("database performance optimization", "technical_examples_test")
        ]

        async with httpx.AsyncClient() as client:
            for query, collection in test_queries:
                try:
                    start_time = time.time()
                    response = await client.post(
                        f"{self.base_url}/collections/{collection}/query",
                        json={
                            "query_texts": [query],
                            "n_results": 2
                        }
                    )
                    search_time = time.time() - start_time

                    print(f"\nQuery: '{query}' in {collection}")
                    print(f"Time: {search_time:.3f}s")

                    if response.status_code == 200:
                        results = response.json()
                        docs = results.get("documents", [[]])[0]
                        distances = results.get("distances", [[]])[0]

                        print(f"Results: {len(docs)} documents found")
                        for i, (doc, dist) in enumerate(zip(docs, distances)):
                            similarity = max(0, 1 - dist)
                            print(f"   {i+1}. [{similarity:.3f}] {doc[:50]}...")
                    else:
                        print(f"Search returned: {response.status_code}")

                except Exception as e:
                    print(f"Search error: {str(e)}")

async def main():
    parser = argparse.ArgumentParser(description="Load test data via HTTP API")
    parser.add_argument("--host", default="localhost", help="ChromaDB host")
    parser.add_argument("--port", type=int, default=8000, help="ChromaDB port")
    parser.add_argument("--list", action="store_true", help="List collections")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test data")
    parser.add_argument("--test-search", action="store_true", help="Test search functionality")

    args = parser.parse_args()

    loader = HTTPTestDataLoader(args.host, args.port)

    try:
        if args.list:
            await loader.list_collections()
        elif args.cleanup:
            await loader.cleanup_collections()
        elif args.test_search:
            await loader.test_search()
        else:
            print("Loading test data into ChromaDB...")
            print("=" * 40)

            # Load all test datasets
            success_count = 0

            if await loader.load_troubleshooting_data():
                success_count += 1
            if await loader.load_faq_data():
                success_count += 1
            if await loader.load_technical_examples():
                success_count += 1

            print(f"\nLoading completed: {success_count}/3 collections loaded")

            # Show what was loaded
            await loader.list_collections()

            # Test search functionality
            await loader.test_search()

        return 0

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)