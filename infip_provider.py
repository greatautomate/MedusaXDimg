"""
MedusaXD Image Generator - Enhanced Error Handling
Fixed JSON decode errors with comprehensive debugging
"""

import requests
import asyncio
import random
import time
from typing import Optional, List
import logging
import json

logger = logging.getLogger(__name__)

class ImageData:
    def __init__(self, url: str = None, b64_json: str = None):
        self.url = url
        self.b64_json = b64_json

class ImageResponse:
    def __init__(self, created: int, data: List[ImageData]):
        self.created = created
        self.data = data

class MedusaXDImageGenerator:
    """Enhanced MedusaXD Image Generator with robust error handling"""

    AVAILABLE_MODELS = ["flux", "turbo", "gptimage"]

    ASPECT_RATIOS = {
        "landscape": "16:9",
        "portrait": "9:16", 
        "square": "1:1",
        "photo": "4:3",
        "classic": "3:2",
        "wide": "21:9",
        "golden": "1.618:1",
        "cinema": "2.35:1",
        "poster": "3:4"
    }

    SIZE_MAPPING = {
        "landscape": "1344x768",
        "portrait": "768x1344",
        "square": "1024x1024",
        "photo": "1024x768",
        "classic": "1024x683",
        "wide": "1344x576",
        "golden": "1024x633",
        "cinema": "1344x572",
        "poster": "768x1024"
    }

    # Multiple API endpoints for fallback
    API_ENDPOINTS = [
        "https://aiworldcreator.com/v1/images/generations",
        "https://api.aiworldcreator.com/v1/images/generations",  # Alternative subdomain
        "https://aiworldcreator.com/api/v1/images/generations"   # Alternative path
    ]

    def __init__(self):
        """Initialize with enhanced session configuration"""
        self.session = requests.Session()

        # Enhanced headers
        self.session.headers.update({
            "accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "MedusaXD-Bot/2.0 (AI Image Generator)",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache"
        })

    async def _make_request_with_retry(self, payload: dict, max_retries: int = 3) -> dict:
        """Enhanced request method with comprehensive error handling"""

        for attempt in range(max_retries):
            for endpoint_idx, endpoint in enumerate(self.API_ENDPOINTS):
                try:
                    logger.info(f"🎨 Attempt {attempt + 1}/{max_retries} using endpoint {endpoint_idx + 1}")

                    if attempt > 0:
                        delay = min(2 ** attempt + random.uniform(0, 2), 15)
                        logger.info(f"⏳ Waiting {delay:.1f}s before retry...")
                        await asyncio.sleep(delay)

                    # Make the request with enhanced debugging
                    response = await asyncio.to_thread(
                        self._sync_request_debug, 
                        endpoint,
                        payload, 
                        timeout=60
                    )

                    if response and "data" in response and response["data"]:
                        logger.info(f"✅ Successfully generated image using endpoint {endpoint_idx + 1}")
                        return response
                    else:
                        logger.warning(f"⚠️ Empty or invalid response from endpoint {endpoint_idx + 1}")
                        continue

                except requests.exceptions.Timeout:
                    logger.warning(f"⏰ Timeout on endpoint {endpoint_idx + 1}")
                    continue

                except requests.exceptions.ConnectionError as e:
                    logger.warning(f"🔌 Connection error on endpoint {endpoint_idx + 1}: {e}")
                    continue

                except requests.exceptions.HTTPError as e:
                    status_code = e.response.status_code if e.response else 0
                    logger.warning(f"🔥 HTTP {status_code} error on endpoint {endpoint_idx + 1}")

                    # Log response content for debugging
                    if e.response:
                        try:
                            response_text = e.response.text[:500]
                            logger.error(f"Response content: {response_text}")
                        except:
                            pass
                    continue

                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error on endpoint {endpoint_idx + 1}: {e}")
                    continue

                except Exception as e:
                    logger.error(f"❌ Unexpected error on endpoint {endpoint_idx + 1}: {e}")
                    continue

            # Wait between full retry cycles
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                logger.info(f"😴 All endpoints failed, waiting {wait_time}s before next cycle...")
                await asyncio.sleep(wait_time)

        raise RuntimeError("All API endpoints failed after maximum retries")

    def _sync_request_debug(self, endpoint: str, payload: dict, timeout: int) -> dict:
        """Enhanced synchronous request with comprehensive debugging"""
        try:
            logger.info(f"🔗 Making request to: {endpoint}")
            logger.info(f"📦 Payload: {json.dumps(payload, indent=2)}")

            response = self.session.post(
                endpoint,
                json=payload,
                timeout=timeout
            )

            logger.info(f"📊 Response status: {response.status_code}")
            logger.info(f"📋 Response headers: {dict(response.headers)}")

            # Check if response is empty
            if not response.content:
                logger.error("❌ Empty response content")
                raise RuntimeError("API returned empty response")

            # Log first 200 chars of response for debugging
            content_preview = response.text[:200] if response.text else "No content"
            logger.info(f"📄 Response preview: {content_preview}")

            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                logger.error(f"❌ Unexpected content type: {content_type}")
                logger.error(f"Full response: {response.text}")
                raise RuntimeError(f"API returned {content_type} instead of JSON")

            response.raise_for_status()

            # Try to parse JSON with better error handling
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON decode failed: {e}")
                logger.error(f"Raw response: {response.text}")
                raise RuntimeError(f"Invalid JSON response: {str(e)}")

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {e}")
            raise

    async def generate_images(
        self,
        prompt: str,
        model: str = "turbo",
        num_images: int = 1,
        aspect_ratio: str = "landscape",
        seed: Optional[int] = None,
        timeout: int = 60,
        style: str = "realistic"
    ) -> ImageResponse:
        """Generate images with enhanced error handling"""

        # Validate parameters
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model '{model}' not supported. Available models: {self.AVAILABLE_MODELS}")

        if num_images < 1 or num_images > 4:
            raise ValueError("Number of images must be between 1 and 4")

        if aspect_ratio not in self.ASPECT_RATIOS:
            logger.warning(f"Unknown aspect ratio '{aspect_ratio}', defaulting to 'landscape'")
            aspect_ratio = "landscape"

        # Clean prompt
        prompt = prompt.strip()
        if len(prompt) < 2:
            raise ValueError("Prompt must be at least 2 characters long")

        if len(prompt) > 1000:
            prompt = prompt[:1000]
            logger.warning("⚠️ Prompt truncated to 1000 characters")

        # Map parameters
        size = self.SIZE_MAPPING.get(aspect_ratio, "1024x1024")
        api_aspect_ratio = self.ASPECT_RATIOS[aspect_ratio]

        if seed is None:
            seed = random.randint(1, 1000000)

        # Create payload
        payload = {
            "prompt": prompt,
            "model": model,
            "n": num_images,
            "size": size,
            "response_format": "url",
            "user": "medusaxd-bot",
            "style": style,
            "aspect_ratio": api_aspect_ratio,
            "timeout": timeout,
            "image_format": "png",
            "seed": seed
        }

        try:
            logger.info(f"🎨 Generating {num_images} image(s) with {model}")
            logger.info(f"📝 Prompt: {prompt}")

            # First test API connectivity
            if not await self.test_connection():
                raise RuntimeError("API connectivity test failed - service may be down")

            # Make request with retry logic
            result = await self._make_request_with_retry(payload, max_retries=3)

            # Process response
            result_data = []
            for item in result["data"]:
                if "url" in item and item["url"]:
                    result_data.append(ImageData(url=item["url"]))

            if not result_data:
                raise RuntimeError("No valid images in API response")

            logger.info(f"✅ Successfully generated {len(result_data)} image(s)")
            return ImageResponse(created=result.get("created", int(time.time())), data=result_data)

        except Exception as e:
            logger.error(f"❌ Image generation failed: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test API connectivity with simple request"""
        test_payload = {
            "prompt": "test",
            "model": "turbo",
            "n": 1,
            "size": "512x512",
            "response_format": "url",
            "user": "test",
            "style": "realistic",
            "aspect_ratio": "1:1",
            "timeout": 15,
            "image_format": "png",
            "seed": 12345
        }

        for endpoint in self.API_ENDPOINTS:
            try:
                logger.info(f"🧪 Testing endpoint: {endpoint}")

                response = await asyncio.to_thread(
                    self._sync_request_debug, 
                    endpoint,
                    test_payload, 
                    timeout=15
                )

                if response:
                    logger.info(f"✅ Endpoint {endpoint} is working")
                    return True

            except Exception as e:
                logger.warning(f"❌ Endpoint {endpoint} failed: {e}")
                continue

        logger.error("❌ All API endpoints are down")
        return False

    def get_models(self) -> List[str]:
        return self.AVAILABLE_MODELS.copy()

    def get_aspect_ratios(self) -> List[str]:
        return list(self.ASPECT_RATIOS.keys())

    def get_model_info(self) -> dict:
        return {
            "flux": {
                "name": "Flux",
                "description": "High-quality detailed generation",
                "best_for": "Professional artwork, detailed scenes"
            },
            "turbo": {
                "name": "Turbo", 
                "description": "Fast generation with good quality",
                "best_for": "Quick prototypes, general use"
            },
            "gptimage": {
                "name": "GPT Image",
                "description": "Creative AI generation", 
                "best_for": "Creative artwork, concept art"
            }
        }
