"""
Vector Database Performance Tests for Story 1.5

Focused performance testing to validate <2 second search requirement
and overall system performance under load.
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any
import httpx
import concurrent.futures
from dataclasses import dataclass
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class PerformanceResult:
    """Performance test result data structure"""
    operation: str
    duration: float
    success: bool
    error: str = None
    metadata: Dict[str, Any] = None


class VectorPerformanceTester:
    """Performance testing utilities for vector database"""

    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.results: List[PerformanceResult] = []

    async def benchmark_search_latency(
        self,
        collection_name: str,
        queries: List[str],
        n_results: int = 10,
        concurrent_requests: int = 1
    ) -> Dict[str, Any]:
        """Benchmark search latency with various load patterns"""

        async def single_search(query: str, request_id: int) -> PerformanceResult:
            """Perform single search operation"""
            start_time = time.time()

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.base_url}/collections/{collection_name}/query",
                        json={
                            "query_texts": [query],
                            "n_results": n_results
                        }
                    )

                    duration = time.time() - start_time

                    if response.status_code == 200:
                        results = response.json()
                        results_count = len(results.get("documents", [[]])[0])

                        return PerformanceResult(
                            operation=f"search_{request_id}",
                            duration=duration,
                            success=True,
                            metadata={
                                "query": query,
                                "results_count": results_count,
                                "request_id": request_id
                            }
                        )
                    else:
                        return PerformanceResult(
                            operation=f"search_{request_id}",
                            duration=duration,
                            success=False,
                            error=f"HTTP {response.status_code}",
                            metadata={"query": query, "request_id": request_id}
                        )

            except Exception as e:
                duration = time.time() - start_time
                return PerformanceResult(
                    operation=f"search_{request_id}",
                    duration=duration,
                    success=False,
                    error=str(e),
                    metadata={"query": query, "request_id": request_id}
                )

        # Create tasks for concurrent execution
        tasks = []
        request_id = 0

        for _ in range(concurrent_requests):
            for query in queries:
                tasks.append(single_search(query, request_id))
                request_id += 1

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        valid_results = [r for r in results if isinstance(r, PerformanceResult) and r.success]
        failed_results = [r for r in results if isinstance(r, PerformanceResult) and not r.success]

        if not valid_results:
            return {
                "success": False,
                "error": "No successful search operations",
                "failed_count": len(failed_results)
            }

        durations = [r.duration for r in valid_results]

        return {
            "success": True,
            "total_requests": len(tasks),
            "successful_requests": len(valid_results),
            "failed_requests": len(failed_results),
            "concurrent_requests": concurrent_requests,
            "avg_latency": statistics.mean(durations),
            "median_latency": statistics.median(durations),
            "p95_latency": self._percentile(durations, 0.95),
            "p99_latency": self._percentile(durations, 0.99),
            "min_latency": min(durations),
            "max_latency": max(durations),
            "requests_per_second": len(valid_results) / max(durations) if durations else 0,
            "all_under_2s": all(d < 2.0 for d in durations),
            "two_second_compliance": sum(1 for d in durations if d < 2.0) / len(durations) * 100
        }

    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """Calculate percentile from data"""
        sorted_data = sorted(data)
        index = int(percentile * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]


class TestVectorSearchPerformance:
    """Performance tests for vector search operations"""

    @pytest.fixture
    def performance_tester(self):
        """Create performance tester instance"""
        return VectorPerformanceTester()

    @pytest.fixture
    def test_collection_name(self):
        """Generate test collection name"""
        return f"perf_test_{int(time.time())}"

    @pytest.fixture
    def performance_test_data(self):
        """Generate test data for performance testing"""
        base_documents = [
            "Vector database performance optimization techniques",
            "Semantic search algorithms for large datasets",
            "High-performance API design with FastAPI framework",
            "Machine learning model deployment at scale",
            "Database indexing strategies for vector similarity",
            "Container orchestration for AI applications",
            "Distributed computing patterns for ML workloads",
            "Real-time search engine architecture design",
            "Scalable vector embeddings storage solutions",
            "Performance monitoring for database systems"
        ]

        # Create larger dataset by variation
        documents = []
        for i in range(100):  # 1000 total documents
            for doc in base_documents:
                documents.append(f"Document {i}: {doc}")

        return {
            "documents": documents,
            "ids": [f"perf_doc_{i}" for i in range(len(documents))],
            "metadatas": [
                {"batch": i // 10, "category": "performance_test", "doc_id": i}
                for i in range(len(documents))
            ]
        }

    @pytest.fixture
    def search_queries(self):
        """Performance test search queries"""
        return [
            "vector database optimization performance",
            "semantic search large scale datasets",
            "API framework high performance design",
            "machine learning deployment scalability",
            "database indexing vector similarity search",
            "container AI application orchestration",
            "distributed ML workload computing patterns",
            "real-time search architecture design",
            "scalable vector storage embeddings",
            "database performance monitoring systems"
        ]

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_setup_performance_test_collection(
        self,
        performance_tester,
        test_collection_name,
        performance_test_data
    ):
        """Setup collection with test data for performance testing"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Create collection
                create_response = await client.post(
                    f"{performance_tester.base_url}/collections",
                    json={
                        "name": test_collection_name,
                        "metadata": {"test_type": "performance", "document_count": len(performance_test_data["documents"])}
                    }
                )

                assert create_response.status_code in [200, 201]

                # Add documents in batches for better performance
                batch_size = 50
                documents = performance_test_data["documents"]

                for i in range(0, len(documents), batch_size):
                    batch_docs = documents[i:i+batch_size]
                    batch_ids = performance_test_data["ids"][i:i+batch_size]
                    batch_metadatas = performance_test_data["metadatas"][i:i+batch_size]

                    add_response = await client.post(
                        f"{performance_tester.base_url}/collections/{test_collection_name}/add",
                        json={
                            "documents": batch_docs,
                            "ids": batch_ids,
                            "metadatas": batch_metadatas
                        }
                    )

                    assert add_response.status_code == 200, f"Failed to add batch starting at {i}"

                # Verify collection
                info_response = await client.get(f"{performance_tester.base_url}/collections/{test_collection_name}")
                assert info_response.status_code == 200

                collection_info = info_response.json()
                assert collection_info["count"] == len(documents)

        except httpx.ConnectError:
            pytest.skip("ChromaDB not available for performance testing")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_single_query_performance(
        self,
        performance_tester,
        test_collection_name,
        search_queries
    ):
        """Test single query performance meets <2 second requirement"""
        try:
            # Test each query individually
            for query in search_queries[:5]:  # Test first 5 queries
                start_time = time.time()

                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{performance_tester.base_url}/collections/{test_collection_name}/query",
                        json={
                            "query_texts": [query],
                            "n_results": 10
                        }
                    )

                query_time = time.time() - start_time

                # Core requirement: <2 second response time
                assert query_time < 2.0, f"Query '{query}' took {query_time:.3f}s, exceeds 2s requirement"
                assert response.status_code == 200, f"Query failed with status {response.status_code}"

                # Validate response structure
                results = response.json()
                assert "documents" in results
                assert len(results["documents"][0]) > 0, "Query returned no results"

        except httpx.ConnectError:
            pytest.skip("ChromaDB not available for performance testing")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_query_performance(
        self,
        performance_tester,
        test_collection_name,
        search_queries
    ):
        """Test concurrent query performance under load"""
        try:
            # Test with different concurrency levels
            concurrency_levels = [1, 3, 5]

            for concurrent_requests in concurrency_levels:
                print(f"Testing {concurrent_requests} concurrent requests...")

                performance_result = await performance_tester.benchmark_search_latency(
                    collection_name=test_collection_name,
                    queries=search_queries[:5],  # Use first 5 queries
                    n_results=10,
                    concurrent_requests=concurrent_requests
                )

                assert performance_result["success"], f"Performance test failed: {performance_result.get('error')}"

                # Performance assertions
                assert performance_result["all_under_2s"], (
                    f"Not all queries under 2s. Max latency: {performance_result['max_latency']:.3f}s"
                )

                assert performance_result["two_second_compliance"] >= 95.0, (
                    f"Only {performance_result['two_second_compliance']:.1f}% queries under 2s"
                )

                assert performance_result["failed_requests"] == 0, (
                    f"{performance_result['failed_requests']} requests failed"
                )

                # Log performance metrics
                print(f"  Concurrent requests: {concurrent_requests}")
                print(f"  Average latency: {performance_result['avg_latency']:.3f}s")
                print(f"  95th percentile: {performance_result['p95_latency']:.3f}s")
                print(f"  Max latency: {performance_result['max_latency']:.3f}s")
                print(f"  2s compliance: {performance_result['two_second_compliance']:.1f}%")

        except httpx.ConnectError:
            pytest.skip("ChromaDB not available for performance testing")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_result_set_performance(
        self,
        performance_tester,
        test_collection_name,
        search_queries
    ):
        """Test performance with large result sets"""
        try:
            result_set_sizes = [10, 25, 50]

            for n_results in result_set_sizes:
                query = search_queries[0]  # Use first query
                start_time = time.time()

                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.post(
                        f"{performance_tester.base_url}/collections/{test_collection_name}/query",
                        json={
                            "query_texts": [query],
                            "n_results": n_results
                        }
                    )

                query_time = time.time() - start_time

                assert response.status_code == 200
                assert query_time < 2.0, f"Query with {n_results} results took {query_time:.3f}s"

                results = response.json()
                actual_results = len(results["documents"][0])

                # Should return requested number of results (or all available if less)
                assert actual_results <= n_results
                assert actual_results > 0

                print(f"  {n_results} results requested: {query_time:.3f}s ({actual_results} returned)")

        except httpx.ConnectError:
            pytest.skip("ChromaDB not available for performance testing")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_sustained_load_performance(
        self,
        performance_tester,
        test_collection_name,
        search_queries
    ):
        """Test performance under sustained load"""
        try:
            # Simulate sustained load over time
            duration_seconds = 30  # 30 second test
            requests_per_second = 2
            total_requests = duration_seconds * requests_per_second

            print(f"Sustained load test: {total_requests} requests over {duration_seconds} seconds")

            async def timed_request(query: str, delay: float) -> PerformanceResult:
                """Execute request after delay"""
                await asyncio.sleep(delay)
                start_time = time.time()

                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            f"{performance_tester.base_url}/collections/{test_collection_name}/query",
                            json={
                                "query_texts": [query],
                                "n_results": 5
                            }
                        )

                    duration = time.time() - start_time

                    return PerformanceResult(
                        operation="sustained_search",
                        duration=duration,
                        success=response.status_code == 200,
                        error=None if response.status_code == 200 else f"HTTP {response.status_code}"
                    )

                except Exception as e:
                    duration = time.time() - start_time
                    return PerformanceResult(
                        operation="sustained_search",
                        duration=duration,
                        success=False,
                        error=str(e)
                    )

            # Create tasks with staggered timing
            tasks = []
            for i in range(total_requests):
                query = search_queries[i % len(search_queries)]
                delay = i / requests_per_second  # Stagger requests
                tasks.append(timed_request(query, delay))

            # Execute sustained load
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            # Analyze results
            valid_results = [r for r in results if isinstance(r, PerformanceResult)]
            successful_results = [r for r in valid_results if r.success]
            failed_results = [r for r in valid_results if not r.success]

            assert len(successful_results) > 0, "No successful requests in sustained load test"

            durations = [r.duration for r in successful_results]
            success_rate = len(successful_results) / len(valid_results) * 100

            # Performance assertions
            assert success_rate >= 95.0, f"Success rate {success_rate:.1f}% below 95%"
            assert all(d < 2.0 for d in durations), f"Some requests exceeded 2s: max={max(durations):.3f}s"

            avg_latency = statistics.mean(durations)
            p95_latency = performance_tester._percentile(durations, 0.95)

            print(f"Sustained load results:")
            print(f"  Total requests: {len(valid_results)}")
            print(f"  Successful: {len(successful_results)}")
            print(f"  Failed: {len(failed_results)}")
            print(f"  Success rate: {success_rate:.1f}%")
            print(f"  Average latency: {avg_latency:.3f}s")
            print(f"  95th percentile: {p95_latency:.3f}s")
            print(f"  Test duration: {total_time:.1f}s")

        except httpx.ConnectError:
            pytest.skip("ChromaDB not available for performance testing")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cleanup_performance_collection(
        self,
        performance_tester,
        test_collection_name
    ):
        """Cleanup performance test collection"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{performance_tester.base_url}/collections/{test_collection_name}"
                )

                # Cleanup should succeed or collection should not exist
                assert response.status_code in [200, 404]

        except httpx.ConnectError:
            pytest.skip("ChromaDB not available for cleanup")


# Test configuration
pytestmark = [
    pytest.mark.performance,
    pytest.mark.asyncio
]


if __name__ == "__main__":
    # Run performance tests with detailed output
    pytest.main([
        __file__,
        "-v",
        "-s",  # Show print statements
        "-m", "performance",
        "--tb=short"
    ])