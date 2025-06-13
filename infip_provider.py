"""
MedusaXD Image Generator - InfipAI Provider
Rebranded image generation provider for MedusaXD Bot
"""

import requests
from typing import Optional, List
import time
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
    MedusaXD Image Generator using InfipAI API
    Generates high-quality AI images from text prompts
    """

    AVAILABLE_MODELS = ["img3", "img4", "uncen"]
    ASPECT_RATIOS = {
        "landscape": "IMAGE_ASPECT_RATIO_LANDSCAPE",
        "portrait": "IMAGE_ASPECT_RATIO_PORTRAIT", 
        "square": "IMAGE_ASPECT_RATIO_SQUARE"
    }

    def __init__(self):
        """Initialize the MedusaXD Image Generator"""
        self.api_endpoint = "https://api.infip.pro/generate"
        self.session = requests.Session()

        # Set up headers
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "MedusaXD-Bot/1.0"
        }
        self.session.headers.update(self.headers)

    async def generate_images(
        self,
        prompt: str,
        model: str = "img3",
        num_images: int = 1,
        aspect_ratio: str = "landscape",
        seed: Optional[int] = None,
        timeout: int = 60
    ) -> ImageResponse:
        """
        Generate images using MedusaXD AI

        Args:
            prompt: Text description of the image to generate
            model: The model to use ("img3", "img4", or "uncen")
            num_images: Number of images to generate (1-4)
            aspect_ratio: Image aspect ratio ("landscape", "portrait", "square")
            seed: Random seed for reproducibility (optional)
            timeout: Request timeout in seconds

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
            aspect_ratio = "landscape"

        # Map aspect ratio
        api_aspect_ratio = self.ASPECT_RATIOS[aspect_ratio]

        # Prepare request payload
        payload = {
            "prompt": prompt,
            "num_images": num_images,
            "seed": seed if seed is not None else 0,
            "aspect_ratio": api_aspect_ratio,
            "models": model
        }

        try:
            logger.info(f"🎨 Generating {num_images} image(s) with model {model}")

            # Make API request
            response = self.session.post(
                self.api_endpoint,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()

            # Parse response
            result = response.json()

            if "images" not in result or not result["images"]:
                raise RuntimeError("No images returned from MedusaXD AI API")

            # Process response
            result_data = []
            for image_url in result["images"]:
                result_data.append(ImageData(url=image_url))

            logger.info(f"✅ Successfully generated {len(result_data)} image(s)")
            return ImageResponse(created=int(time.time()), data=result_data)

        except requests.RequestException as e:
            logger.error(f"❌ API request failed: {e}")
            raise RuntimeError(f"Failed to generate image: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise RuntimeError(f"Unexpected error during image generation: {e}")

    def get_models(self) -> List[str]:
        """Get available models"""
        return self.AVAILABLE_MODELS.copy()

    def get_aspect_ratios(self) -> List[str]:
        """Get available aspect ratios"""
        return list(self.ASPECT_RATIOS.keys())
