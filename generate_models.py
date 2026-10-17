#!/usr/bin/env python3
"""Генерация эталонных моделей через Nano Banana 2."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gptunnel_lamoda_client import LamodaStyleClient
from PIL import Image

API_KEY = os.environ.get("GPTUNNEL_API_KEY")

if not API_KEY:
    print("❌ export GPTUNNEL_API_KEY=your_key")
    sys.exit(1)

# Создаем папку для моделей
models_dir = Path("models")
models_dir.mkdir(exist_ok=True)

client = LamodaStyleClient(api_key=API_KEY, model="nano-banana-2-gemini")

# Промпты для генерации эталонных моделей
MODEL_PROMPTS = {
    "male": {
        "front": """Generate a professional e-commerce fashion photo of a MALE model.
CRITICAL: This is a FRONT view. The model MUST face the camera directly.
Model: 27 years old, European, athletic build, short well-groomed hair, neutral expression, no tattoos, no piercings.
Pose: Standing straight, arms relaxed at sides, weight evenly distributed, head straight.
Clothing: Plain white t-shirt and dark blue jeans (neutral, non-branded).
Background: Pure white seamless (#FFFFFF), no shadows, no gradients.
Lighting: Soft even studio lighting.
Quality: 8K resolution, ultra sharp focus, professional catalog style.
Full body from head to feet. No fashion poses, no crossed arms.""",
        
        "side": """Generate a professional e-commerce fashion photo of a MALE model.
CRITICAL: This is a SIDE PROFILE view (90 degrees to camera).
Model: 27 years old, European, athletic build, short well-groomed hair, neutral expression, no tattoos, no piercings.
Pose: Standing straight in side profile, arms relaxed, looking straight ahead.
Clothing: Plain white t-shirt and dark blue jeans (neutral, non-branded).
Background: Pure white seamless (#FFFFFF), no shadows, no gradients.
Lighting: Soft even studio lighting.
Quality: 8K resolution, ultra sharp focus, professional catalog style.
Full body from head to feet. Side silhouette must be clear.""",
        
        "back": """Generate a professional e-commerce fashion photo of a MALE model.
CRITICAL: This is a BACK view. The model's back faces the camera.
Model: 27 years old, European, athletic build, short well-groomed hair, no tattoos, no piercings.
Pose: Standing straight with back to camera, arms relaxed at sides.
Clothing: Plain white t-shirt and dark blue jeans (neutral, non-branded).
Background: Pure white seamless (#FFFFFF), no shadows, no gradients.
Lighting: Soft even studio lighting.
Quality: 8K resolution, ultra sharp focus, professional catalog style.
Full body from head to feet. Back of the garment must be clearly visible.""",
    },
    "female": {
        "front": """Generate a professional e-commerce fashion photo of a FEMALE model.
CRITICAL: This is a FRONT view. The model MUST face the camera directly.
Model: 25 years old, European, slim athletic build, natural long hair, neutral expression, natural minimal makeup, no tattoos, no piercings.
Pose: Standing straight, arms relaxed at sides, weight evenly distributed, head straight.
Clothing: Plain white t-shirt and dark blue jeans (neutral, non-branded).
Background: Pure white seamless (#FFFFFF), no shadows, no gradients.
Lighting: Soft even studio lighting.
Quality: 8K resolution, ultra sharp focus, professional catalog style.
Full body from head to feet. No fashion poses, no crossed arms.""",
        
        "side": """Generate a professional e-commerce fashion photo of a FEMALE model.
CRITICAL: This is a SIDE PROFILE view (90 degrees to camera).
Model: 25 years old, European, slim athletic build, natural long hair, neutral expression, natural minimal makeup, no tattoos, no piercings.
Pose: Standing straight in side profile, arms relaxed, looking straight ahead.
Clothing: Plain white t-shirt and dark blue jeans (neutral, non-branded).
Background: Pure white seamless (#FFFFFF), no shadows, no gradients.
Lighting: Soft even studio lighting.
Quality: 8K resolution, ultra sharp focus, professional catalog style.
Full body from head to feet. Side silhouette must be clear.""",
        
        "back": """Generate a professional e-commerce fashion photo of a FEMALE model.
CRITICAL: This is a BACK view. The model's back faces the camera.
Model: 25 years old, European, slim athletic build, natural long hair, no tattoos, no piercings.
Pose: Standing straight with back to camera, arms relaxed at sides.
Clothing: Plain white t-shirt and dark blue jeans (neutral, non-branded).
Background: Pure white seamless (#FFFFFF), no shadows, no gradients.
Lighting: Soft even studio lighting.
Quality: 8K resolution, ultra sharp focus, professional catalog style.
Full body from head to feet. Back of the garment must be clearly visible.""",
    },
}

def generate_model(gender: str, angle: str) -> Image.Image:
    """Генерирует модель через Nano Banana 2."""
    
    print(f"   🎨 Генерация: {gender} / {angle}")
    
    prompt = MODEL_PROMPTS[gender][angle]
    
    # Создаем заглушку для изображения (Nano Banana не принимает пустое изображение)
    # Создаем белое изображение как референс
    dummy_image = Image.new('RGB', (512, 768), color='white')
    
    # Генерируем через Nano Banana
    result = client._generate(dummy_image, prompt, seed=42 if gender == 'male' else 123)
    
    # Приводим к стандартному размеру
    result = client._standardize(result)
    
    return result

def main():
    print("="*60)
    print("ГЕНЕРАЦИЯ ЭТАЛОННЫХ МОДЕЛЕЙ ЧЕРЕЗ NANO BANANA 2")
    print("="*60)
    
    for gender in ['male', 'female']:
        for angle in ['front', 'side', 'back']:
            output_path = models_dir / f"{gender}_{angle}.png"
            
            if output_path.exists():
                print(f"   ⏭️ Пропуск: {gender}/{angle} (уже существует)")
                continue
            
            try:
                result = generate_model(gender, angle)
                result.save(output_path, "PNG")
                print(f"   ✅ Сохранено: {output_path}")
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
    
    print("\n" + "="*60)
    print("ГОТОВО!")
    print(f"Модели сохранены в папке: {models_dir}")
    print("="*60)

if __name__ == "__main__":
    main()