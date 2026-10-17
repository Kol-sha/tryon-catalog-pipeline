import base64
import io
import json
import logging
import ssl
import time
import urllib.request
from typing import Optional

import numpy as np
from PIL import Image

from config import config

logger = logging.getLogger(__name__)


def _make_ssl_context() -> ssl.SSLContext:
    """Permissive SSL context to avoid macOS certificate errors."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    return ctx


def _image_to_base64_jpeg(image: Image.Image, quality: int = 85) -> str:
    """
    Convert PIL image to base64 JPEG data URI.
    JPEG is much smaller than PNG, bypassing network timeouts.
    """
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=quality)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def _http_post(url: str, payload: dict, token: str, timeout: int = 120) -> dict:
    """Raw HTTPS POST using urllib (bypasses httpx timeout bugs)."""
    body    = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "User-Agent":    "python-urllib/3.13",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, context=_make_ssl_context(), timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get(url: str, token: str, timeout: int = 60) -> dict:
    """Raw HTTPS GET using urllib."""
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent":    "python-urllib/3.13",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, context=_make_ssl_context(), timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download_image(url: str, timeout: int = 60) -> Image.Image:
    """Download image from URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "python-urllib/3.13"})
    with urllib.request.urlopen(req, context=_make_ssl_context(), timeout=timeout) as resp:
        return Image.open(io.BytesIO(resp.read())).convert("RGB")


class TryOnPipeline:
    """
    Virtual try-on using Replicate IDM-VTON API via Raw REST.
    No local GPU or third-party SDK required.
    """

    MODEL_VERSION = "c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4"
    PREDICT_URL   = "https://api.replicate.com/v1/predictions"

    def __init__(self, device: Optional[str] = None):
        self.device = device or config.DEVICE
        self._token = self._get_token()

    def _get_token(self) -> str:
        import os
        token = config.REPLICATE_TOKEN or os.environ.get("REPLICATE_API_TOKEN", "")
        if not token:
            raise ValueError("REPLICATE_API_TOKEN is missing!")
        return token

    # ---------------------------------------------------------------- #
    #  Main try-on                                                      #
    # ---------------------------------------------------------------- #

    def try_on(
        self,
        model_image:    Image.Image,
        clothing_image: Image.Image,
        clothing_mask:  Image.Image,
        gender:         str,
        angle:          str,
        seed:           Optional[int] = None,
    ) -> Image.Image:

        logger.info("Calling Replicate IDM-VTON API (REST) ...")
        
        color = self._dominant_color(clothing_image)
        style = self._clothing_style(clothing_image)
        desc  = f"{color} {style}"
        logger.info(f"Clothing desc: '{desc}'")

        # 1. Convert to Base64 (JPEG to avoid upload timeouts)
        logger.info("Encoding images...")
        model_b64 = _image_to_base64_jpeg(model_image)
        cloth_b64 = _image_to_base64_jpeg(clothing_image)

        # 2. Submit to API
        payload = {
            "version": self.MODEL_VERSION,
            "input": {
                "human_img":       model_b64,
                "garm_img":        cloth_b64,
                "garment_des":     desc,
                "is_checked":      True,
                "is_checked_crop": True,
                "denoise_steps":   30,
                "seed":            seed or config.SEED,
                "category":        self._garment_category(style),
            }
        }

        logger.info("Submitting prediction to Replicate ...")
        try:
            resp = _http_post(self.PREDICT_URL, payload, self._token)
        except Exception as e:
            raise RuntimeError(f"Replicate API submission failed: {e}")

        pred_id  = resp.get("id")
        poll_url = resp.get("urls", {}).get("get", f"{self.PREDICT_URL}/{pred_id}")
        logger.info(f"Prediction started (ID: {pred_id})")

        # 3. Poll for completion
        result_url = self._poll_until_success(poll_url)

        # 4. Download result
        logger.info("Downloading final image...")
        output = _download_image(result_url)
        return output.resize(config.IMAGE_SIZE, Image.LANCZOS)

    # ---------------------------------------------------------------- #
    #  Polling                                                          #
    # ---------------------------------------------------------------- #

    def _poll_until_success(self, poll_url: str, timeout_sec: int = 300) -> str:
        start_time = time.time()
        attempt = 0

        while time.time() - start_time < timeout_sec:
            attempt += 1
            data = _http_get(poll_url, self._token)
            status = data.get("status", "unknown")
            
            if status == "succeeded":
                out = data.get("output")
                if isinstance(out, list): out = out[0]
                logger.info(f"✓ API Success in {int(time.time() - start_time)}s")
                return out
                
            elif status == "failed":
                err = data.get("error", "Unknown error")
                raise RuntimeError(f"Replicate API failed: {err}")
                
            elif status == "canceled":
                raise RuntimeError("Prediction canceled.")

            logger.info(f"  [{attempt:02d}] Status: {status}...")
            time.sleep(5.0)

        raise TimeoutError("Prediction timed out.")

    # ---------------------------------------------------------------- #
    #  Clothing analysis                                                #
    # ---------------------------------------------------------------- #

    def _dominant_color(self, image: Image.Image) -> str:
        arr    = np.array(image.resize((50, 50)).convert("RGB"))
        not_bg = ~((arr[:,:,0] > 220) & (arr[:,:,1] > 220) & (arr[:,:,2] > 220))
        pixels = arr[not_bg]
        if len(pixels) < 10: return "dark"
        r, g, b = pixels.mean(axis=0).astype(int)
        
        brightness = r + g + b
        if brightness < 150: return "black"
        if brightness > 650: return "white"
        if abs(r-g) < 25 and abs(g-b) < 25: return "gray"
        if r > g and r > b:  return "red"
        if g > r and g > b:  return "green"
        if b > r and b > g:  return "blue"
        return "dark"

    def _clothing_style(self, image: Image.Image) -> str:
        arr    = np.array(image.convert("L"))
        ys, xs = np.where(arr < 225)
        if len(ys) < 10: return "shirt"
        ratio = (ys.max() - ys.min()) / (xs.max() - xs.min() + 1e-6)
        if ratio > 2.0: return "long dress"
        if ratio > 1.5: return "long sleeve shirt"
        if ratio > 0.9: return "shirt"
        return "jacket"

    def _garment_category(self, style: str) -> str:
        if "dress" in style: return "dresses"
        if any(w in style for w in ["trouser","pant","skirt"]): return "lower_body"
        return "upper_body"

    def unload(self) -> None:
        pass