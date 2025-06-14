"""
MedusaXD Image Generator - AIWorldCreator Provider
Enhanced image generation provider for MedusaXD Bot using aiworldcreator.com API
Supports advanced command-line options and multiple aspect ratios
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
    High-quality AI image generation with multiple models and advanced options
    """

    # Updated models based on API documentation
    AVAILABLE_MODELS = ["flux", "turbo", "gptimage"]

    # Extended aspect ratios for advanced CLI
    ASPECT_RATIOS = {
        # Standard ratios
        "landscape": "16:9",
        "portrait": "9:16", 
        "square": "1:1",

        # Photography ratios
        "photo": "4:3",
        "classic": "3:2",
        "wide": "21:9",

        # Creative ratios
        "golden": "1.618:1",
        "cinema": "2.35:1",
        "poster": "3:4",

        # Social media ratios
        "instagram": "1:1",
        "story": "9:16",
        "cover": "16:9",
        "twitter": "16:9",

        # Print ratios
        "a4": "297:210",
        "letter": "11:8.5",

        # Special ratios
        "imax": "1.43:1",
        "ultrawide": "32:9"
    }

    # Size mapping for each aspect ratio (optimized for quality)
    SIZE_MAPPING = {
        # Standard ratios
        "landscape": "1344x768",
        "portrait": "768x1344",
        "square": "1024x1024",

        # Photography ratios
        "photo": "1024x768",
        "classic": "1024x683",
        "wide": "1344x576",

        # Creative ratios
        "golden": "1024x633",
        "cinema": "1344x572",
        "poster": "768x1024",

        # Social media ratios
        "instagram": "1024x1024",
        "story": "768x1344",
        "cover": "1344x768",
        "twitter": "1344x768",

        # Print ratios
        "a4": "1024x727",
        "letter": "1024x791",

        # Special ratios
        "imax": "1024x716",
        "ultrawide": "1344x384"
    }

    # Style mappings for the API
    STYLE_MAPPING = {
        "realistic": "realistic",
        "photographic": "photographic",
        "artistic": "artistic",
        "anime": "anime",
        "cartoon": "cartoon",
        "cinematic": "cinematic",
        "fantasy": "fantasy",
        "cyberpunk": "cyberpunk",
        "oil_painting": "oil painting",
        "watercolor": "watercolor",
        "sketch": "sketch",
        "digital_art": "digital art"
    }

    # Main API endpoint
    API_ENDPOINT = "https://aiworldcreator.com/v1/images/generations"

    def __init__(self):
        """Initialize the MedusaXD Image Generator"""
        self.session = requests.Session()

        # User agents for better compatibility
        self.user_agents = [
            "MedusaXD-Bot/2.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "AIWorldCreator-Client/1.0"
        ]

    def _get_headers(self):
        """Get request headers with rotation"""
        return {
            "accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": random.choice(self.user_agents),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache"
        }

    async def _make_request_with_retry(self, payload: dict, max_retries: int = 3) -> dict:
        """Make API request with comprehensive retry logic"""

        for attempt in range(max_retries):
            try:
                logger.info(f"🎨 Attempt {attempt + 1}/{max_retries} - Generating image with {payload.get('model', 'unknown')} model")

                # Progressive delay between retries
                if attempt > 0:
                    delay = min(2 ** attempt + random.uniform(0, 1), 10)  # Exponential backoff with jitter
                    logger.info(f"⏳ Waiting {delay:.1f}s before retry...")
                    await asyncio.sleep(delay)

                # Make the request
                response = await asyncio.to_thread(
                    self._sync_request, 
                    payload, 
                    timeout=90  # Increased timeout for complex generations
                )

                if response and "data" in response and response["data"]:
                    logger.info(f"✅ Successfully generated {len(response['data'])} image(s) on attempt {attempt + 1}")
                    return response
                else:
                    logger.warning(f"⚠️ Empty or invalid response on attempt {attempt + 1}")
                    if attempt == max_retries - 1:
                        raise RuntimeError("API returned empty response")
                    continue

            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Request timeout on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    raise RuntimeError("Request timed out after maximum retries")
                continue

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"🔌 Connection error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise RuntimeError("Failed to connect to image generation service")
                continue

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 0

                if status_code == 400:
                    # Bad request - likely invalid parameters
                    try:
                        error_data = e.response.json()
                        if "error" in error_data:
                            error_msg = error_data["error"].get("message", "Invalid request parameters")
                            raise ValueError(f"API Error: {error_msg}")
                    except (ValueError, KeyError):
                        raise ValueError("Invalid request parameters - check your prompt and options")

                elif status_code == 401:
                    raise RuntimeError("API authentication failed")

                elif status_code == 403:
                    raise RuntimeError("API access forbidden - check permissions")

                elif status_code == 429:
                    logger.warning(f"⏱️ Rate limited on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(30 + random.uniform(0, 10))  # Wait longer for rate limits
                        continue
                    else:
                        raise RuntimeError("Rate limit exceeded - please try again later")

                elif status_code >= 500:
                    logger.warning(f"🔥 Server error ({status_code}) on attempt {attempt + 1}")
                    if attempt == max_retries - 1:
                        raise RuntimeError(f"Server error ({status_code}) - service temporarily unavailable")
                    continue
                else:
                    logger.error(f"❌ HTTP error {status_code} on attempt {attempt + 1}")
                    raise RuntimeError(f"HTTP error {status_code}")

            except Exception as e:
                logger.error(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Unexpected error: {str(e)}")
                continue

        raise RuntimeError("Failed to generate image after maximum retries")

    def _sync_request(self, payload: dict, timeout: int) -> dict:
        """Make synchronous request (called from asyncio.to_thread)"""
        headers = self._get_headers()

        logger.debug(f"Making request to {self.API_ENDPOINT} with payload: {payload}")

        response = self.session.post(
            self.API_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=timeout
        )

        logger.debug(f"Response status: {response.status_code}")
        response.raise_for_status()

        return response.json()

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
        """
        Generate images using AIWorldCreator API with enhanced parameters

        Args:
            prompt: Text description of the image to generate
            model: The model to use ("flux", "turbo", or "gptimage")
            num_images: Number of images to generate (1-4)
            aspect_ratio: Image aspect ratio (see ASPECT_RATIOS for options)
            seed: Random seed for reproducibility (optional)
            timeout: Request timeout in seconds
            style: Image style (see STYLE_MAPPING for options)

        Returns:
            ImageResponse: The generated images

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If image generation fails
        """
        # Validate parameters
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model '{model}' not supported. Available models: {self.AVAILABLE_MODELS}")

        if num_images < 1 or num_images > 4:
            raise ValueError("Number of images must be between 1 and 4")

        if aspect_ratio not in self.ASPECT_RATIOS:
            logger.warning(f"Unknown aspect ratio '{aspect_ratio}', defaulting to 'landscape'")
            aspect_ratio = "landscape"

        # Clean and validate prompt
        prompt = prompt.strip()
        if len(prompt) < 3:
            raise ValueError("Prompt must be at least 3 characters long")

        if len(prompt) > 2000:
            prompt = prompt[:2000]
            logger.warning("⚠️ Prompt truncated to 2000 characters")

        # Map aspect ratio to size and API format
        size = self.SIZE_MAPPING.get(aspect_ratio, "1344x768")
        api_aspect_ratio = self.ASPECT_RATIOS[aspect_ratio]

        # Map style to API format
        api_style = self.STYLE_MAPPING.get(style, "realistic")

        # Generate seed if not provided
        if seed is None:
            seed = random.randint(1, 2147483647)  # Max int32

        # Prepare request payload matching the API structure
        payload = {
            "prompt": prompt,
            "model": model,
            "n": num_images,
            "size": size,
            "response_format": "url",
            "user": "medusaxd-bot",
            "style": api_style,
            "aspect_ratio": api_aspect_ratio,
            "timeout": timeout,
            "image_format": "png",
            "seed": seed
        }

        try:
            logger.info(f"🎨 Generating {num_images} image(s) with model '{model.upper()}'")
            logger.info(f"📝 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            logger.info(f"📐 Size: {size} ({aspect_ratio}) | 🎨 Style: {api_style}")
            logger.info(f"🌱 Seed: {seed}")

            # Make request with retry logic
            result = await self._make_request_with_retry(payload, max_retries=3)

            # Process response - matches the API response format
            result_data = []
            for item in result["data"]:
                if "url" in item and item["url"]:
                    result_data.append(ImageData(url=item["url"]))
                else:
                    logger.warning("⚠️ Invalid image data in response")

            if not result_data:
                raise RuntimeError("No valid images in API response")

            logger.info(f"✅ Successfully generated {len(result_data)} image(s)")
            return ImageResponse(created=result.get("created", int(time.time())), data=result_data)

        except ValueError as e:
            # Re-raise validation errors
            logger.error(f"❌ Validation error: {e}")
            raise e
        except RuntimeError as e:
            # Re-raise runtime errors
            logger.error(f"❌ Runtime error: {e}")
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

    def get_styles(self) -> List[str]:
        """Get available styles"""
        return list(self.STYLE_MAPPING.keys())

    async def test_connection(self) -> bool:
        """Test if the API endpoint is working"""
        test_payload = {
            "prompt": "test image generation",
            "model": "turbo",
            "n": 1,
            "size": "1024x1024",
            "response_format": "url",
            "user": "medusaxd-test",
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
                logger.info("✅ API endpoint is working properly")
                return True
            else:
                logger.warning("❌ API test failed - empty or invalid response")
                return False
        except Exception as e:
            logger.error(f"❌ API test failed: {e}")
            return False

    def get_model_info(self) -> dict:
        """Get detailed information about available models"""
        return {
            "flux": {
                "name": "Flux",
                "description": "High-quality, detailed image generation with superior realism",
                "best_for": "Professional artwork, detailed scenes, photorealistic images",
                "speed": "Slow",
                "quality": "Excellent"
            },
            "turbo": {
                "name": "Turbo",
                "description": "Fast generation with good quality balance",
                "best_for": "Quick prototypes, general use, social media content",
                "speed": "Fast",
                "quality": "Good"
            },
            "gptimage": {
                "name": "GPT Image",
                "description": "Advanced AI model for creative and conceptual images",
                "best_for": "Creative artwork, concept art, abstract designs",
                "speed": "Medium",
                "quality": "Very Good"
            }
        }

    def get_aspect_ratio_info(self) -> dict:
        """Get detailed information about available aspect ratios"""
        return {
            "Standard": {
                "landscape": {"ratio": "16:9", "size": "1344x768", "best_for": "Wallpapers, presentations, general use"},
                "portrait": {"ratio": "9:16", "size": "768x1344", "best_for": "Phone wallpapers, vertical displays"},
                "square": {"ratio": "1:1", "size": "1024x1024", "best_for": "Social media posts, avatars, thumbnails"}
            },
            "Photography": {
                "photo": {"ratio": "4:3", "size": "1024x768", "best_for": "Traditional photography, camera-like shots"},
                "classic": {"ratio": "3:2", "size": "1024x683", "best_for": "Film photography style, professional photos"},
                "wide": {"ratio": "21:9", "size": "1344x576", "best_for": "Panoramic shots, ultra-wide scenes"}
            },
            "Creative": {
                "golden": {"ratio": "1.618:1", "size": "1024x633", "best_for": "Artistic compositions, balanced designs"},
                "cinema": {"ratio": "2.35:1", "size": "1344x572", "best_for": "Cinematic scenes, movie-style shots"},
                "poster": {"ratio": "3:4", "size": "768x1024", "best_for": "Movie posters, vertical artwork"}
            },
            "Social Media": {
                "instagram": {"ratio": "1:1", "size": "1024x1024", "best_for": "Instagram posts, square content"},
                "story": {"ratio": "9:16", "size": "768x1344", "best_for": "Instagram/Facebook stories"},
                "cover": {"ratio": "16:9", "size": "1344x768", "best_for": "Facebook covers, YouTube banners"}
            }
        }

    def get_usage_stats(self) -> dict:
        """Get usage statistics for the generator"""
        return {
            "total_models": len(self.AVAILABLE_MODELS),
            "total_aspect_ratios": len(self.ASPECT_RATIOS),
            "total_styles": len(self.STYLE_MAPPING),
            "api_endpoint": self.API_ENDPOINT,
            "max_images_per_request": 4,
            "max_prompt_length": 2000,
            "supported_formats": ["png", "jpg"],
            "timeout_seconds": 90
        }
