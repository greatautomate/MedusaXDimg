"""
MedusaXD Image Generator - AIWorldCreator Provider
Enhanced image generation provider for MedusaXD Bot using aiworldcreator.com API
"""

import requests
import asyncio
import random
import time
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
    High-quality AI image generation with multiple models
    """

    # Updated models based on API documentation
    AVAILABLE_MODELS = ["flux", "turbo", "gptimage"]

    ASPECT_RATIOS = {
        "landscape": "16:9",
        "portrait": "9:16", 
        "square": "1:1"
    }

    SIZE_MAPPING = {
        "landscape": "1344x768",
        "portrait": "768x1344",
        "square": "1024x1024"
    }

    # Main API endpoint
    API_ENDPOINT = "https://aiworldcreator.com/v1/images/generations"

    def __init__(self):
        """Initialize the MedusaXD Image Generator"""
        self.session = requests.Session()

        # User agents for better compatibility
        self.user_agents = [
            "MedusaXD-Bot/2.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "AIWorldCreator-Client/1.0"
        ]

    def _get_headers(self):
        """Get request headers"""
        return {
            "accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": random.choice(self.user_agents)
        }

    async def _make_request_with_retry(self, payload: dict, max_retries: int = 3) -> dict:
        """Make API request with retry logic"""

        for attempt in range(max_retries):
            try:
                logger.info(f"🎨 Attempt {attempt + 1}/{max_retries} - Generating image...")

                # Add delay between retries
                if attempt > 0:
                    delay = random.uniform(2, 5)
                    logger.info(f"⏳ Waiting {delay:.1f}s before retry...")
                    await asyncio.sleep(delay)

                # Make the request
                response = await asyncio.to_thread(
                    self._sync_request, 
                    payload, 
                    timeout=60
                )

                if response and "data" in response and response["data"]:
                    logger.info(f"✅ Successfully generated image on attempt {attempt + 1}")
                    return response
                else:
                    logger.warning(f"⚠️ Empty response on attempt {attempt + 1}")

            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Timeout on attempt {attempt + 1}")
                continue

            except requests.exceptions.ConnectionError:
                logger.warning(f"🔌 Connection error on attempt {attempt + 1}")
                continue

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400:
                    # Bad request - likely invalid parameters
                    try:
                        error_data = e.response.json()
                        if "error" in error_data:
                            error_msg = error_data["error"].get("message", "Invalid request")
                            raise ValueError(f"API Error: {error_msg}")
                    except:
                        raise ValueError("Invalid request parameters")
                elif e.response.status_code == 429:
                    logger.warning(f"⏱️ Rate limited on attempt {attempt + 1}")
                    await asyncio.sleep(30)
                    continue
                elif e.response.status_code == 500:
                    logger.warning(f"🔥 Server error on attempt {attempt + 1}")
                    continue
                else:
                    logger.error(f"❌ HTTP error {e.response.status_code} on attempt {attempt + 1}")
                    continue

            except Exception as e:
                logger.error(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                continue

            # Wait between retry cycles
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                logger.info(f"😴 Waiting {wait_time}s before next retry...")
                await asyncio.sleep(wait_time)

        raise RuntimeError("Failed to generate image after maximum retries")

    def _sync_request(self, payload: dict, timeout: int) -> dict:
        """Make synchronous request"""
        headers = self._get_headers()

        response = self.session.post(
            self.API_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()

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
        """Generate images using AIWorldCreator API"""

        # Validate parameters
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model '{model}' not supported. Available models: {self.AVAILABLE_MODELS}")

        if num_images < 1 or num_images > 4:
            raise ValueError("Number of images must be between 1 and 4")

        if aspect_ratio not in self.ASPECT_RATIOS:
            aspect_ratio = "landscape"

        # Clean and validate prompt
        prompt = prompt.strip()
        if len(prompt) < 3:
            raise ValueError("Prompt must be at least 3 characters long")

        if len(prompt) > 1000:
            prompt = prompt[:1000]
            logger.warning("⚠️ Prompt truncated to 1000 characters")

        # Map aspect ratio to size
        size = self.SIZE_MAPPING[aspect_ratio]
        api_aspect_ratio = self.ASPECT_RATIOS[aspect_ratio]

        # Prepare request payload
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
            "seed": seed if seed is not None else random.randint(1, 1000000)
        }

        try:
            logger.info(f"🎨 Generating {num_images} image(s) with model '{model}'")
            logger.info(f"📝 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

            # Make request with retry logic
            result = await self._make_request_with_retry(payload, max_retries=3)

            # Process response
            result_data = []
            for item in result["data"]:
                result_data.append(ImageData(url=item["url"]))

            logger.info(f"✅ Successfully generated {len(result_data)} image(s)")
            return ImageResponse(created=result.get("created", int(time.time())), data=result_data)

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"❌ Image generation failed: {e}")
            raise RuntimeError(f"Failed to generate image: {e}")

    def get_models(self) -> List[str]:
        """Get available models"""
        return self.AVAILABLE_MODELS.copy()

    def get_aspect_ratios(self) -> List[str]:
        """Get available aspect ratios"""
        return list(self.ASPECT_RATIOS.keys())

    async def test_connection(self) -> bool:
        """Test if the API endpoint is working"""
        test_payload = {
            "prompt": "test image",
            "model": "turbo",
            "n": 1,
            "size": "1024x1024",
            "response_format": "url",
            "user": "test-user",
            "style": "realistic",
            "aspect_ratio": "1:1",
            "timeout": 30,
            "image_format": "png",
            "seed": 12345
        }

        try:
            logger.info(f"🧪 Testing API endpoint: {self.API_ENDPOINT}")
            response = await asyncio.to_thread(
                self._sync_request, 
                test_payload, 
                timeout=30
            )
            if response and "data" in response and response["data"]:
                logger.info("✅ API endpoint is working")
                return True
            else:
                logger.warning("❌ API test failed - empty response")
                return False
        except Exception as e:
            logger.error(f"❌ API test failed: {e}")
            return False

    def get_model_info(self) -> dict:
        """Get information about available models"""
        return {
            "flux": {
                "name": "Flux",
                "description": "High-quality, detailed image generation",
                "best_for": "Professional artwork, detailed scenes"
            },
            "turbo": {
                "name": "Turbo",
                "description": "Fast generation with good quality",
                "best_for": "Quick prototypes, general use"
            },
            "gptimage": {
                "name": "GPT Image",
                "description": "Advanced AI model for creative images",
                "best_for": "Creative artwork, concept art"
            }
        }
