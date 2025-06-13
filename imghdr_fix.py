"""
Fix for Python 3.13 compatibility with python-telegram-bot
The imghdr module was removed in Python 3.13 but telegram library still needs it
"""

import sys
from PIL import Image
import io

class ImgHdr:
    """Minimal imghdr replacement using Pillow"""

    @staticmethod
    def what(file_path_or_bytes, h=None):
        """Detect image format"""
        try:
            if isinstance(file_path_or_bytes, (str, bytes)):
                if isinstance(file_path_or_bytes, str):
                    # File path
                    with open(file_path_or_bytes, 'rb') as f:
                        image = Image.open(f)
                        return image.format.lower() if image.format else None
                else:
                    # Bytes
                    image = Image.open(io.BytesIO(file_path_or_bytes))
                    return image.format.lower() if image.format else None
            else:
                # File-like object
                image = Image.open(file_path_or_bytes)
                return image.format.lower() if image.format else None
        except Exception:
            return None

# Create the missing imghdr module
sys.modules['imghdr'] = ImgHdr()
