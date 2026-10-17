# src/output_manager.py

import logging
from pathlib import Path
from typing import List

from PIL import Image

from config import config

logger = logging.getLogger(__name__)


class OutputManager:
    def __init__(self, output_folder: str = config.OUTPUT_FOLDER):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def save_result(
        self,
        image:      Image.Image,
        article_id: str,
        angle_num:  int,
    ) -> Path:
        path = self.output_folder / f"{article_id}_{angle_num}.jpg"
        image.convert("RGB").save(path, "JPEG", quality=95)
        logger.info(f"  ✓ Saved: {path}")
        return path

    def generate_report(self, results: List[dict]) -> Path:
        path = self.output_folder / "processing_report.txt"
        lines = [
            "=" * 60,
            "NANO BANANA TRY-ON REPORT",
            "=" * 60,
            f"Total articles : {len(results)}",
            "",
        ]
        for r in results:
            ok = "✓" if r["success"] else "✗"
            lines.append(
                f"  {ok} {r['article_id']:20s} | {r['gender']:6s} | "
                f"angles={r['angles_processed']} | "
                f"{r.get('error', 'OK')}"
            )
        path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Report: {path}")
        return path