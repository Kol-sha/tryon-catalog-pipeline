import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import rembg

from config import config

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """
    Prepares clothing images for the try-on pipeline:
    - Background removal
    - Resizing / padding
    - Enhancement
    - Mask generation
    """
    
    def __init__(self, target_size: Tuple[int, int] = config.IMAGE_SIZE):
        self.target_size = target_size   # (width, height)
        self._rembg_session = rembg.new_session("u2net_cloth_seg")
        
    def remove_background(self, image: Image.Image) -> Image.Image:
        """Returns RGBA image with background removed."""
        img_bytes = self._pil_to_bytes(image)
        result_bytes = rembg.remove(img_bytes, session=self._rembg_session)
        return Image.open(__import__("io").BytesIO(result_bytes)).convert("RGBA")

    def generate_clothing_mask(self, image_rgba: Image.Image) -> Image.Image:
        """
        Binary mask (L mode) where white = clothing pixels.
        Uses the alpha channel from background-removed image.
        """
        alpha = np.array(image_rgba.split()[-1])          # (H, W)
        mask = (alpha > 10).astype(np.uint8) * 255
        
        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)
        
        return Image.fromarray(mask, mode="L")

    def resize_with_padding(
        self,
        image: Image.Image,
        background_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> Image.Image:
        """Resize keeping aspect ratio and pad to target_size."""
        w_target, h_target = self.target_size
        w_orig, h_orig = image.size
        
        scale = min(w_target / w_orig, h_target / h_orig)
        new_w = int(w_orig * scale)
        new_h = int(h_orig * scale)
        
        resized = image.resize((new_w, new_h), Image.LANCZOS)
        
        # Paste onto white canvas
        canvas = Image.new("RGB", (w_target, h_target), background_color)
        offset_x = (w_target - new_w) // 2
        offset_y = (h_target - new_h) // 2
        
        if resized.mode == "RGBA":
            canvas.paste(resized, (offset_x, offset_y), resized.split()[-1])
        else:
            canvas.paste(resized, (offset_x, offset_y))
        
        return canvas
    
    def enhance_image(self, image: Image.Image) -> Image.Image:
        """Sharpen + slight contrast boost."""
        image = ImageEnhance.Contrast(image).enhance(1.1)
        image = ImageEnhance.Sharpness(image).enhance(1.2)
        return image

    def process(
        self, image: Image.Image
    ) -> Tuple[Image.Image, Image.Image, Image.Image]:
        """
        Returns:
            clothing_clean  – background-removed on white canvas (RGB)
            clothing_rgba   – RGBA with transparent background
            mask            – binary clothing mask (L)
        """
        # 1. Remove background
        rgba = self.remove_background(image)
        
        # 2. Generate mask
        mask = self.generate_clothing_mask(rgba)
        
        # 3. Compose on white background & resize
        clothing_clean = self.resize_with_padding(rgba)
        clothing_clean = self.enhance_image(clothing_clean)
        
        # 4. Resize mask to same size
        mask = mask.resize(self.target_size[::-1], Image.NEAREST)
        
        # 5. Keep RGBA version resized
        rgba_resized = rgba.resize(self.target_size, Image.LANCZOS)
        
        return clothing_clean, rgba_resized, mask

    @staticmethod
    def _pil_to_bytes(image: Image.Image) -> bytes:
        import io
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()