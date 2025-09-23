#!/usr/bin/env python3
"""
ChromaDB basic vector operations test script.

Tests CRUD operations and performance benchmarking to validate
acceptance criteria for vector database infrastructure.
"""

import asyncio
import json
import time
import uuid
import sys
import os
from typing import List, Dict, Any
import argparse

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.python.database.vector_client import get_vector_client, VectorDatabaseError


class ChromaDBTester:
    """Test suite for ChromaDB vector operations"""

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.test_collection = f"test_collection_{int(time.time())}"
        self.test_data = [
            "The quick brown fox jumps over the lazy dog.",
            "Python is a versatile programming language.",
            "Vector databases store high-dimensional embeddings.",
            "ChromaDB provides similarity search capabilities.",
            "Machine learning models generate text embeddings.",
            "Semantic search finds relevant documents.",
            "FastAPI creates high-performance web APIs.",
            "Railway platform simplifies cloud deployment.",
            "PostgreSQL stores structured relational data.",
            "Microsoft Teams enables workplace collaboration."
        ]

    async def run_all_tests(self) -> bool:
        """Run complete test suite"""
        print(f"🧪 Starting ChromaDB test suite")
        print(f"   Host: {self.host}:{self.port}")
        print(f"   Test Collection: {self.test_collection}")

        try:
            async with get_vector_client(self.host, self.port) as client:
                # Run test suite
                await self._test_crud_operations(client)
                await self._test_performance_benchmarking(client)
                await self._test_error_handling(client)

                # Cleanup
                await self._cleanup(client)

                print("🎉 All tests passed successfully!")
                return True

        except Exception as e:
            print(f"❌ Test suite failed: {str(e)}")
            return False

    async def _test_crud_operations(self, client) -> None:
        """Test Create, Read, Update, Delete operations"""
        print("\n📝 Testing CRUD Operations...")

        # CREATE: Create collection
        collection_id = await client.create_collection(
            self.test_collection,
            metadata={"description": "Test collection for vector operations"}
        )
        print(f"✅ Created collection: {collection_id}")

        # CREATE: Add embeddings
        document_ids = await client.add_embeddings(
            self.test_collection,
            self.test_data[:5],  # First 5 documents
            metadatas=[{"index": i, "category": "test"} for i in range(5)]
        )
        print(f"✅ Added {len(document_ids)} documents")

        # READ: Get collection info
        collection_info = await client.get_collection_info(self.test_collection)
        assert collection_info["count"] == 5, f"Expected 5 documents, got {collection_info['count']}"
        print(f"✅ Collection info: {collection_info['count']} documents")

        # READ: Search similar documents
        search_results = await client.search_similar(
            self.test_collection,
            "programming language Python development",
            n_results=3
        )
        assert len(search_results["documents"]) > 0, "No search results found"
        print(f"✅ Search returned {len(search_results['documents'])} results")

        # UPDATE: Add more documents (extend collection)
        additional_ids = await client.add_embeddings(
            self.test_collection,
            self.test_data[5:],  # Remaining documents
            metadatas=[{"index": i, "category": "test"} for i in range(5, len(self.test_data))]
        )
        print(f"✅ Added {len(additional_ids)} additional documents")

        # Verify final count
        final_info = await client.get_collection_info(self.test_collection)
        assert final_info["count"] == len(self.test_data), f"Expected {len(self.test_data)} documents, got {final_info['count']}"
        print(f"✅ Final collection size: {final_info['count']} documents")

    async def _test_performance_benchmarking(self, client) -> None:
        """Test performance requirements (<2 second target)"""
        print("\n⚡ Testing Performance Benchmarking...")

        search_queries = [
            "programming languages and software development",
            "database storage and data management",
            "web API development with FastAPI",
            "cloud deployment and infrastructure",
            "machine learning and artificial intelligence"
        ]

        total_time = 0
        successful_queries = 0

        for i, query in enumerate(search_queries):
            start_time = time.time()

            try:
                results = await client.search_similar(
                    self.test_collection,
                    query,
                    n_results=5
                )

                query_time = time.time() - start_time
                total_time += query_time
                successful_queries += 1

                print(f"   Query {i+1}: {query_time:.3f}s ({len(results['documents'])} results)")

                # Validate <2 second requirement
                assert query_time < 2.0, f"Query {i+1} took {query_time:.3f}s (>2s limit)"

            except Exception as e:
                print(f"   Query {i+1} failed: {str(e)}")
                raise

        avg_time = total_time / successful_queries
        print(f"✅ Performance test passed:")
        print(f"   Average query time: {avg_time:.3f}s")
        print(f"   All queries under 2s limit: {successful_queries}/{len(search_queries)}")

        # Additional performance assertions
        assert avg_time < 1.0, f"Average query time {avg_time:.3f}s should be <1s for good performance"
        assert successful_queries == len(search_queries), "All queries should succeed"

    async def _test_error_handling(self, client) -> None:
        """Test error handling and fallback responses"""
        print("\n🛡️ Testing Error Handling...")

        # Test search on non-existent collection
        try:
            await client.search_similar(
                "non_existent_collection",
                "test query",
                n_results=5
            )
            assert False, "Should have raised VectorDatabaseError"
        except VectorDatabaseError as e:
            assert "knowledge gap" in str(e).lower(), "Should return knowledge gap response"
            print("✅ Non-existent collection handled correctly")

        # Test health check
        health_result = await client.health_check()
        assert health_result["status"] == "healthy", f"Health check failed: {health_result}"
        print("✅ Health check passed")

        # Test connection validation
        try:
            await client._test_connection()
            print("✅ Connection validation passed")
        except VectorDatabaseError:
            print("❌ Connection validation failed")
            raise

    async def _cleanup(self, client) -> None:
        """Clean up test collection"""
        print("\n🧹 Cleaning up test data...")

        try:
            success = await client.delete_collection(self.test_collection)
            if success:
                print("✅ Test collection deleted successfully")
            else:
                print("⚠️ Test collection deletion returned False")
        except Exception as e:
            print(f"⚠️ Cleanup error (non-critical): {str(e)}")

    async def benchmark_large_dataset(self, num_documents: int = 1000) -> Dict[str, Any]:
        """Benchmark performance with larger dataset"""
        print(f"\n📊 Benchmarking with {num_documents} documents...")

        benchmark_collection = f"benchmark_{int(time.time())}"
        results = {
            "collection_creation_time": 0,
            "embedding_generation_time": 0,
            "document_insertion_time": 0,
            "search_performance": [],
            "total_documents": num_documents
        }

        try:
            async with get_vector_client(self.host, self.port) as client:
                # Create collection
                start_time = time.time()
                await client.create_collection(benchmark_collection)
                results["collection_creation_time"] = time.time() - start_time

                # Generate large dataset
                documents = [f"Document {i}: {self.test_data[i % len(self.test_data)]}" for i in range(num_documents)]

                # Batch insert documents
                batch_size = 50
                total_insert_time = 0

                for i in range(0, num_documents, batch_size):
                    batch = documents[i:i+batch_size]
                    start_time = time.time()

                    await client.add_embeddings(
                        benchmark_collection,
                        batch,
                        metadatas=[{"batch": i//batch_size, "index": j} for j in range(len(batch))]
                    )

                    total_insert_time += time.time() - start_time

                    if (i + batch_size) % 200 == 0:
                        print(f"   Inserted {i + batch_size} documents...")

                results["document_insertion_time"] = total_insert_time

                # Test search performance
                search_queries = [
                    "document search query",
                    "performance testing benchmark",
                    "large dataset validation"
                ]

                for query in search_queries:
                    start_time = time.time()
                    search_results = await client.search_similar(
                        benchmark_collection,
                        query,
                        n_results=20
                    )
                    query_time = time.time() - start_time

                    results["search_performance"].append({
                        "query": query,
                        "time": query_time,
                        "results_count": len(search_results["documents"])
                    })

                # Cleanup
                await client.delete_collection(benchmark_collection)

                return results

        except Exception as e:
            print(f"❌ Benchmark failed: {str(e)}")
            raise


async def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test ChromaDB vector operations")
    parser.add_argument("--host", default="localhost", help="ChromaDB host")
    parser.add_argument("--port", type=int, default=8000, help="ChromaDB port")
    parser.add_argument("--benchmark", action="store_true", help="Run large dataset benchmark")
    parser.add_argument("--benchmark-size", type=int, default=1000, help="Benchmark dataset size")

    args = parser.parse_args()

    tester = ChromaDBTester(args.host, args.port)

    try:
        # Run basic test suite
        success = await tester.run_all_tests()

        if not success:
            sys.exit(1)

        # Run benchmark if requested
        if args.benchmark:
            benchmark_results = await tester.benchmark_large_dataset(args.benchmark_size)

            print("\n📊 Benchmark Results:")
            print(f"   Collection Creation: {benchmark_results['collection_creation_time']:.3f}s")
            print(f"   Document Insertion: {benchmark_results['document_insertion_time']:.3f}s")
            print(f"   Insertion Rate: {benchmark_results['total_documents']/benchmark_results['document_insertion_time']:.1f} docs/sec")

            for perf in benchmark_results["search_performance"]:
                print(f"   Search '{perf['query'][:30]}...': {perf['time']:.3f}s ({perf['results_count']} results)")

            # Validate performance requirements
            avg_search_time = sum(p["time"] for p in benchmark_results["search_performance"]) / len(benchmark_results["search_performance"])
            print(f"   Average Search Time: {avg_search_time:.3f}s")

            if avg_search_time > 2.0:
                print("❌ Benchmark failed: Average search time exceeds 2s requirement")
                sys.exit(1)

        print("\n🎉 All tests completed successfully!")

    except KeyboardInterrupt:
        print("\n⏸️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())