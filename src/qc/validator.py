"""QC-валидатор для AI-сгенерированных изображений."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from PIL import Image

from src.qc.config import qc_config, BusinessFlags
from src.qc.metrics import MetricsCalculator
from src.qc.background_check import BackgroundChecker
from src.qc.artifact_detector import ArtifactDetector
from src.qc.ocr_check import OCRChecker

logger = logging.getLogger(__name__)


@dataclass
class QCResult:
    """Результат QC проверки."""
    
    # Boolean gates
    qc_dimensions_ok: bool = True
    qc_format_ok: bool = True
    qc_colorspace_ok: bool = True
    qc_required_shots_ok: bool = True
    qc_source_count_ok: bool = True
    qc_background_ok: bool = True
    qc_visibility_ok: bool = True
    qc_artifact_hard_fail: bool = False
    qc_text_match_ok: Optional[bool] = None
    
    # Scores
    qc_ocr_confidence: float = 1.0
    silhouette_score: float = 0.0
    fit_score: float = 0.0
    texture_score: float = 0.0
    detail_integrity_score: float = 0.0
    lifestyle_score: float = 0.0
    overall_qc_score: float = 0.0
    
    # Decision
    qc_decision: str = "AUTO_PASS"  # AUTO_PASS, MANUAL_REVIEW, AUTO_FAIL
    qc_fail_reasons: List[str] = field(default_factory=list)
    qc_review_reasons: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует результат в словарь."""
        return {
            "qc_dimensions_ok": self.qc_dimensions_ok,
            "qc_format_ok": self.qc_format_ok,
            "qc_colorspace_ok": self.qc_colorspace_ok,
            "qc_required_shots_ok": self.qc_required_shots_ok,
            "qc_source_count_ok": self.qc_source_count_ok,
            "qc_background_ok": self.qc_background_ok,
            "qc_visibility_ok": self.qc_visibility_ok,
            "qc_artifact_hard_fail": self.qc_artifact_hard_fail,
            "qc_text_match_ok": self.qc_text_match_ok,
            "qc_ocr_confidence": self.qc_ocr_confidence,
            "silhouette_score": self.silhouette_score,
            "fit_score": self.fit_score,
            "texture_score": self.texture_score,
            "detail_integrity_score": self.detail_integrity_score,
            "lifestyle_score": self.lifestyle_score,
            "overall_qc_score": self.overall_qc_score,
            "qc_decision": self.qc_decision,
            "qc_fail_reasons": self.qc_fail_reasons,
            "qc_review_reasons": self.qc_review_reasons,
        }


