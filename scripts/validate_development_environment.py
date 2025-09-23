#!/usr/bin/env python3
"""
Development Environment Validation Script

Validates that the ChromaDB vector database infrastructure is properly
configured and working in the local development environment.
"""

import asyncio
import sys
import time
import os
from typing import Dict, Any, List
import argparse

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.python.database.vector_client import get_vector_client, VectorDatabaseError


class DevelopmentEnvironmentValidator:
    """Validates ChromaDB development environment setup"""

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.validation_results: Dict[str, Any] = {}

    async def validate_environment(self) -> bool:
        """Run complete development environment validation"""
        print("🔍 Validating ChromaDB Development Environment")
        print(f"   Target: {self.host}:{self.port}")
        print("=" * 60)

        validators = [
            ("ChromaDB Connectivity", self._validate_connectivity),
            ("Collection Operations", self._validate_collection_operations),
            ("Embedding Operations", self._validate_embedding_operations),
            ("Search Performance", self._validate_search_performance),
            ("Error Handling", self._validate_error_handling),
            ("Health Check Integration", self._validate_health_checks),
        ]

        all_passed = True

        for validation_name, validator_func in validators:
            print(f"\n📋 {validation_name}")
            print("-" * 40)

            try:
                result = await validator_func()
                self.validation_results[validation_name] = {
                    "status": "PASS" if result else "FAIL",
                    "details": result if isinstance(result, dict) else {"success": result}
                }

                if result:
                    print(f"✅ {validation_name}: PASSED")
                else:
                    print(f"❌ {validation_name}: FAILED")
                    all_passed = False

            except Exception as e:
                print(f"❌ {validation_name}: ERROR - {str(e)}")
                self.validation_results[validation_name] = {
                    "status": "ERROR",
                    "details": {"error": str(e)}
                }
                all_passed = False

        print("\n" + "=" * 60)
        print(f"🎯 Environment Validation: {'PASSED' if all_passed else 'FAILED'}")
        return all_passed

    async def _validate_connectivity(self) -> bool:
        """Validate basic ChromaDB connectivity"""
        try:
            async with get_vector_client(self.host, self.port) as client:
                health_result = await client.health_check()

                if health_result["status"] == "healthy":
                    print(f"   ✓ Connection established successfully")
                    print(f"   ✓ Health check: {health_result['status']}")
                    return True
                else:
                    print(f"   ✗ Health check failed: {health_result}")
                    return False

        except Exception as e:
            print(f"   ✗ Connection failed: {str(e)}")
            return False

    async def _validate_collection_operations(self) -> bool:
        """Validate collection creation and management"""
        test_collection = f"dev_validation_{int(time.time())}"

        try:
            async with get_vector_client(self.host, self.port) as client:
                # Create collection
                collection_id = await client.create_collection(
                    test_collection,
                    metadata={"purpose": "development_validation", "created_by": "validator"}
                )
                print(f"   ✓ Collection created: {collection_id}")

                # Get collection info
                info = await client.get_collection_info(test_collection)
                print(f"   ✓ Collection info retrieved: {info['count']} documents")

                # Delete collection
                deleted = await client.delete_collection(test_collection)
                print(f"   ✓ Collection deleted: {deleted}")

                return True

        except Exception as e:
            print(f"   ✗ Collection operations failed: {str(e)}")
            return False

    async def _validate_embedding_operations(self) -> bool:
        """Validate embedding generation and storage"""
        test_collection = f"dev_validation_embed_{int(time.time())}"
        test_documents = [
            "This is a test document for development validation.",
            "Vector databases store high-dimensional embeddings efficiently.",
            "ChromaDB provides similarity search capabilities for developers."
        ]

        try:
            async with get_vector_client(self.host, self.port) as client:
                # Create collection
                await client.create_collection(test_collection)
                print(f"   ✓ Test collection created")

                # Add embeddings
                doc_ids = await client.add_embeddings(
                    test_collection,
                    test_documents,
                    metadatas=[{"index": i, "type": "test"} for i in range(len(test_documents))]
                )
                print(f"   ✓ {len(doc_ids)} documents embedded and stored")

                # Verify collection count
                info = await client.get_collection_info(test_collection)
                if info["count"] == len(test_documents):
                    print(f"   ✓ Document count verified: {info['count']}")
                else:
                    print(f"   ✗ Document count mismatch: expected {len(test_documents)}, got {info['count']}")
                    return False

                # Cleanup
                await client.delete_collection(test_collection)
                print(f"   ✓ Test collection cleaned up")

                return True

        except Exception as e:
            print(f"   ✗ Embedding operations failed: {str(e)}")
            return False

    async def _validate_search_performance(self) -> bool:
        """Validate search performance meets requirements"""
        test_collection = f"dev_validation_perf_{int(time.time())}"
        test_documents = [
            "FastAPI is a modern web framework for building APIs with Python.",
            "Docker containers provide consistent development environments.",
            "PostgreSQL is a powerful relational database management system.",
            "ChromaDB enables semantic search using vector embeddings.",
            "Railway platform simplifies cloud application deployment.",
            "Python async/await enables high-performance concurrent programming.",
            "Vector similarity search finds relevant documents efficiently.",
            "Microservices architecture improves system scalability and maintainability."
        ]

        try:
            async with get_vector_client(self.host, self.port) as client:
                # Setup test data
                await client.create_collection(test_collection)
                await client.add_embeddings(test_collection, test_documents)
                print(f"   ✓ Performance test collection created with {len(test_documents)} documents")

                # Test search performance
                search_queries = [
                    "web development framework",
                    "database management system",
                    "cloud deployment platform"
                ]

                total_time = 0
                for i, query in enumerate(search_queries):
                    start_time = time.time()

                    results = await client.search_similar(
                        test_collection,
                        query,
                        n_results=3
                    )

                    query_time = time.time() - start_time
                    total_time += query_time

                    print(f"   ✓ Query {i+1}: {query_time:.3f}s ({len(results['documents'])} results)")

                    # Validate <2 second requirement
                    if query_time >= 2.0:
                        print(f"   ✗ Query {i+1} exceeded 2s limit: {query_time:.3f}s")
                        return False

                avg_time = total_time / len(search_queries)
                print(f"   ✓ Average search time: {avg_time:.3f}s (target: <2s)")

                # Cleanup
                await client.delete_collection(test_collection)

                return avg_time < 2.0

        except Exception as e:
            print(f"   ✗ Performance validation failed: {str(e)}")
            return False

    async def _validate_error_handling(self) -> bool:
        """Validate error handling and fallback responses"""
        try:
            async with get_vector_client(self.host, self.port) as client:
                # Test search on non-existent collection
                try:
                    await client.search_similar("non_existent_collection", "test query")
                    print(f"   ✗ Should have raised VectorDatabaseError")
                    return False
                except VectorDatabaseError as e:
                    if "knowledge gap" in str(e).lower():
                        print(f"   ✓ Proper fallback response for missing collection")
                    else:
                        print(f"   ✗ Unexpected error message: {str(e)}")
                        return False

                # Test connection validation
                await client._test_connection()
                print(f"   ✓ Connection validation works")

                return True

        except Exception as e:
            print(f"   ✗ Error handling validation failed: {str(e)}")
            return False

    async def _validate_health_checks(self) -> bool:
        """Validate health check integration"""
        try:
            # Test shared health utilities
            from shared.python.utils.health import chromadb_health_check

            health_result = await chromadb_health_check(self.host, self.port)

            if health_result["status"] == "healthy":
                print(f"   ✓ Shared health check utility works")
                print(f"   ✓ Health status: {health_result['status']}")
                return True
            else:
                print(f"   ✗ Health check returned: {health_result}")
                return False

        except Exception as e:
            print(f"   ✗ Health check validation failed: {str(e)}")
            return False

    def generate_report(self) -> str:
        """Generate validation report"""
        report = ["", "📊 DEVELOPMENT ENVIRONMENT VALIDATION REPORT", "=" * 60]

        passed = sum(1 for r in self.validation_results.values() if r["status"] == "PASS")
        total = len(self.validation_results)

        report.append(f"Overall Status: {passed}/{total} validations passed")
        report.append("")

        for validation_name, result in self.validation_results.items():
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            report.append(f"{status_icon} {validation_name}: {result['status']}")

            if result["status"] != "PASS" and "error" in result["details"]:
                report.append(f"   Error: {result['details']['error']}")

        report.append("")
        report.append("🔧 Next Steps:")

        if passed == total:
            report.append("✅ Development environment is ready for use!")
            report.append("   - Run: docker-compose up chromadb")
            report.append("   - Test: python scripts/test_chromadb.py")
            report.append("   - Develop: Use shared.python.database.vector_client")
        else:
            report.append("❌ Development environment needs attention:")
            report.append("   - Ensure Docker and docker-compose are installed")
            report.append("   - Run: docker-compose up chromadb")
            report.append("   - Check ChromaDB container logs for errors")
            report.append("   - Verify port 8000 is not blocked")

        return "\n".join(report)


async def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="Validate ChromaDB development environment")
    parser.add_argument("--host", default="localhost", help="ChromaDB host")
    parser.add_argument("--port", type=int, default=8000, help="ChromaDB port")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")

    args = parser.parse_args()

    validator = DevelopmentEnvironmentValidator(args.host, args.port)

    try:
        success = await validator.validate_environment()

        if args.report:
            print(validator.generate_report())

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⏸️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())