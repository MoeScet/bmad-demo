#!/usr/bin/env python3
"""
Smoke test script for BMAD services.
Validates basic health and connectivity of deployed services.
"""
import argparse
import asyncio
import sys
import time
from typing import Dict, List, Optional

import httpx


class SmokeTestRunner:
    """Runs smoke tests against deployed BMAD services."""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.results: List[Dict] = []
    
    async def test_health_endpoint(self, service_name: str, port: int) -> Dict:
        """Test health endpoint for a service."""
        url = f"{self.base_url}:{port}/health"
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "service": service_name,
                        "status": "PASS",
                        "response_time_ms": round(response_time, 2),
                        "details": data
                    }
                else:
                    return {
                        "service": service_name,
                        "status": "FAIL",
                        "response_time_ms": round(response_time, 2),
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "service": service_name,
                "status": "FAIL", 
                "response_time_ms": round(response_time, 2),
                "error": str(e)
            }
    
    async def test_api_endpoint(self, service_name: str, port: int, path: str = "/") -> Dict:
        """Test basic API endpoint for a service."""
        url = f"{self.base_url}:{port}{path}"
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code in [200, 404]:  # 404 is acceptable for root endpoints
                    return {
                        "service": service_name,
                        "endpoint": path,
                        "status": "PASS",
                        "response_time_ms": round(response_time, 2),
                        "http_status": response.status_code
                    }
                else:
                    return {
                        "service": service_name,
                        "endpoint": path, 
                        "status": "FAIL",
                        "response_time_ms": round(response_time, 2),
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "service": service_name,
                "endpoint": path,
                "status": "FAIL",
                "response_time_ms": round(response_time, 2),
                "error": str(e)
            }
    
    async def run_tests(self) -> bool:
        """Run all smoke tests and return success status."""
        services = [
            ("teams-bot", 8001),
            ("query-orchestration", 8002),
            ("fast-qa", 8003),
            ("semantic-search", 8004),
            ("safety-classification", 8005),
            ("user-context", 8006),
            ("manual-processing", 8007),
            ("management-api", 8008),
        ]
        
        print(f"Running smoke tests against {self.base_url}")
        print(f"Timeout: {self.timeout}s")
        print("=" * 50)
        
        # Test health endpoints
        health_tasks = [
            self.test_health_endpoint(name, port) 
            for name, port in services
        ]
        health_results = await asyncio.gather(*health_tasks, return_exceptions=True)
        
        # Test basic API endpoints
        api_tasks = [
            self.test_api_endpoint(name, port) 
            for name, port in services
        ]
        api_results = await asyncio.gather(*api_tasks, return_exceptions=True)
        
        # Combine results
        all_results = []
        for result in health_results + api_results:
            if isinstance(result, Exception):
                all_results.append({
                    "service": "unknown",
                    "status": "FAIL",
                    "error": str(result)
                })
            else:
                all_results.append(result)
        
        # Print results
        passed = 0
        failed = 0
        
        for result in all_results:
            status_icon = "[PASS]" if result["status"] == "PASS" else "[FAIL]"
            service = result["service"]
            endpoint = result.get("endpoint", "/health")
            response_time = result.get("response_time_ms", 0)
            
            print(f"{status_icon} {service} {endpoint} - {response_time}ms")
            
            if result["status"] == "PASS":
                passed += 1
            else:
                failed += 1
                if "error" in result:
                    print(f"    Error: {result['error']}")
        
        print("=" * 50)
        print(f"Results: {passed} passed, {failed} failed")
        
        return failed == 0


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run smoke tests for BMAD services")
    parser.add_argument(
        "--env", 
        choices=["development", "staging", "production"],
        default="development",
        help="Environment to test against"
    )
    parser.add_argument(
        "--base-url",
        help="Base URL for services (overrides environment default)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout in seconds for each test"
    )
    
    args = parser.parse_args()
    
    # Determine base URL
    if args.base_url:
        base_url = args.base_url
    else:
        url_map = {
            "development": "http://localhost",
            "staging": "https://bmad-staging.railway.app",
            "production": "https://bmad-prod.railway.app"
        }
        base_url = url_map.get(args.env, "http://localhost")
    
    # Run tests
    runner = SmokeTestRunner(base_url, args.timeout)
    success = await runner.run_tests()
    
    if success:
        print("All smoke tests passed!")
        sys.exit(0)
    else:
        print("Some smoke tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())