class QCValidator:
    """
    QC-валидатор для AI-сгенерированных изображений.
    Проверяет качество и принимает решение: AUTO_PASS / MANUAL_REVIEW / AUTO_FAIL.
    """
    
    def __init__(self):
        self.metrics_calculator = MetricsCalculator()
        self.background_checker = BackgroundChecker()
        self.artifact_detector = ArtifactDetector()
        self.ocr_checker = OCRChecker()
        self.business_flags = BusinessFlags()
    
    def validate(
        self,
        image: Image.Image,
        image_path: Path,
        article_data: Dict[str, Any],
        category: str,
        has_text_or_logo: bool = False,
        **business_flags,
    ) -> QCResult:
        """
        Выполняет полную QC проверку изображения.
        
        Args:
            image: PIL Image для проверки
            image_path: Путь к файлу
            article_data: Данные артикула из Excel
            category: Категория одежды
            has_text_or_logo: Есть ли текст/логотип на одежде
            **business_flags: Дополнительные бизнес-флаги
        
        Returns:
            QCResult с результатами проверки
        """
        
        result = QCResult()
        
        # 1. Technical gates (формальные проверки)
        result = self._check_technical_gates(image, image_path, result)
        
        # 2. Business flags (риск-флаги)
        risk_flags = self._check_business_flags(article_data, category, business_flags)
        
        # 3. Quality metrics (score-based)
        result = self._calculate_metrics(image, result, category, has_text_or_logo)
        
        # 4. Background check
        result = self._check_background(image, result)
        
        # 5. Artifact detection
        result = self._check_artifacts(image, result)
        
        # 6. OCR check for text/logo
        if has_text_or_logo:
            result = self._check_ocr(image, result)
        
        # 7. Calculate overall score
        result = self._calculate_overall_score(result, has_text_or_logo)
        
        # 8. Make decision
        result = self._make_decision(result, risk_flags)
        
        return result
    
    def _check_technical_gates(
        self, 
        image: Image.Image, 
        image_path: Path, 
        result: QCResult
    ) -> QCResult:
        """Проверяет технические требования."""
        
        # Размер
        if image.size != qc_config.required_size:
            result.qc_dimensions_ok = False
            result.qc_fail_reasons.append("OUTPUT_WRONG_DIMENSIONS")
        
        # Формат
        suffix = image_path.suffix.lower()
        if suffix != f".{qc_config.required_format}":
            result.qc_format_ok = False
            result.qc_fail_reasons.append("OUTPUT_WRONG_FORMAT")
        
        # Цветовой профиль (упрощенная проверка)
        if image.mode != "RGB":
            result.qc_colorspace_ok = False
            result.qc_fail_reasons.append("OUTPUT_WRONG_COLORSPACE")
        
        return result
    
    def _check_business_flags(
        self,
        article_data: Dict[str, Any],
        category: str,
        flags: Dict[str, bool],
    ) -> List[str]:
        """Проверяет бизнес-флаги для ручной проверки."""
        
        risk_flags = []
        
        # Проверяем переданные флаги
        for flag, value in flags.items():
            if value and flag in self.business_flags.manual_review_categories:
                risk_flags.append(flag)
        
        # Проверяем категорию на риск
        if category in self.business_flags.risk_categories:
            risk_level = self.business_flags.risk_categories[category]
            if risk_level == "high":
                risk_flags.append(f"high_risk_category_{category}")
        
        return risk_flags
    
    def _calculate_metrics(
        self,
        image: Image.Image,
        result: QCResult,
        category: str,
        has_text_or_logo: bool,
    ) -> QCResult:
        """Рассчитывает score-based метрики."""
        
        metrics = self.metrics_calculator.calculate_all(image, category)
        
        result.silhouette_score = metrics.get("silhouette", 0.0)
        result.fit_score = metrics.get("fit", 0.0)
        result.texture_score = metrics.get("texture", 0.0)
        result.detail_integrity_score = metrics.get("detail_integrity", 0.0)
        result.lifestyle_score = metrics.get("lifestyle", 0.0)
        
        return result
    
    def _check_background(
        self,
        image: Image.Image,
        result: QCResult,
    ) -> QCResult:
        """Проверяет фон."""
        
        is_white, confidence = self.background_checker.is_white_background(image)
        
        if not is_white:
            result.qc_background_ok = False
            result.qc_review_reasons.append("QC_BACKGROUND_NOT_WHITE")
        
        return result
    
    def _check_artifacts(
        self,
        image: Image.Image,
        result: QCResult,
    ) -> QCResult:
        """Проверяет наличие артефактов."""
        
        has_critical, artifacts = self.artifact_detector.detect(image)
        
        if has_critical:
            result.qc_artifact_hard_fail = True
            result.qc_fail_reasons.append("QC_ARTIFACT_CRITICAL")
        
        return result
    
    def _check_ocr(
        self,
        image: Image.Image,
        result: QCResult,
    ) -> QCResult:
        """Проверяет текст/принт на изображении."""
        
        text_detected, confidence, matched = self.ocr_checker.check_text_accuracy(image)
        
        result.qc_ocr_confidence = confidence
        
        if not matched:
            result.qc_text_match_ok = False
            result.qc_review_reasons.append("QC_TEXT_MISMATCH")
        else:
            result.qc_text_match_ok = True
        
        return result
    
    def _calculate_overall_score(
        self,
        result: QCResult,
        has_text_or_logo: bool,
    ) -> QCResult:
        """Рассчитывает общий QC score."""
        
        # Для товаров без текста OCR confidence = 1.0
        ocr_adj = result.qc_ocr_confidence if has_text_or_logo else 1.0
        
        overall = (
            qc_config.weights["silhouette"] * result.silhouette_score +
            qc_config.weights["fit"] * result.fit_score +
            qc_config.weights["texture"] * result.texture_score +
            qc_config.weights["detail_integrity"] * result.detail_integrity_score +
            qc_config.weights["lifestyle"] * result.lifestyle_score +
            qc_config.weights["ocr_confidence"] * ocr_adj
        )
        
        result.overall_qc_score = round(overall, 3)
        
        return result
    
    def _make_decision(
        self,
        result: QCResult,
        risk_flags: List[str],
    ) -> QCResult:
        """
        Принимает решение на основе всех проверок.
        
        Правила:
        1. AUTO_FAIL если есть hard fail
        2. MANUAL_REVIEW если есть риск-флаги или scores в review-zone
        3. AUTO_PASS если все gates true и scores >= thresholds
        """
        
        # AUTO_FAIL: hard fail gates
        if not all([
            result.qc_dimensions_ok,
            result.qc_format_ok,
            result.qc_colorspace_ok,
            result.qc_source_count_ok,
            not result.qc_artifact_hard_fail,
        ]):
            result.qc_decision = "AUTO_FAIL"
            return result
        
        # AUTO_FAIL: score ниже hard-fail порога
        if self._is_below_hard_fail_threshold(result):
            result.qc_decision = "AUTO_FAIL"
            return result
        
        # MANUAL_REVIEW: бизнес-флаги
        if risk_flags:
            result.qc_decision = "MANUAL_REVIEW"
            result.qc_review_reasons.extend(risk_flags)
            return result
        
        # MANUAL_REVIEW: scores в review-zone
        if self._is_in_review_zone(result):
            result.qc_decision = "MANUAL_REVIEW"
            if not result.qc_review_reasons:
                result.qc_review_reasons.append("SCORES_IN_REVIEW_ZONE")
            return result
        
        # MANUAL_REVIEW: manual flag в результатах
        if result.qc_review_reasons:
            result.qc_decision = "MANUAL_REVIEW"
            return result
        
        # AUTO_PASS: все условия выполнены
        if (result.overall_qc_score >= qc_config.overall_auto_pass_threshold and
            not result.qc_fail_reasons):
            result.qc_decision = "AUTO_PASS"
        else:
            result.qc_decision = "MANUAL_REVIEW"
        
        return result
    
    def _is_below_hard_fail_threshold(self, result: QCResult) -> bool:
        """Проверяет, есть ли score ниже hard-fail порога."""
        
        checks = [
            ("silhouette", result.silhouette_score),
            ("fit", result.fit_score),
            ("texture", result.texture_score),
            ("detail_integrity", result.detail_integrity_score),
        ]
        
        for name, score in checks:
            auto_pass, manual_min, hard_fail = qc_config.thresholds[name]
            if score < hard_fail:
                result.qc_fail_reasons.append(f"QC_{name.upper()}_LOW")
                return True
        
        return False
    
    def _is_in_review_zone(self, result: QCResult) -> bool:
        """Проверяет, попали ли scores в зону manual review."""
        
        checks = [
            ("silhouette", result.silhouette_score),
            ("fit", result.fit_score),
            ("texture", result.texture_score),
            ("detail_integrity", result.detail_integrity_score),
        ]
        
        for name, score in checks:
            auto_pass, manual_min, hard_fail = qc_config.thresholds[name]
            if manual_min <= score < auto_pass:
                return True
        
        return False


