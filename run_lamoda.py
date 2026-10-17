#!/usr/bin/env python3
"""Запуск пайплайна с генерацией detail через API."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.lamoda_pipeline import LamodaPipeline
from src.data_loader import DataLoader

API_KEY = os.environ.get("GPTUNNEL_API_KEY")

if not API_KEY:
    print("❌ export GPTUNNEL_API_KEY=your_key")
    sys.exit(1)

# ============================================
# НАСТРОЙКИ
# ============================================
ROOT_FOLDER = "Предметные фото"
EXCEL_FILE = "articles.xlsx"
SHEET_NAME = 0

# Какие ракурсы генерировать
# detail генерируется отдельно через API
ANGLES = ["front", "side", "back", "detail"]
# ============================================

# Загружаем данные
loader = DataLoader(
    root_folder=ROOT_FOLDER,
    excel_file=EXCEL_FILE,
    sheet_name=SHEET_NAME,
)
articles = loader.load_all()

print(f"\n📊 Найдено артикулов: {len(articles)}")

if not articles:
    print("❌ Нет артикулов для обработки")
    sys.exit(1)

# Выводим информацию
print("\n📋 Артикулы:")
for art in articles[:5]:
    print(f"   {art.article_id} | {art.category} | {art.color} | {art.gender}")
    print(f"      Исходные ракурсы: {list(art.images.keys())}")

# Создаем пайплайн
pipeline = LamodaPipeline(api_key=API_KEY)

# Обрабатываем артикулы
for article in articles:
    print(f"\n{'='*60}")
    print(f"📦 Артикул: {article.article_id}")
    print(f"   Категория: {article.category}")
    print(f"   Цвет: {article.color}")
    print(f"   Бренд: {article.brand}")
    print(f"   Пол: {article.gender}")
    print(f"   Исходные ракурсы: {list(article.images.keys())}")
    print(f"{'='*60}")
    
    # Для каждого угла из списка ANGLES
    for angle in ANGLES:
        # Для front/side/back нужно исходное изображение одежды
        if angle != "detail":
            if angle not in article.images:
                print(f"\n⚠️ Ракурс {angle} не найден для {article.article_id}, пропускаем")
                continue
            
            image_path = article.images[angle]
            clothing = DataLoader.open_image(image_path)
        else:
            # Для detail берем любое изображение (front)
            if "front" in article.images:
                image_path = article.images["front"]
            elif article.images:
                image_path = list(article.images.values())[0]
            else:
                print(f"\n⚠️ Нет изображений для {article.article_id}")
                continue
            
            clothing = DataLoader.open_image(image_path)
        
        print(f"\n📸 Обработка ракурса: {angle}")
        
        pipeline.process_article(
            article_id=article.article_id,
            clothing_image=clothing,
            category=article.category,
            gender=article.gender,
            angle=angle,
            output_dir="output_lamoda",
            seed=42,
        )

print("\n✅ Все артикулы обработаны!")