#!/usr/bin/env python3
"""
Test Data Loading Script

Loads sample test data into ChromaDB for development and testing purposes.
Creates realistic troubleshooting content for vector database validation.
"""

import asyncio
import json
import time
import sys
import os
from typing import List, Dict, Any
import argparse

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.python.database.vector_client import get_vector_client, VectorDatabaseError


class TestDataLoader:
    """Loads test data into ChromaDB collections"""

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port

    async def load_all_test_data(self) -> bool:
        """Load all test datasets"""
        print("📚 Loading Test Data into ChromaDB")
        print(f"   Target: {self.host}:{self.port}")
        print("=" * 50)

        try:
            async with get_vector_client(self.host, self.port) as client:
                await self._load_troubleshooting_docs(client)
                await self._load_faq_content(client)
                await self._load_technical_examples(client)

                print("\n🎉 All test data loaded successfully!")
                return True

        except Exception as e:
            print(f"\n❌ Test data loading failed: {str(e)}")
            return False

    async def _load_troubleshooting_docs(self, client) -> None:
        """Load troubleshooting documentation test data"""
        collection_name = "troubleshooting_docs_test"
        print(f"\n📖 Loading troubleshooting documentation...")

        # Create collection
        await client.create_collection(
            collection_name,
            metadata={
                "description": "Test troubleshooting documentation",
                "content_type": "troubleshooting_guides",
                "created_for": "development_testing"
            }
        )

        # Sample troubleshooting documents
        documents = [
            {
                "content": "When experiencing network connectivity issues, first check if the Ethernet cable is properly connected. Verify that the network adapter is enabled in Device Manager. Try pinging the gateway to test local network connectivity.",
                "metadata": {
                    "title": "Network Connectivity Troubleshooting",
                    "category": "network",
                    "difficulty": "beginner",
                    "resolution_time": "5-10 minutes"
                }
            },
            {
                "content": "Application crashes can be caused by memory leaks, incompatible drivers, or corrupted system files. Check Windows Event Viewer for error details. Run system file checker (sfc /scannow) to repair corrupted files. Update device drivers to latest versions.",
                "metadata": {
                    "title": "Application Crash Analysis",
                    "category": "software",
                    "difficulty": "intermediate",
                    "resolution_time": "15-30 minutes"
                }
            },
            {
                "content": "Blue Screen of Death (BSOD) errors indicate serious system problems. Note the error code (e.g., 0x0000007B). Boot into Safe Mode to troubleshoot. Check for recent hardware changes or driver updates that might have caused the issue.",
                "metadata": {
                    "title": "Blue Screen Error Resolution",
                    "category": "system",
                    "difficulty": "advanced",
                    "resolution_time": "30-60 minutes"
                }
            },
            {
                "content": "Printer not responding issues often relate to driver problems or connection issues. Restart the Print Spooler service in Windows Services. Reinstall printer drivers from manufacturer's website. Check USB or network connection.",
                "metadata": {
                    "title": "Printer Connectivity Issues",
                    "category": "hardware",
                    "difficulty": "beginner",
                    "resolution_time": "10-15 minutes"
                }
            },
            {
                "content": "Slow computer performance can be improved by disabling startup programs, running disk cleanup, checking for malware, and ensuring adequate free disk space. Use Task Manager to identify resource-heavy processes.",
                "metadata": {
                    "title": "Performance Optimization Guide",
                    "category": "performance",
                    "difficulty": "beginner",
                    "resolution_time": "20-30 minutes"
                }
            },
            {
                "content": "Email configuration problems in Outlook require verifying server settings. Check incoming (IMAP/POP3) and outgoing (SMTP) server addresses. Ensure correct port numbers and security settings (SSL/TLS) are configured.",
                "metadata": {
                    "title": "Email Setup Troubleshooting",
                    "category": "software",
                    "difficulty": "intermediate",
                    "resolution_time": "10-20 minutes"
                }
            },
            {
                "content": "Wi-Fi connection drops can be caused by power management settings, outdated drivers, or interference. Disable power saving mode for wireless adapter. Update Wi-Fi drivers and check for interference from other devices.",
                "metadata": {
                    "title": "Wireless Connection Stability",
                    "category": "network",
                    "difficulty": "intermediate",
                    "resolution_time": "15-25 minutes"
                }
            },
            {
                "content": "Hard drive errors require immediate attention. Run CHKDSK to scan for and repair file system errors. Use disk health monitoring tools to check SMART attributes. Backup important data immediately if errors are detected.",
                "metadata": {
                    "title": "Hard Drive Error Recovery",
                    "category": "hardware",
                    "difficulty": "advanced",
                    "resolution_time": "45-90 minutes"
                }
            }
        ]

        # Add documents to collection
        contents = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]

        doc_ids = await client.add_embeddings(
            collection_name,
            contents,
            metadatas=metadatas
        )

        print(f"   ✓ Added {len(doc_ids)} troubleshooting documents")

        # Test search functionality
        test_query = "computer running slowly"
        results = await client.search_similar(collection_name, test_query, n_results=3)
        print(f"   ✓ Test search for '{test_query}' returned {len(results['documents'])} results")

    async def _load_faq_content(self, client) -> None:
        """Load FAQ content test data"""
        collection_name = "faq_content_test"
        print(f"\n❓ Loading FAQ content...")

        # Create collection
        await client.create_collection(
            collection_name,
            metadata={
                "description": "Test FAQ content for troubleshooting",
                "content_type": "frequently_asked_questions",
                "created_for": "development_testing"
            }
        )

        # Sample FAQ documents
        faq_data = [
            {
                "question": "How do I reset my password?",
                "answer": "To reset your password, go to the login page and click 'Forgot Password'. Enter your email address and follow the instructions sent to your email. You'll receive a link to create a new password.",
                "category": "account_management"
            },
            {
                "question": "Why is my computer running slow?",
                "answer": "Computer slowness can be caused by too many startup programs, insufficient RAM, malware, or a full hard drive. Try restarting your computer, running antivirus scans, and clearing temporary files.",
                "category": "performance"
            },
            {
                "question": "How do I connect to Wi-Fi?",
                "answer": "Click the Wi-Fi icon in the system tray, select your network name from the list, enter the password when prompted, and click Connect. Make sure your wireless adapter is enabled.",
                "category": "networking"
            },
            {
                "question": "What should I do if my screen is black?",
                "answer": "Check if the monitor is powered on and cables are connected properly. Try pressing Ctrl+Shift+Esc to open Task Manager. If unresponsive, hold the power button to force restart.",
                "category": "display"
            },
            {
                "question": "How do I update my drivers?",
                "answer": "Open Device Manager, right-click the device you want to update, select 'Update driver', then choose 'Search automatically for drivers'. Windows will search and install available updates.",
                "category": "drivers"
            },
            {
                "question": "Why can't I print documents?",
                "answer": "Check if the printer is powered on and connected. Verify paper and ink levels. Restart the Print Spooler service or reinstall printer drivers if the problem persists.",
                "category": "printing"
            }
        ]

        # Combine questions and answers for better semantic search
        documents = []
        metadatas = []

        for faq in faq_data:
            content = f"Q: {faq['question']} A: {faq['answer']}"
            metadata = {
                "question": faq["question"],
                "answer": faq["answer"],
                "category": faq["category"],
                "content_type": "faq"
            }
            documents.append(content)
            metadatas.append(metadata)

        doc_ids = await client.add_embeddings(
            collection_name,
            documents,
            metadatas=metadatas
        )

        print(f"   ✓ Added {len(doc_ids)} FAQ entries")

        # Test search functionality
        test_query = "how to fix printing problems"
        results = await client.search_similar(collection_name, test_query, n_results=2)
        print(f"   ✓ Test search for '{test_query}' returned {len(results['documents'])} results")

    async def _load_technical_examples(self, client) -> None:
        """Load technical examples and code snippets"""
        collection_name = "technical_examples_test"
        print(f"\n💻 Loading technical examples...")

        # Create collection
        await client.create_collection(
            collection_name,
            metadata={
                "description": "Test technical examples and code snippets",
                "content_type": "technical_documentation",
                "created_for": "development_testing"
            }
        )

        # Sample technical content
        technical_docs = [
            {
                "content": "FastAPI endpoint configuration: Create REST API endpoints using @app.get(), @app.post() decorators. Use Pydantic models for request/response validation. Include proper error handling with HTTPException for user-friendly error messages.",
                "metadata": {
                    "title": "FastAPI Endpoint Setup",
                    "technology": "FastAPI",
                    "language": "Python",
                    "complexity": "intermediate"
                }
            },
            {
                "content": "Docker containerization best practices: Use multi-stage builds to reduce image size. Set non-root user for security. Include health checks for container monitoring. Use .dockerignore to exclude unnecessary files.",
                "metadata": {
                    "title": "Docker Best Practices",
                    "technology": "Docker",
                    "language": "Dockerfile",
                    "complexity": "intermediate"
                }
            },
            {
                "content": "PostgreSQL database optimization: Create indexes on frequently queried columns. Use EXPLAIN ANALYZE to identify slow queries. Implement connection pooling to manage database connections efficiently. Regular VACUUM operations maintain performance.",
                "metadata": {
                    "title": "PostgreSQL Performance Tuning",
                    "technology": "PostgreSQL",
                    "language": "SQL",
                    "complexity": "advanced"
                }
            },
            {
                "content": "React component development: Use functional components with hooks for state management. Implement useEffect for side effects and cleanup. Use React.memo for performance optimization. Follow component composition patterns for reusability.",
                "metadata": {
                    "title": "React Development Patterns",
                    "technology": "React",
                    "language": "JavaScript",
                    "complexity": "intermediate"
                }
            },
            {
                "content": "ChromaDB vector database integration: Use async context managers for connection management. Implement proper error handling with fallback responses. Include correlation IDs for request tracing. Follow <2 second search performance requirements.",
                "metadata": {
                    "title": "Vector Database Integration",
                    "technology": "ChromaDB",
                    "language": "Python",
                    "complexity": "advanced"
                }
            }
        ]

        contents = [doc["content"] for doc in technical_docs]
        metadatas = [doc["metadata"] for doc in technical_docs]

        doc_ids = await client.add_embeddings(
            collection_name,
            contents,
            metadatas=metadatas
        )

        print(f"   ✓ Added {len(doc_ids)} technical examples")

        # Test search functionality
        test_query = "database performance optimization"
        results = await client.search_similar(collection_name, test_query, n_results=2)
        print(f"   ✓ Test search for '{test_query}' returned {len(results['documents'])} results")

    async def cleanup_test_data(self) -> bool:
        """Remove all test collections"""
        print("\n🧹 Cleaning up test data...")

        test_collections = [
            "troubleshooting_docs_test",
            "faq_content_test",
            "technical_examples_test"
        ]

        try:
            async with get_vector_client(self.host, self.port) as client:
                for collection in test_collections:
                    try:
                        success = await client.delete_collection(collection)
                        if success:
                            print(f"   ✓ Deleted collection: {collection}")
                        else:
                            print(f"   ⚠️ Collection not found: {collection}")
                    except Exception as e:
                        print(f"   ⚠️ Error deleting {collection}: {str(e)}")

                print("\n✅ Test data cleanup completed")
                return True

        except Exception as e:
            print(f"\n❌ Cleanup failed: {str(e)}")
            return False

    async def list_collections(self) -> None:
        """List all collections with their sizes"""
        print("\n📋 Current Collections:")
        print("-" * 30)

        try:
            async with get_vector_client(self.host, self.port) as client:
                # Note: In a real implementation, ChromaDB would have a list_collections method
                # For now, we'll try to get info on known test collections
                test_collections = [
                    "troubleshooting_docs_test",
                    "faq_content_test",
                    "technical_examples_test",
                    "manual_content_embeddings"  # Production collection
                ]

                for collection_name in test_collections:
                    try:
                        info = await client.get_collection_info(collection_name)
                        print(f"   {collection_name}: {info['count']} documents")
                    except VectorDatabaseError:
                        # Collection doesn't exist - skip
                        pass

        except Exception as e:
            print(f"   Error listing collections: {str(e)}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Load test data into ChromaDB")
    parser.add_argument("--host", default="localhost", help="ChromaDB host")
    parser.add_argument("--port", type=int, default=8000, help="ChromaDB port")
    parser.add_argument("--cleanup", action="store_true", help="Remove test data")
    parser.add_argument("--list", action="store_true", help="List existing collections")

    args = parser.parse_args()

    loader = TestDataLoader(args.host, args.port)

    try:
        if args.cleanup:
            success = await loader.cleanup_test_data()
        elif args.list:
            await loader.list_collections()
            success = True
        else:
            success = await loader.load_all_test_data()

        if success and not args.list:
            await loader.list_collections()

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⏸️ Operation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Operation failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)