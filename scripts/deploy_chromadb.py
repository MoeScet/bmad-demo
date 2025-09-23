#!/usr/bin/env python3
"""
ChromaDB deployment script for Railway platform.

Handles deployment of ChromaDB service with proper configuration
and validation following BMAD deployment standards.
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any, Optional
import argparse

import httpx


class ChromaDBDeployment:
    """Handles ChromaDB deployment to Railway platform"""

    def __init__(self, environment: str = "staging"):
        self.environment = environment
        self.service_name = f"bmad-chromadb-{environment}"
        self.base_url = None

    async def deploy(self) -> bool:
        """Deploy ChromaDB service to Railway"""
        try:
            print(f"🚀 Deploying ChromaDB to {self.environment} environment...")

            # 1. Deploy via Railway CLI
            result = subprocess.run([
                "railway", "up",
                "--service", self.service_name,
                "--environment", self.environment,
                "--detach"
            ], cwd="infrastructure/chromadb", capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Deployment failed: {result.stderr}")
                return False

            print("✅ Deployment initiated successfully")

            # 2. Wait for service to be ready
            await self._wait_for_service_ready()

            # 3. Validate deployment
            await self._validate_deployment()

            print(f"🎉 ChromaDB deployed successfully to {self.environment}")
            return True

        except Exception as e:
            print(f"❌ Deployment error: {str(e)}")
            return False

    async def _wait_for_service_ready(self, timeout: int = 300) -> None:
        """Wait for ChromaDB service to be ready"""
        print("⏳ Waiting for service to be ready...")

        # Get service URL
        result = subprocess.run([
            "railway", "status", "--service", self.service_name
        ], capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Failed to get service status: {result.stderr}")

        # Extract URL from status (simplified - in real implementation parse JSON)
        # For now, use expected URL pattern
        self.base_url = f"https://{self.service_name}.railway.app"

        start_time = time.time()
        async with httpx.AsyncClient(timeout=10.0) as client:
            while time.time() - start_time < timeout:
                try:
                    response = await client.get(f"{self.base_url}/api/v1/heartbeat")
                    if response.status_code == 200:
                        print("✅ Service is ready")
                        return
                except httpx.RequestError:
                    pass

                await asyncio.sleep(10)

        raise Exception(f"Service not ready after {timeout} seconds")

    async def _validate_deployment(self) -> None:
        """Validate ChromaDB deployment"""
        print("🔍 Validating deployment...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test basic connectivity
            response = await client.get(f"{self.base_url}/api/v1/heartbeat")
            if response.status_code != 200:
                raise Exception(f"Health check failed: {response.status_code}")

            # Test collection operations
            test_collection = f"test_deployment_{int(time.time())}"

            # Create test collection
            response = await client.post(
                f"{self.base_url}/api/v1/collections",
                json={"name": test_collection}
            )

            if response.status_code not in [200, 201]:
                raise Exception(f"Failed to create test collection: {response.status_code}")

            # List collections
            response = await client.get(f"{self.base_url}/api/v1/collections")
            if response.status_code != 200:
                raise Exception(f"Failed to list collections: {response.status_code}")

            collections = response.json()
            collection_names = [c.get("name") for c in collections]

            if test_collection not in collection_names:
                raise Exception("Test collection not found in collections list")

            # Clean up test collection
            response = await client.delete(f"{self.base_url}/api/v1/collections/{test_collection}")

            print("✅ Deployment validation passed")

    async def rollback(self) -> bool:
        """Rollback to previous deployment"""
        try:
            print(f"🔄 Rolling back {self.service_name}...")

            result = subprocess.run([
                "railway", "rollback",
                "--service", self.service_name,
                "--confirm"
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Rollback failed: {result.stderr}")
                return False

            print("✅ Rollback completed")
            return True

        except Exception as e:
            print(f"❌ Rollback error: {str(e)}")
            return False


async def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy ChromaDB to Railway")
    parser.add_argument(
        "--environment",
        choices=["staging", "production"],
        default="staging",
        help="Deployment environment"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback previous deployment"
    )

    args = parser.parse_args()

    deployment = ChromaDBDeployment(args.environment)

    if args.rollback:
        success = await deployment.rollback()
    else:
        success = await deployment.deploy()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())