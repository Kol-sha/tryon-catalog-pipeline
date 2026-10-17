"""Анализ цвета одежды с предметного фото."""

import numpy as np
from PIL import Image
from collections import Counter
import webcolors


class ColorAnalyzer:
    """Определяет точный цвет одежды с предметного фото."""
    
    # Базовые цвета для маппинга
    COLOR_MAP = {
        'black': ['black', 'dark', 'charcoal', 'graphite'],
        'white': ['white', 'off-white', 'cream', 'ivory'],
        'red': ['red', 'scarlet', 'crimson', 'burgundy', 'maroon'],
        'blue': ['blue', 'navy', 'cobalt', 'royal', 'azure'],
        'green': ['green', 'olive', 'emerald', 'forest', 'lime'],
        'yellow': ['yellow', 'gold', 'mustard', 'lemon'],
        'pink': ['pink', 'rose', 'coral', 'magenta', 'fuschia'],
        'purple': ['purple', 'lavender', 'violet', 'plum'],
        'orange': ['orange', 'peach', 'coral', 'tangerine'],
        'gray': ['gray', 'grey', 'silver', 'slate'],
        'brown': ['brown', 'beige', 'tan', 'camel', 'khaki'],
        'denim': ['denim', 'indigo', 'jeans'],
    }
    
    @staticmethod
    def get_dominant_color(image: Image.Image) -> str:
        """
        Определяет доминирующий цвет одежды.
        Игнорирует белый фон.
        """
        
        # Конвертируем в RGB
        img = image.convert('RGB')
        
        # Уменьшаем для скорости
        img_small = img.resize((100, 100))
        
        # Получаем все пиксели
        pixels = np.array(img_small).reshape(-1, 3)
        
        # Фильтруем белый фон (игнорируем очень светлые пиксели)
        brightness = pixels.mean(axis=1)
        mask = brightness < 240  # исключаем фон
        filtered_pixels = pixels[mask]
        
        if len(filtered_pixels) == 0:
            filtered_pixels = pixels
        
        # Находим средний цвет
        avg_color = filtered_pixels.mean(axis=0).astype(int)
        
        # Находим ближайший именованный цвет
        color_name = ColorAnalyzer._find_closest_color(avg_color)
        
        return color_name
    
    @staticmethod
    def _find_closest_color(rgb: np.ndarray) -> str:
        """Находит ближайший именованный цвет по RGB."""
        
        r, g, b = rgb
        
        # Простая эвристика
        if r < 50 and g < 50 and b < 50:
            return "black"
        if r > 200 and g > 200 and b > 200:
            return "white"
        
        # Определяем доминирующий канал
        max_val = max(r, g, b)
        
        if max_val == r and r > g + 30 and r > b + 30:
            return "red"
        if max_val == g and g > r + 30 and g > b + 30:
            return "green"
        if max_val == b and b > r + 30 and b > g + 30:
            return "blue"
        
        # Если цвета близки
        if abs(r - g) < 30 and abs(g - b) < 30:
            if r < 100:
                return "gray"
            if r > 200:
                return "white"
            return "gray"
        
        # Дополнительные проверки
        if r > 150 and g > 100 and b < 100:
            return "orange"
        if r > 150 and g < 100 and b > 150:
            return "purple"
        if r > 200 and g > 100 and b > 100:
            return "pink"
        
        return "dark"  # fallback
    
    @staticmethod
    def get_detailed_description(image: Image.Image) -> dict:
        """Возвращает детальное описание цвета с RGB значениями."""
        
        img = image.convert('RGB')
        img_small = img.resize((100, 100))
        pixels = np.array(img_small).reshape(-1, 3)
        
        # Более агрессивная фильтрация фона
        # Исключаем белый (R>240, G>240, B>240) и очень темный
        mask = (pixels[:, 0] < 240) | (pixels[:, 1] < 240) | (pixels[:, 2] < 240)
        mask &= (pixels[:, 0] > 10) | (pixels[:, 1] > 10) | (pixels[:, 2] > 10)
        filtered = pixels[mask]
        
        if len(filtered) > 50:
            avg = filtered.mean(axis=0).astype(int)
        else:
            avg = pixels.mean(axis=0).astype(int)
        
        r, g, b = avg
        
        # Точное определение цвета с RGB значениями в промпт
        color_name = ColorAnalyzer._find_closest_color(avg)
        
        # Добавляем точные RGB значения для максимальной точности
        return {
            "name": color_name,
            "rgb": f"RGB({r},{g},{b})",
            "rgb_values": (r, g, b),
            "description": color_name,
            "prompt_color": f"{color_name} (exact RGB: {r},{g},{b})",
        }