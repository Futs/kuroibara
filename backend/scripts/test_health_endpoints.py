#!/usr/bin/env python3
"""Test script for system health endpoints."""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any


async def test_health_endpoint(session: aiohttp.ClientSession, base_url: str, endpoint: str, name: str) -> Dict[str, Any]:
    """Test a single health endpoint."""
    print(f"\n🔍 Testing {name}: {endpoint}")
    
    try:
        async with session.get(f"{base_url}{endpoint}") as response:
            print(f"Status: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                return {"success": True, "data": data, "status": response.status}
            else:
                error_text = await response.text()
                return {"success": False, "error": error_text, "status": response.status}
                
    except Exception as e:
        return {"success": False, "error": str(e), "status": None}


def print_health_summary(data: Dict[str, Any], endpoint_name: str):
    """Print formatted health summary."""
    if not data.get("success"):
        print(f"❌ {endpoint_name} failed: {data.get('error', 'Unknown error')}")
        return
    
    health_data = data["data"]
    status = health_data.get("status", "unknown")
    status_icon = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
    
    print(f"{status_icon} Overall Status: {status}")
    
    # Print summary if available
    if "summary" in health_data:
        summary = health_data["summary"]
        healthy = summary.get("healthy_components", 0)
        total = summary.get("total_components", 0)
        percentage = summary.get("health_percentage", 0)
        response_time = summary.get("total_response_time_ms", 0)
        
        print(f"📊 Health: {healthy}/{total} components ({percentage}%)")
        print(f"⏱️ Response Time: {response_time}ms")
    
    # Print components if available
    if "components" in health_data:
        print("🔧 Components:")
        for comp_name, comp_data in health_data["components"].items():
            comp_status = comp_data.get("status", "unknown")
            comp_icon = "✅" if comp_status == "healthy" else "⚠️" if comp_status == "degraded" else "❌"
            message = comp_data.get("message", "No message")
            response_time = comp_data.get("response_time_ms")
            
            if response_time is not None:
                print(f"  {comp_icon} {comp_name}: {message} ({response_time}ms)")
            else:
                print(f"  {comp_icon} {comp_name}: {message}")
    
    # Print indexers if available
    if "indexers" in health_data:
        print("🔍 Indexers:")
        for idx_name, idx_data in health_data["indexers"].items():
            idx_status = idx_data.get("status", "unknown")
            idx_icon = "✅" if idx_status == "healthy" else "❌"
            tier = idx_data.get("tier", "unknown")
            message = idx_data.get("message", "No message")
            
            print(f"  {idx_icon} {idx_name} ({tier}): {message}")


async def main():
    """Main test function."""
    print("🏥 System Health Endpoints Test Suite")
    print("=" * 60)
    
    # Configuration
    base_url = "http://127.0.0.1:8000"
    
    endpoints = [
        ("/api/v1/health/", "System Health"),
        ("/api/v1/health/quick", "Quick Health"),
        ("/api/v1/health/indexers", "Indexers Health")
    ]
    
    async with aiohttp.ClientSession() as session:
        results = {}
        
        # Test all endpoints
        for endpoint, name in endpoints:
            result = await test_health_endpoint(session, base_url, endpoint, name)
            results[name] = result
            print_health_summary(result, name)
        
        # Overall test summary
        print("\n" + "=" * 60)
        print("📋 Test Summary:")
        
        successful_tests = 0
        total_tests = len(endpoints)
        
        for name, result in results.items():
            if result["success"]:
                status = result["data"].get("status", "unknown")
                status_icon = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
                print(f"  {status_icon} {name}: {status}")
                if status in ["healthy", "degraded"]:
                    successful_tests += 1
            else:
                print(f"  ❌ {name}: Failed ({result.get('status', 'No response')})")
        
        print(f"\n🎯 Results: {successful_tests}/{total_tests} endpoints working")
        
        if successful_tests == total_tests:
            print("🎉 All health endpoints are working correctly!")
            return 0
        else:
            print("⚠️ Some health endpoints have issues")
            return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
