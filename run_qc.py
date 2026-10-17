# run_qc.py
"""Запуск QC проверки для сгенерированных изображений."""

import json
from pathlib import Path

from src.qc_integration import add_qc_to_pipeline

# Загружаем метаданные артикулов из Excel
# (здесь нужно реализовать загрузку)

metadata = {
    "ART001": {
        "category": "Футболки",
        "has_text_or_logo": True,
        "has_small_print": False,
    },
    # ...
}

stats = add_qc_to_pipeline(
    output_folder="output_lamoda",
    metadata=metadata,
)

print(f"QC Статистика:")
print(f"  Всего: {stats['total']}")
print(f"  Auto-pass: {stats['auto_pass']}")
print(f"  Manual review: {stats['manual_review']}")
print(f"  Auto-fail: {stats['auto_fail']}")
print(f"  Auto-approval rate: {stats['auto_approval_rate']:.1f}%")