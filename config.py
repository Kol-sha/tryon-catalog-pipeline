# config.py

import os
from dataclasses import dataclass, field
from typing import Dict, Tuple, List


@dataclass
class Config:
    # ── Paths ────────────────────────────────────────────────────────
    INPUT_FOLDER:  str = "Предметные фото"
    EXCEL_FILE:    str = "articles.xlsx"
    OUTPUT_FOLDER: str = "output"

    # ── Image settings ───────────────────────────────────────────────
    IMAGE_SIZE: Tuple[int, int] = (1024, 1024)
    SUPPORTED_FORMATS: Tuple[str, ...] = (".jpg", ".jpeg", ".png", ".webp")

    # ── Angle mapping ────────────────────────────────────────────────
    ANGLE_MAP: Dict[int, str] = field(default_factory=lambda: {
        1: "front",
        2: "side_profile",
        3: "back",
    })

    # Device
    DEVICE: str = "cpu"

    # ── GPTunnel API ─────────────────────────────────────────────────
    GPTUNNEL_API_KEY: str = field(
        default_factory=lambda: os.environ.get("GPTUNNEL_API_KEY", "")
    )
    GPTUNNEL_BASE_URL: str = "https://gptunnel.ru/v1"
    NANO_BANANA_MODEL: str = "nano-banana-2-gemini"

    # Replicate
    REPLICATE_TOKEN: str = field(
        default_factory=lambda: os.environ.get("REPLICATE_API_TOKEN", "")
    )

    # ── Generation params ────────────────────────────────────────────
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 5.0
    TIMEOUT_SEC: int = 180

    # ── Prompts per gender + angle ───────────────────────────────────
    MODEL_PROMPTS: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        "female": {
            "front": (
                "Generate a photorealistic full-body fashion photo. "
                "A European woman, around 25 years old, with neutral facial expression, "
                "natural makeup, slim athletic build, standing straight and facing the camera directly. "
                "She is wearing the exact garment shown in the input image — preserve its color, "
                "texture, pattern, length, and silhouette PERFECTLY. "
                "The garment should fit naturally on her body with realistic fabric folds. "
                "Studio setting with pure white seamless background, soft professional lighting. "
                "Sharp focus, 8K resolution, high-end e-commerce fashion photography style. "
                "The model's pose: arms relaxed at sides, weight evenly distributed, head straight. "
                "Show the entire body from head to feet."
            ),
            "side_profile": (
                "Generate a photorealistic full-body fashion photo. "
                "A European woman, around 25 years old, with neutral facial expression, "
                "natural makeup, slim athletic build, standing in a side profile pose (90 degrees from camera). "
                "She is wearing the exact garment shown in the input image — preserve its color, "
                "texture, pattern, length, and silhouette PERFECTLY. "
                "Studio setting with pure white seamless background, soft professional lighting. "
                "Sharp focus, 8K resolution, e-commerce fashion photography style. "
                "Show the entire body from head to feet, side view."
            ),
            "back": (
                "Generate a photorealistic full-body fashion photo. "
                "A European woman, around 25 years old, slim athletic build, "
                "standing straight with her back to the camera. "
                "She is wearing the exact garment shown in the input image — preserve its color, "
                "texture, pattern, length, and silhouette PERFECTLY, including the back design. "
                "Studio setting with pure white seamless background, soft professional lighting. "
                "Sharp focus, 8K resolution, e-commerce fashion photography style. "
                "Show the entire body from head to feet, back view."
            ),
        },
        "male": {
            "front": (
                "Generate a photorealistic full-body fashion photo. "
                "A European man, around 27 years old, with neutral facial expression, "
                "athletic build, short well-groomed hair, standing straight and facing the camera directly. "
                "He is wearing the exact garment shown in the input image — preserve its color, "
                "texture, pattern, length, and silhouette PERFECTLY. "
                "The garment should fit naturally on his body with realistic fabric folds. "
                "Studio setting with pure white seamless background, soft professional lighting. "
                "Sharp focus, 8K resolution, high-end e-commerce fashion photography style. "
                "The model's pose: arms relaxed at sides, weight evenly distributed, head straight. "
                "Show the entire body from head to feet."
            ),
            "side_profile": (
                "Generate a photorealistic full-body fashion photo. "
                "A European man, around 27 years old, athletic build, "
                "standing in a side profile pose (90 degrees from camera). "
                "He is wearing the exact garment shown in the input image — preserve its color, "
                "texture, pattern, length, and silhouette PERFECTLY. "
                "Studio setting with pure white seamless background, soft professional lighting. "
                "Sharp focus, 8K resolution, e-commerce fashion photography style. "
                "Show the entire body from head to feet, side view."
            ),
            "back": (
                "Generate a photorealistic full-body fashion photo. "
                "A European man, around 27 years old, athletic build, "
                "standing straight with his back to the camera. "
                "He is wearing the exact garment shown in the input image — preserve its color, "
                "texture, pattern, length, and silhouette PERFECTLY, including the back design. "
                "Studio setting with pure white seamless background, soft professional lighting. "
                "Sharp focus, 8K resolution, e-commerce fashion photography style. "
                "Show the entire body from head to feet, back view."
            ),
        },
    })

    NEGATIVE_PROMPT: str = "bad quality, blurry, distorted, deformed, ugly, low resolution, watermark, text, logo, extra limbs, missing limbs, bad anatomy, bad proportions"

    # ── Generation params ────────────────────────────────────────────
    API_STEPS: int = 40
    API_CFG_SCALE: float = 7.5
    SEED: int = 42
    API_SAMPLER: str = "DPM++ 2M Karras"

    # ── Excel columns ────────────────────────────────────────────────
    ARTICLE_COL:    str = "ARTICLE"
    GENDER_COL:     str = "GENDER"
    VALID_GENDERS:  Tuple[str, ...] = ("male", "female")

    # ── Стандарт Lamoda ──────────────────────────────────────────────
    OUTPUT_SIZE: Tuple[int, int] = (1524, 2200)  # цел таргет
    OUTPUT_FORMAT: str = "webp"
    OUTPUT_QUALITY: int = 95
    COLOR_PROFILE: str = "sRGB"
    OUTPUT_DPI: int = 300
    OUTPUT_DPI_MACRO: int = 300  # Для макро-деталей тоже 300 DPI
    
    # Базовые промпты по категориям
    BASE_PROMPTS: Dict[str, str] = field(default_factory=lambda: {
        "t-shirt": (
            "A professional e-commerce fashion photo of a {gender} model "
            "wearing a {color} {category}. The garment fits perfectly on the body. "
            "Studio lighting, pure white seamless background, sharp focus. "
            "The model's pose: arms relaxed at sides, weight evenly distributed. "
            "Standard catalog style with neutral facial expression."
        ),
        "jeans": (
            "A professional e-commerce fashion photo of a {gender} model "
            "wearing {color} {category}. The jeans fit naturally at the waist and hips. "
            "Studio lighting, pure white seamless background, sharp focus. "
            "Standard catalog style with neutral facial expression."
        ),
    })
    
    # Промпты для разных углов
    ANGLE_PROMPTS: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        "front": {
            "pose": "standing straight, full body, facing the camera directly",
            "weight": 1.0,
        },
        "side": {
            "pose": "standing straight, full body, side profile view (90 degrees)",
            "weight": 1.0,
        },
        "back": {
            "pose": "standing straight, full body, with back to the camera",
            "weight": 1.0,
        },
        "crop": {
            "pose": "cropped view focusing on the {category} fit and silhouette",
            "weight": 0.8,
        },
        "lifestyle": {
            "pose": "natural relaxed pose, soft daylight, minimal studio environment",
            "weight": 0.7,
        },
    })
    
    # Негативные промпты для качества
    QUALITY_NEGATIVE: str = (
        "bad quality, blurry, low resolution, distorted, deformed, ugly, "
        "watermark, text, logo, extra limbs, missing limbs, bad anatomy, "
        "crossed arms, hands in pockets, extreme pose, fashion pose, "
        "theatrical, dramatic, dark background, colored background, "
        "interior, street, outdoor, texture pattern, dirty, wrinkled, "
        "dyed hair, tattoos, piercings, heavy makeup"
    )
    
    # Категории и их параметры
    CATEGORIES: Dict[str, Dict] = field(default_factory=lambda: {
        "t-shirt": {
            "angles": ["front", "side", "back", "crop", "lifestyle"],
            "macro_needed": False,
            "has_fabric_texture": True,
        },
        "jeans": {
            "angles": ["front", "side", "back", "crop", "lifestyle"],
            "macro_needed": True,
            "has_fabric_texture": True,
        },
    })
    
    # Макро-детали для реальных фото
    MACRO_ANGLES: List[str] = field(default_factory=lambda: [
        "fabric_texture",
        "detail_print",
        "detail_hardware",
    ])


config = Config()




config = Config()