# Утилита для batch-валидации
class BatchValidator:
    """Валидатор для пачки изображений."""
    
    def __init__(self):
        self.validator = QCValidator()
    
    def validate_all(
        self,
        output_folder: str,
        metadata: Dict[str, Any],
    ) -> List[QCResult]:
        """
        Валидирует все изображения в output папке.
        
        Args:
            output_folder: Папка с результатами генерации
            metadata: Метаданные по артикулам (из Excel)
        
        Returns:
            Список результатов QC для каждого изображения
        """
        
        results = []
        output_path = Path(output_folder)
        
        for image_file in output_path.glob("*.webp"):
            # Парсим артикул и ракурс из имени файла
            parts = image_file.stem.split("_")
            if len(parts) >= 2:
                article_id = parts[0]
                angle = parts[1]
            else:
                continue
            
            # Получаем метаданные артикула
            article_meta = metadata.get(article_id, {})
            
            # Валидируем
            image = Image.open(image_file)
            result = self.validator.validate(
                image=image,
                image_path=image_file,
                article_data=article_meta,
                category=article_meta.get("category", "unknown"),
                has_text_or_logo=article_meta.get("has_text_or_logo", False),
            )
            
            results.append(result)
            
            # Сохраняем результат в JSON
            result_file = image_file.with_suffix(".qc.json")
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        
        return results