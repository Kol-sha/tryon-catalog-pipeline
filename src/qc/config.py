"""QC пороги и настройки."""

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class QCThresholds:
    """Пороги для score-based проверок."""
    
    # Пороги для auto-pass / manual-review / hard-fail
    thresholds: Dict[str, Tuple[float, float, float]] = field(default_factory=lambda: {
        "silhouette": (0.92, 0.80, 0.80),    # (auto_pass, manual_min, hard_fail)
        "fit": (0.90, 0.78, 0.78),
        "texture": (0.88, 0.72, 0.72),
        "detail_integrity": (0.92, 0.80, 0.80),
        "lifestyle": (0.85, 0.70, 0.70),
        "ocr_confidence": (0.93, 0.75, 0.75),
    })
    
    # Веса для overall_score
    weights: Dict[str, float] = field(default_factory=lambda: {
        "silhouette": 0.22,
        "fit": 0.22,
        "texture": 0.18,
        "detail_integrity": 0.18,
        "lifestyle": 0.10,
        "ocr_confidence": 0.10,
    })
    
    # Общий порог auto-pass
    overall_auto_pass_threshold: float = 0.87
    
    # Размер и формат
    required_size: Tuple[int, int] = (1524, 2200)
    required_format: str = "webp"
    required_color_profile: str = "sRGB"
    required_shots_count: int = 6


@dataclass
class BusinessFlags:
    """Бизнес-флаги для маршрутизации."""
    
    risk_categories: Dict[str, str] = field(default_factory=lambda: {
        "прозрачная ткань": "high",
        "мелкий принт": "high",
        "текст/логотип": "high",
        "сложная фурнитура": "high",
    })
    
    # Категории, требующие manual review
    manual_review_categories: list = field(default_factory=lambda: [
        "has_transparency",
        "has_small_print", 
        "has_text_or_logo",
        "has_complex_hardware",
    ])


qc_config = QCThresholds()