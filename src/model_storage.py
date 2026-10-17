"""Хранение и управление эталонными моделями."""

import os
import json
from pathlib import Path
from typing import Dict, Optional

from PIL import Image


class ModelStorage:
    """
    Хранилище эталонных моделей.
    Сохраняет сгенерированные модели в папку и загружает при повторном использовании.
    """
    
    def __init__(self, models_folder: str = "models"):
        self.models_folder = Path(models_folder)
        self.models_folder.mkdir(exist_ok=True)
        
        # Словарь для хранения путей к моделям
        self.models: Dict[str, Dict[str, str]] = {}
        self._load_index()
    
    def _load_index(self):
        """Загружает индекс сохраненных моделей."""
        index_path = self.models_folder / "index.json"
        
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                self.models = json.load(f)
        else:
            self.models = {
                "male": {"front": "", "side": "", "back": ""},
                "female": {"front": "", "side": "", "back": ""}
            }
    
    def _save_index(self):
        """Сохраняет индекс моделей."""
        index_path = self.models_folder / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(self.models, f, ensure_ascii=False, indent=2)
    
    def save_model(self, gender: str, angle: str, image: Image.Image) -> str:
        """
        Сохраняет модель в папку.
        
        Args:
            gender: 'male' или 'female'
            angle: 'front', 'side', 'back'
            image: Изображение модели
        """
        # Сохраняем изображение
        filename = f"{gender}_{angle}.png"
        filepath = self.models_folder / filename
        image.save(filepath, "PNG")
        
        # Обновляем индекс
        if gender not in self.models:
            self.models[gender] = {}
        self.models[gender][angle] = str(filepath)
        self._save_index()
        
        return str(filepath)
    
    def get_model(self, gender: str, angle: str) -> Optional[Image.Image]:
        """
        Загружает модель из хранилища.
        
        Returns:
            PIL Image или None, если модель не найдена
        """
        if gender not in self.models:
            return None
        
        filepath = self.models[gender].get(angle, "")
        
        if filepath and os.path.exists(filepath):
            return Image.open(filepath).convert("RGB")
        
        return None
    
    def has_model(self, gender: str, angle: str) -> bool:
        """Проверяет, существует ли модель для данного пола и ракурса."""
        if gender not in self.models:
            return False
        return bool(self.models[gender].get(angle)) and os.path.exists(self.models[gender][angle])
    
    def get_any_model(self, gender: str) -> Optional[Image.Image]:
        """Возвращает любую доступную модель для указанного пола."""
        if gender not in self.models:
            return None
        
        for angle in ['front', 'side', 'back']:
            if self.has_model(gender, angle):
                return self.get_model(gender, angle)
        
        return None