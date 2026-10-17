"""Пайплайн генерации с использованием эталонных моделей из папки models."""

import logging
import os
from pathlib import Path
from typing import Optional

from PIL import Image

from src.model_generator import ModelGenerator
from src.gptunnel_lamoda_client import LamodaStyleClient
from src.color_analyzer import ColorAnalyzer

logger = logging.getLogger(__name__)


class LamodaPipeline:
    """
    Пайплайн генерации с едиными моделями из папки models.
    detail ракурс генерируется через API с отдельным промптом.
    """
    
    def __init__(self, api_key: str, models_folder: str = "models"):
        self.client = LamodaStyleClient(api_key=api_key)
        self.model_gen = ModelGenerator()
        self.models_folder = Path(models_folder)
        
        # Создаем папку для моделей
        self.models_folder.mkdir(exist_ok=True)
        
        # Кэш для хранения сгенерированных изображений
        self.generated_cache: dict = {}
        
        # Проверяем наличие моделей
        self._check_models()
    
    def _check_models(self):
        """Проверяет наличие всех необходимых моделей."""
        print("\n" + "="*60)
        print("ПРОВЕРКА ЭТАЛОННЫХ МОДЕЛЕЙ")
        print("="*60)
        
        missing = []
        
        for gender in ['male', 'female']:
            for angle in ['front', 'side', 'back']:
                model_path = self.models_folder / f"{gender}_{angle}.png"
                if model_path.exists():
                    print(f"   ✅ {gender}/{angle} - найдена")
                else:
                    print(f"   ❌ {gender}/{angle} - ОТСУТСТВУЕТ")
                    missing.append(f"{gender}_{angle}.png")
        
        if missing:
            print(f"\n⚠️ ВНИМАНИЕ: Отсутствуют модели: {missing}")
            print("   Запустите python3 generate_models.py для их создания")
        
        print("="*60 + "\n")
    
    def get_model_image(self, gender: str, angle: str) -> Optional[Image.Image]:
        """Возвращает изображение эталонной модели."""
        model_path = self.models_folder / f"{gender}_{angle}.png"
        
        if not model_path.exists():
            print(f"   ❌ Модель не найдена: {gender}/{angle}")
            return None
        
        return Image.open(model_path).convert("RGB")
    
    def _generate_detail_via_api(
        self,
        clothing_image: Image.Image,
        model_image: Image.Image,
        category: str,
        gender: str,
        seed: int,
    ) -> Image.Image:
        """
        Генерирует детальное изображение (макро/крупный план) через API.
        """
        
        # Специальный промпт для детального кадра
        detail_prompt = f"""Generate a DETAILED CLOSE-UP fashion photo of the garment.

CRITICAL INSTRUCTION:
- The FIRST reference image shows the EXACT PERSON (model)
- The SECOND reference image shows the EXACT GARMENT

YOUR TASK:
1. Take the EXACT PERSON from the first reference image
2. Take the EXACT GARMENT from the second reference image
3. Create a CLOSE-UP / DETAIL shot focusing on the upper body and the garment
4. Show the garment details clearly: texture, fabric, pattern, fit

DETAIL SHOT SPECIFICATIONS:
- Frame: Crop tightly around the upper body (chest, shoulders, upper arms)
- DO NOT show full body - only upper body/torso area
- Focus on the garments
- The {category} must be clearly visible and take most of the frame

Model: {gender}, same person as in first reference image
Garment: EXACT {category} from second reference image
Color: Use EXACT color from second reference image
Background: Pure white seamless
Lighting: Soft even studio lighting, accentuating garment texture
Quality: Ultra HD, macro detail visible, sharp focus

CRITICAL: This is a DETAIL shot - close-up on the garment, not full body.
The garment should fill approximately 70-80% of the frame.

ABSOLUTELY FORBIDDEN:
- Full body shot
- Different person, changed face
- Changing garment color
- Dark or colored background
- Fashion poses, crossed arms"""
        
        print(f"   📝 Детальный промпт: {detail_prompt[:150]}...")
        
        # Генерируем через API с двумя reference images
        result = self.client._generate_with_reference(
            clothing_image=clothing_image,
            model_image=model_image,
            prompt=detail_prompt,
            seed=seed
        )
        
        return result
    
    def process_article(
        self,
        article_id: str,
        clothing_image: Image.Image,
        category: str,
        gender: str,
        angle: str,
        output_dir: str,
        seed: int = 42,
    ) -> Optional[str]:
        """
        Обрабатывает одно предметное фото.
        
        Для front/side/back: генерирует изображение через API.
        Для detail: генерирует крупный план через API.
        """
        
        print(f"\n{'─'*40}")
        print(f"📝 Артикул: {article_id}")
        print(f"   Ракурс: {angle}")
        print(f"   Категория: {category}")
        print(f"   Пол: {gender}")
        
        # ============================================================
        # detail ракурс — генерируем через API
        # ============================================================
        if angle == "detail":
            print(f"   🔍 Генерация детального кадра (крупный план)...")
            
            # Получаем эталонную модель (используем front для detail)
            model_image = self.get_model_image(gender, "front")
            if model_image is None:
                print(f"   ❌ Невозможно продолжить: отсутствует модель {gender}/front")
                return None
            
            print(f"   👤 Используется модель: {gender}/front")
            
            # Анализируем цвет для информации
            color_info = ColorAnalyzer.get_detailed_description(clothing_image)
            color = color_info["description"]
            print(f"   🎨 Цвет одежды: {color}")
            
            # Генерируем детальный кадр
            result = self._generate_detail_via_api(
                clothing_image=clothing_image,
                model_image=model_image,
                category=category,
                gender=gender,
                seed=seed,
            )
            
            # Приводим к стандартному размеру
            result = self.client._standardize_high_quality(result)
            
            # Сохраняем результат
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{article_id}_detail.webp")
            result.save(output_path, "WEBP", quality=95)
            
            print(f"   💾 Сохранено (деталь): {output_path}")
            return output_path
        
        # ============================================================
        # front/side/back — генерируем через API
        # ============================================================
        
        # Анализируем цвет одежды
        color_info = ColorAnalyzer.get_detailed_description(clothing_image)
        color = color_info["description"]
        print(f"   🎨 Цвет одежды: {color}")
        
        # Получаем эталонную модель
        model_image = self.get_model_image(gender, angle)
        if model_image is None:
            print(f"   ❌ Невозможно продолжить: отсутствует модель {gender}/{angle}")
            return None
        
        print(f"   👤 Эталонная модель: {gender}/{angle} загружена")
        
        # Генерируем результат
        result = self.client.generate_catalog_image(
            clothing_image=clothing_image,
            model_image=model_image,
            category=category,
            gender=gender,
            angle=angle,
            seed=seed,
        )
        
        # Сохраняем результат
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{article_id}_{angle}.webp")
        result.save(output_path, "WEBP", quality=95)
        
        print(f"   💾 Сохранено: {output_path}")
        
        # Сохраняем в кэш
        cache_key = f"{article_id}_{angle}"
        self.generated_cache[cache_key] = result
        
        return output_path
    
    def unload(self):
        """Освобождает ресурсы."""
        self.model_gen.unload()
        print("🔌 Ресурсы освобождены")