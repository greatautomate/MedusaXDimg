"""
MedusaXD Image Generator - AIWorldCreator API Provider (Fixed)
Fixed to match the exact API specification and handle JSON decode errors
"""

import requests
import asyncio
import random
import time
import json
from typing import Optional, List
import logging

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
    """
    MedusaXD Image Generator using AIWorldCreator API
    Fixed to match exact API specification
    """

    # Exact models from API
    AVAILABLE_MODELS = ["flux", "turbo", "gptimage"]

    # Standard aspect ratios that work with the API
    ASPECT_RATIOS = {
        "landscape": "16:9",
        "portrait": "9:16", 
        "square": "1:1",
        "wide": "21:9",
        "cinema": "2.35:1",
        "photo": "4:3"
    }

    # Standard sizes that work with the API
    SIZE_MAPPING = {
        "landscape": "1344x768",
        "portrait": "768x1344",
        "square": "1024x1024",
        "wide": "1344x576", 
        "cinema": "1344x572",
        "photo": "1024x768"
    }

    # API endpoint
    API_ENDPOINT = "https://aiworldcreator.com/v1/images/generations"

    def __init__(self):
        """Initialize with proper session configuration"""
        self.session = requests.Session()

        # Set headers exactly as shown in API docs
        self.session.headers.update({
            "accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "MedusaXD-Bot/2.0"
        })

    def _create_payload(self, prompt: str, model: str, num_images: int, 
                       aspect_ratio: str, style: str, seed: int) -> dict:
        """Create API payload matching exact specification"""

        size = self.SIZE_MAPPING.get(aspect_ratio, "1024x1024")
        api_aspect_ratio = self.ASPECT_RATIOS.get(aspect_ratio, "1:1")

        # Create payload exactly matching API specification
        payload = {
            "prompt": prompt,
            "model": model,
            "n": num_images,
            "size": size,
            "response_format": "url",
            "user": "medusaxd-user",
            "style": style,
            "aspect_ratio": api_aspect_ratio,
            "timeout": 60,
            "image_format": "png",
            "seed": seed
        }

        return payload

    async def _make_api_request(self, payload: dict, timeout: int = 90) -> dict:
        """Make API request with comprehensive error handling"""

        try:
            logger.info(f"🔗 Making request to: {self.API_ENDPOINT}")
            logger.info(f"📦 Payload: {json.dumps(payload, indent=2)}")

            # Make synchronous request in thread
            response = await asyncio.to_thread(
                self._sync_request,
                payload,
                timeout
            )

            return response

        except Exception as e:
            logger.error(f"❌ API request failed: {e}")
            raise

    def _sync_request(self, payload: dict, timeout: int) -> dict:
        """Make synchronous request with detailed debugging"""

        try:
            # Make the POST request
            response = self.session.post(
                self.API_ENDPOINT,
                json=payload,
                timeout=timeout,
                verify=True  # Ensure SSL verification
            )

            # Log response details
            logger.info(f"📊 Response Status: {response.status_code}")
            logger.info(f"📋 Response Headers: {dict(response.headers)}")

            # Check if we got any content
            if not response.content:
                logger.error("❌ API returned empty response")
                raise RuntimeError("API returned empty response")

            # Log response content (first 500 chars for debugging)
            content_preview = response.text[:500] if response.text else "No content"
            logger.info(f"📄 Response Content (preview): {content_preview}")

            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            logger.info(f"📝 Content-Type: {content_type}")

            # Handle different response types
            if 'text/html' in content_type:
                logger.error("❌ API returned HTML instead of JSON")
                logger.error(f"HTML Response: {response.text[:1000]}")
                raise RuntimeError("API returned HTML error page instead of JSON")

            if 'application/json' not in content_type:
                logger.warning(f"⚠️ Unexpected content type: {content_type}")

            # Check HTTP status
            if response.status_code != 200:
                logger.error(f"❌ HTTP Error {response.status_code}")
                logger.error(f"Response body: {response.text}")

                if response.status_code == 400:
                    raise ValueError(f"Bad request (400): {response.text}")
                elif response.status_code == 401:
                    raise RuntimeError("Unauthorized (401): Check API credentials")
                elif response.status_code == 403:
                    raise RuntimeError("Forbidden (403): Access denied")
                elif response.status_code == 404:
                    raise RuntimeError("Not found (404): API endpoint not found")
                elif response.status_code == 429:
                    raise RuntimeError("Rate limited (429): Too many requests")
                elif response.status_code >= 500:
                    raise RuntimeError(f"Server error ({response.status_code}): API server issue")
                else:
                    raise RuntimeError(f"HTTP error {response.status_code}: {response.text}")

            # Try to parse JSON
            try:
                json_data = response.json()
                logger.info("✅ Successfully parsed JSON response")
                return json_data

            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON decode error: {e}")
                logger.error(f"Raw response text: '{response.text}'")

                # Check if response is actually empty
                if not response.text.strip():
                    raise RuntimeError("API returned empty response body")
                else:
                    raise RuntimeError(f"API returned invalid JSON: {str(e)}")

        except requests.exceptions.Timeout:
            logger.error("❌ Request timed out")
            raise RuntimeError("Request timed out - API may be slow or down")

        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            raise RuntimeError("Failed to connect to API - check internet connection")

        except requests.exceptions.SSLError as e:
            logger.error(f"❌ SSL error: {e}")
            raise RuntimeError("SSL certificate error - API security issue")

        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise

    async def generate_images(
        self,
        prompt: str,
        model: str = "turbo",
        num_images: int = 1,
        aspect_ratio: str = "landscape",
        seed: Optional[int] = None,
        timeout: int = 90,
        style: str = "realistic"
    ) -> ImageResponse:
        """Generate images with the fixed API implementation"""

        # Validate inputs
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model '{model}' not supported. Available: {self.AVAILABLE_MODELS}")

        if num_images < 1 or num_images > 4:
            raise ValueError("Number of images must be between 1 and 4")

        if aspect_ratio not in self.ASPECT_RATIOS:
            logger.warning(f"Unknown aspect ratio '{aspect_ratio}', using 'square'")
            aspect_ratio = "square"

        # Clean prompt
        prompt = prompt.strip()
        if len(prompt) < 2:
            raise ValueError("Prompt must be at least 2 characters")

        if len(prompt) > 500:
            prompt = prompt[:500]
            logger.warning("⚠️ Prompt truncated to 500 characters")

        # Generate seed if not provided
        if seed is None:
            seed = random.randint(1, 999999)

        # Create API payload
        payload = self._create_payload(prompt, model, num_images, aspect_ratio, style, seed)

        try:
            logger.info(f"🎨 Generating {num_images} image(s) with {model.upper()}")
            logger.info(f"📝 Prompt: {prompt}")
            logger.info(f"📐 Aspect: {aspect_ratio} | 🎨 Style: {style}")

            # Make API request
            result = await self._make_api_request(payload, timeout)

            # Validate response structure
            if not isinstance(result, dict):
                raise RuntimeError(f"API returned invalid response type: {type(result)}")

            if "data" not in result:
                logger.error(f"API response missing 'data' field: {result}")
                raise RuntimeError("API response missing 'data' field")

            if not isinstance(result["data"], list):
                raise RuntimeError("API response 'data' field is not a list")

            if not result["data"]:
                raise RuntimeError("API returned empty data array")

            # Process image data
            result_data = []
            for i, item in enumerate(result["data"]):
                if not isinstance(item, dict):
                    logger.warning(f"Invalid item {i} in response data")
                    continue

                if "url" not in item:
                    logger.warning(f"Item {i} missing 'url' field")
                    continue

                if not item["url"]:
                    logger.warning(f"Item {i} has empty URL")
                    continue

                result_data.append(ImageData(url=item["url"]))

            if not result_data:
                raise RuntimeError("No valid images in API response")

            logger.info(f"✅ Successfully generated {len(result_data)} image(s)")

            return ImageResponse(
                created=result.get("created", int(time.time())), 
                data=result_data
            )

        except Exception as e:
            logger.error(f"❌ Image generation failed: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test API connection with minimal request"""
        test_payload = {
            "prompt": "test",
            "model": "turbo",
            "n": 1,
            "size": "512x512",
            "response_format": "url", 
            "user": "test",
            "style": "realistic",
            "aspect_ratio": "1:1",
            "timeout": 30,
            "image_format": "png",
            "seed": 12345
        }

        try:
            logger.info("🧪 Testing API connection...")
            result = await self._make_api_request(test_payload, timeout=30)

            if result and "data" in result:
                logger.info("✅ API connection test successful")
                return True
            else:
                logger.warning("❌ API test failed - invalid response")
                return False

        except Exception as e:
            logger.error(f"❌ API connection test failed: {e}")
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
