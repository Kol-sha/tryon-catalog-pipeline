"""GPTunnel клиент для Lamoda-стиля с высоким качеством."""

import base64
import io
import logging
import time
from typing import Optional, Tuple

import requests
from PIL import Image

from src.color_analyzer import ColorAnalyzer
from config import config

logger = logging.getLogger(__name__)


class LamodaStyleClient:
    """
    Клиент для генерации каталожных изображений высокого качества (300 DPI).
    """
    
    def __init__(self, api_key: str, model: str = "nano-banana-2-gemini"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://gptunnel.ru/v1/media/create"
        self.result_url = "https://gptunnel.ru/v1/media/result"
        
        # Настройки качества
        self.output_size = config.OUTPUT_SIZE  # (1524, 2200)
        self.output_dpi = config.OUTPUT_DPI    # 300
        self.steps = config.API_STEPS          # 40
        self.cfg_scale = config.API_CFG_SCALE  # 7.5
        
        # Настройки повторных попыток
        self.max_retries = 5
        self.retry_delay = 3
        
    def generate_catalog_image(
        self,
        clothing_image: Image.Image,
        model_image: Image.Image,
        category: str,
        gender: str,
        angle: str,
        output_path: Optional[str] = None,
        seed: int = 42,
    ) -> Image.Image:
        """
        Генерация высококачественного каталожного изображения.
        """
        
        print(f"   📐 Категория: {category}, Пол: {gender}, Ракурс: {angle}")
        print(f"   👤 Используется эталонная модель: {gender}/{angle}")
        print(f"   ⚙️ Параметры качества: {self.steps} steps, CFG={self.cfg_scale}, DPI={self.output_dpi}")
        
        # Формируем промпт с инструкциями по качеству
        prompt = self._build_high_quality_prompt(category, gender, angle)
        
        print(f"   📝 Промпт: {prompt[:150]}...")
        
        # Генерируем с улучшенными параметрами
        result = self._generate_with_reference(
            clothing_image, model_image, prompt, seed
        )
        
        # Приводим к стандартному размеру с 300 DPI
        result = self._standardize_high_quality(result)
        
        if output_path:
            self._save_high_quality(result, output_path)
        
        return result
    
    def _build_high_quality_prompt(self, category: str, gender: str, angle: str) -> str:
        """Промпт с акцентом на высокое качество и 300 DPI."""
        
        # Описание ракурса
        angle_desc = {
            "front": "STANDING STRAIGHT, FACING THE CAMERA DIRECTLY",
            "back": "STANDING WITH BACK TO THE CAMERA",
            "side": "STANDING IN SIDE PROFILE (90 degrees to camera)",
        }.get(angle, "STANDING STRAIGHT")
        
        # Для джинс добавляем белую футболку
        top_instruction = ""
        if category == "Джинсы":
            top_instruction = " The person is wearing a plain WHITE T-SHIRT on top (no logos, no prints, pure white cotton) which is tucked in his pants."
        
        prompt = f"""ULTRA HIGH QUALITY PROFESSIONAL E-COMMERCE PHOTO - 300 DPI PRINT QUALITY

CRITICAL INSTRUCTIONS:
The FIRST image shows the EXACT PERSON (model) that MUST be used.
The SECOND image shows the EXACT GARMENT that MUST be put on that person.

QUALITY REQUIREMENTS (MOST IMPORTANT):
- 300 DPI resolution, print-ready quality
- Ultra sharp focus, tack sharp details
- Professional studio lighting with softboxes
- Pure white seamless background (#FFFFFF)
- No compression artifacts, no noise
- High color accuracy, wide color gamut
- 8K ultra HD detail

GARMENT DETAILS:
- Type: {category}
- COLOR: Use EXACT same color as shown in the second reference image
- Texture, pattern, folds, silhouette: Copy EXACTLY from the second image
- Fabric details must be clearly visible{top_instruction}

MODEL REQUIREMENTS:
- {gender}, 20-25 years old, European appearance
- Natural minimal makeup (no heavy makeup)
- Neutral expression or light smile
- No tattoos, no piercings
- Clean, well-groomed appearance

POSE: {angle_desc}
- Arms relaxed at sides, not crossed
- Weight evenly distributed
- Standing straight with good posture
- Full body from head to feet visible

LIGHTING REQUIREMENTS:
- Soft even studio lighting (3-point lighting setup)
- No harsh shadows
- No hot spots or overexposure
- Even illumination across the garment

TECHNICAL REQUIREMENTS:
- 300 DPI, 1524×2200 pixels final size
- sRGB color space
- Commercial catalog standard
- No watermark, no text overlay

NEGATIVE PROMPT:
bad quality, low resolution, blurry, pixelated, compressed, artifacts, noise, grain
wrong color, different color, color mismatch, color bleeding
dark background, colored background, shadow on background, gradient background
fashion pose, dramatic pose, crossed arms, hands in pockets
tattoo, piercing, heavy makeup, bright lipstick
watermark, text, logo, signature, label
distorted, deformed, bad anatomy, extra limbs, missing limbs
unrealistic, artificial, CGI, 3D render, cartoon, illustration
wrinkled garment, dirty, stained
overexposed, underexposed, harsh shadows, direct flash
soft focus, out of focus, motion blur"""
        
        return prompt
    
    def _generate_with_reference(
        self, 
        clothing_image: Image.Image, 
        model_image: Image.Image,
        prompt: str, 
        seed: int
    ) -> Image.Image:
        """Генерация с высоким качеством через API."""
        
        # Конвертируем в data URL с высоким качеством
        clothing_url = self._image_to_data_url_high_quality(clothing_image)
        model_url = self._image_to_data_url_high_quality(model_image)
        
        # Payload с параметрами качества
        payload = {
            "model": self.model,
            "prompt": prompt,
            "ar": "9:16",
            "images": [model_url, clothing_url],
            "seed": seed,
            "steps": self.steps,           # больше шагов = лучше качество
            "cfg_scale": self.cfg_scale,   # выше = точнее следует промпту
            "sampler": "DPM++ 2M Karras",  # качественный семплер
        }
        
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        
        # Создаем задачу
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url, 
                    json=payload, 
                    headers=headers, 
                    timeout=120  # увеличенный таймаут для высокого качества
                )
                
                if response.status_code != 200:
                    raise Exception(f"Create task failed: {response.text}")
                
                data = response.json()
                task_id = data.get("id")
                
                if not task_id:
                    raise Exception(f"No task ID: {data}")
                
                # Ожидаем результат
                result_url = self._wait_for_result_high_quality(task_id)
                
                # Скачиваем
                img_response = requests.get(result_url, timeout=120)
                img_response.raise_for_status()
                
                return Image.open(io.BytesIO(img_response.content)).convert("RGB")
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait = self.retry_delay * (attempt + 1)
                    print(f"   ⚠️ Попытка {attempt + 1} не удалась: {e}")
                    print(f"   🔄 Повтор через {wait} сек...")
                    time.sleep(wait)
                else:
                    raise
        
        raise Exception("All retries failed")
    
    def _image_to_data_url_high_quality(self, image: Image.Image, quality: int = 95) -> str:
        """Конвертирует в data URL с высоким качеством."""
        
        buffer = io.BytesIO()
        
        # Конвертируем в RGB если нужно
        if image.mode != "RGB":
            rgb = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "RGBA":
                rgb.paste(image, mask=image.split()[-1])
            else:
                rgb.paste(image)
            image = rgb
        
        # Сохраняем с высоким качеством
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        b64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/jpeg;base64,{b64}"
    
    def _wait_for_result_high_quality(self, task_id: str, max_attempts: int = 90) -> str:
        """Ожидает результат с увеличенным временем для высокого качества."""
        
        headers = {"Authorization": self.api_key}
        
        for attempt in range(max_attempts):
            try:
                response = requests.post(
                    self.result_url,
                    headers=headers,
                    json={"task_id": task_id},
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    image_url = data.get("url")
                    
                    if status == "done" and image_url:
                        elapsed = attempt * 3
                        print(f"   ✓ Готово за ~{elapsed} сек")
                        return image_url
                    
                    if status == "running":
                        if attempt % 5 == 0:
                            print(f"   Генерация высокого качества... ({attempt * 3} сек)")
                        time.sleep(3)
                        continue
                    
                    if status == "failed":
                        raise Exception(f"Generation failed: {data.get('error')}")
                
                time.sleep(3)
                
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                print(f"   ⚠️ Ошибка соединения (попытка {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(5)
                else:
                    raise
        
        raise TimeoutError("Generation timed out")
    
    def _standardize_high_quality(self, image: Image.Image) -> Image.Image:
        """Приводит изображение к стандарту 1524×2200 с 300 DPI."""
        
        target_w, target_h = self.output_size
        img_w, img_h = image.size
        
        # Сохраняем соотношение сторон
        scale = min(target_w / img_w, target_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        # Используем LANCZOS для максимального качества
        resized = image.resize((new_w, new_h), Image.LANCZOS)
        
        # Создаем белый канвас
        canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
        x = (target_w - new_w) // 2
        y = (target_h - new_h) // 2
        canvas.paste(resized, (x, y))
        
        # Устанавливаем DPI метаданные
        canvas.info['dpi'] = (self.output_dpi, self.output_dpi)
        
        return canvas
    
    def _save_high_quality(self, image: Image.Image, path: str):
        """Сохраняет изображение с высоким качеством и DPI метаданными."""
        
        if path.endswith('.webp'):
            # WebP с высоким качеством
            image.save(path, "WEBP", quality=95, method=6)
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            # JPEG с высоким качеством и DPI
            image.save(path, "JPEG", quality=95, dpi=(self.output_dpi, self.output_dpi), optimize=True)
        else:
            image.save(path, "PNG", dpi=(self.output_dpi, self.output_dpi))
        
        print(f"   💾 Сохранено с DPI={self.output_dpi}")