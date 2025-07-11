#!/usr/bin/env python3
"""
Test FlareSolverr against Cloudflare-protected providers.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlareSolverrTester:
    """Test FlareSolverr against Cloudflare-protected sites."""
    
    def __init__(self, flaresolverr_url: str = "http://172.16.40.12:8191"):
        self.flaresolverr_url = flaresolverr_url
        self.session_id = None
        
    async def test_flaresolverr_health(self) -> bool:
        """Test if FlareSolverr is accessible and working."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.flaresolverr_url}/")
                
                if response.status_code == 200:
                    logger.info("✅ FlareSolverr is accessible")
                    return True
                else:
                    logger.error(f"❌ FlareSolverr returned status {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ FlareSolverr health check failed: {e}")
            return False
    
    async def create_session(self) -> bool:
        """Create a FlareSolverr session."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.flaresolverr_url}/v1",
                    json={
                        "cmd": "sessions.create",
                        "session": "kuroibara_test"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ok":
                        self.session_id = data["session"]
                        logger.info(f"✅ Created FlareSolverr session: {self.session_id}")
                        return True
                    else:
                        logger.error(f"❌ Session creation failed: {data.get('message')}")
                        return False
                else:
                    logger.error(f"❌ Session creation returned status {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Session creation failed: {e}")
            return False
    
    async def test_direct_request(self, url: str) -> Dict[str, Any]:
        """Test direct request without FlareSolverr."""
        result = {
            "url": url,
            "method": "direct",
            "success": False,
            "status_code": None,
            "error": None,
            "response_time": None,
            "cloudflare_detected": False
        }
        
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = await client.get(url, headers=headers)
                
                end_time = time.time()
                result["response_time"] = round(end_time - start_time, 2)
                result["status_code"] = response.status_code
                
                # Check for Cloudflare protection
                content = response.text.lower()
                if (response.status_code in [403, 503, 521] or 
                    "cloudflare" in content or
                    "checking your browser" in content or
                    "ddos protection" in content):
                    result["cloudflare_detected"] = True
                    result["error"] = f"Cloudflare protection detected (status: {response.status_code})"
                elif response.status_code == 200:
                    result["success"] = True
                else:
                    result["error"] = f"HTTP {response.status_code}"
                    
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    async def test_flaresolverr_request(self, url: str) -> Dict[str, Any]:
        """Test request through FlareSolverr."""
        result = {
            "url": url,
            "method": "flaresolverr",
            "success": False,
            "status_code": None,
            "error": None,
            "response_time": None,
            "content_length": None
        }
        
        if not self.session_id:
            if not await self.create_session():
                result["error"] = "Failed to create FlareSolverr session"
                return result
        
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.flaresolverr_url}/v1",
                    json={
                        "cmd": "request.get",
                        "url": url,
                        "session": self.session_id,
                        "maxTimeout": 60000
                    }
                )
                
                end_time = time.time()
                result["response_time"] = round(end_time - start_time, 2)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ok":
                        solution = data.get("solution", {})
                        result["status_code"] = solution.get("status")
                        result["content_length"] = len(solution.get("response", ""))
                        
                        if solution.get("status") == 200:
                            result["success"] = True
                        else:
                            result["error"] = f"HTTP {solution.get('status')}"
                    else:
                        result["error"] = f"FlareSolverr error: {data.get('message')}"
                else:
                    result["error"] = f"FlareSolverr API returned {response.status_code}"
                    
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    async def test_provider(self, name: str, url: str) -> Dict[str, Any]:
        """Test a provider with both direct and FlareSolverr requests."""
        logger.info(f"🧪 Testing {name}: {url}")
        
        # Test direct request
        direct_result = await self.test_direct_request(url)
        
        # Test FlareSolverr request
        flaresolverr_result = await self.test_flaresolverr_request(url)
        
        # Determine if FlareSolverr helped
        improvement = False
        if not direct_result["success"] and flaresolverr_result["success"]:
            improvement = True
        
        result = {
            "provider_name": name,
            "url": url,
            "direct": direct_result,
            "flaresolverr": flaresolverr_result,
            "flaresolverr_helped": improvement
        }
        
        # Log results
        if direct_result["success"]:
            logger.info(f"  ✅ Direct request successful ({direct_result['response_time']}s)")
        else:
            logger.info(f"  ❌ Direct request failed: {direct_result['error']}")
            
        if flaresolverr_result["success"]:
            logger.info(f"  ✅ FlareSolverr successful ({flaresolverr_result['response_time']}s, {flaresolverr_result['content_length']} bytes)")
        else:
            logger.info(f"  ❌ FlareSolverr failed: {flaresolverr_result['error']}")
            
        if improvement:
            logger.info(f"  🎉 FlareSolverr bypassed protection!")
        
        return result
    
    async def destroy_session(self):
        """Clean up FlareSolverr session."""
        if not self.session_id:
            return
            
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                await client.post(
                    f"{self.flaresolverr_url}/v1",
                    json={
                        "cmd": "sessions.destroy",
                        "session": self.session_id
                    }
                )
                logger.info(f"🧹 Destroyed FlareSolverr session: {self.session_id}")
                
        except Exception as e:
            logger.error(f"Failed to destroy session: {e}")
        
        self.session_id = None


async def main():
    """Main test function."""
    logger.info("🚀 Starting FlareSolverr tests...")
    
    # Cloudflare-protected providers identified from our tests
    test_providers = [
        ("ReaperScans", "https://reaperscans.com"),
        ("ManhuaFast", "https://manhuafast.com"),
        ("Manhuaga", "https://manhuaga.com"),
        # Add a few more that might be Cloudflare protected
        ("MangaFire", "https://mangafire.to"),
        ("MangaReaderTo", "https://mangareader.to"),
        ("Toonily", "https://toonily.com"),  # This one was working, for comparison
    ]
    
    tester = FlareSolverrTester("http://172.16.40.12:8191")
    
    # Test FlareSolverr health
    if not await tester.test_flaresolverr_health():
        logger.error("❌ FlareSolverr is not accessible. Exiting.")
        return
    
    results = []
    
    try:
        for name, url in test_providers:
            result = await tester.test_provider(name, url)
            results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(2)
    
    finally:
        await tester.destroy_session()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*60)
    
    successful_bypasses = 0
    total_cloudflare_blocks = 0
    
    for result in results:
        name = result["provider_name"]
        direct = result["direct"]
        flare = result["flaresolverr"]
        helped = result["flaresolverr_helped"]
        
        if direct["cloudflare_detected"] or not direct["success"]:
            total_cloudflare_blocks += 1
            
        if helped:
            successful_bypasses += 1
            logger.info(f"🎉 {name}: FlareSolverr successfully bypassed protection")
        elif direct["success"]:
            logger.info(f"✅ {name}: Direct access works (no protection)")
        elif flare["success"]:
            logger.info(f"⚠️  {name}: FlareSolverr works but direct also works")
        else:
            logger.info(f"❌ {name}: Both methods failed")
    
    logger.info(f"\n📈 Success Rate: {successful_bypasses}/{total_cloudflare_blocks} Cloudflare bypasses")
    
    # Save detailed results
    with open("flaresolverr_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("💾 Detailed results saved to flaresolverr_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
