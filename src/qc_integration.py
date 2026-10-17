"""Интеграция QC в основной пайплайн."""

import json
from pathlib import Path
from typing import Dict, Any

from src.qc.validator import QCValidator, QCResult


def add_qc_to_pipeline(output_folder: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Добавляет QC проверку в конец пайплайна.
    
    Returns:
        Сводка по QC решениям
    """
    
    from src.qc.validator import BatchValidator
    
    validator = BatchValidator()
    results = validator.validate_all(output_folder, metadata)
    
    # Статистика
    stats = {
        "total": len(results),
        "auto_pass": sum(1 for r in results if r.qc_decision == "AUTO_PASS"),
        "manual_review": sum(1 for r in results if r.qc_decision == "MANUAL_REVIEW"),
        "auto_fail": sum(1 for r in results if r.qc_decision == "AUTO_FAIL"),
        "auto_approval_rate": 0.0,
    }
    
    if stats["total"] > 0:
        stats["auto_approval_rate"] = stats["auto_pass"] / stats["total"] * 100
    
    # Сохраняем сводку
    summary_path = Path(output_folder) / "qc_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    # Сохраняем детальные результаты для manual review
    manual_review_list = [
        r.to_dict() for r in results if r.qc_decision == "MANUAL_REVIEW"
    ]
    
    if manual_review_list:
        manual_path = Path(output_folder) / "manual_review_required.json"
        with open(manual_path, "w", encoding="utf-8") as f:
            json.dump(manual_review_list, f, indent=2, ensure_ascii=False)
    
    return stats