import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from PIL import Image

from config import config

logger = logging.getLogger(__name__)


@dataclass
class ArticleData:
    article_id: str
    gender: str
    category: str
    color: str
    brand: str
    group: str
    subcategory: str
    name: str
    description: str
    images: Dict[str, Path] = field(default_factory=dict)  # {angle: path}


class DataLoader:
    """
    Загрузчик данных для структуры:
    Предметные фото/
    ├── Артикул1/
    │   ├── Артикул1_6.jpg  -> front
    │   ├── Артикул1_7.jpg  -> back
    │   └── Артикул1_8.jpg  -> detail
    └── Артикул2/...
    """
    
    # Маппинг суффиксов на углы съемки
    SUFFIX_TO_ANGLE = {
        "6": "front",
        "7": "back",
        "8": "detail",
    }
    
    # Маппинг группы из Excel в категорию (для совместимости)
    GROUP_TO_CATEGORY = {
        "Джинсы": "Джинсы",
        "Футболки и поло": "Футболки",
        "Верхняя одежда": "Верхняя одежда",
        "Свитшоты и худи": "Свитшоты и худи",
        "Брюки": "Брюки",
        "Рубашки": "Рубашки",
        "Юбки": "Юбки",
        "Платья": "Платья",
    }
    
    def __init__(
        self,
        root_folder: str = "Предметные фото",
        excel_file: str = config.EXCEL_FILE,
        sheet_name: int = 0,
    ):
        self.root_folder = Path(root_folder)
        self.excel_file = Path(excel_file)
        self.sheet_name = sheet_name
        self._validate()
    
    def _validate(self) -> None:
        if not self.root_folder.exists():
            raise FileNotFoundError(f"Root folder not found: {self.root_folder}")
        if not self.excel_file.exists():
            raise FileNotFoundError(f"Excel file not found: {self.excel_file}")
    
    def load_excel(self) -> pd.DataFrame:
        """Загружает Excel и возвращает DataFrame с данными артикулов."""
        df = pd.read_excel(self.excel_file, sheet_name=self.sheet_name, engine="openpyxl")
        
        # Сохраняем оригинальные названия колонок
        original_columns = list(df.columns)
        
        # Нормализуем названия колонок
        df.columns = [str(c).strip().replace(" ", "_") for c in df.columns]
        
        logger.info(f"Excel columns: {list(df.columns)}")
        
        # ============================================================
        # 1. Поиск колонки с артикулом
        # ============================================================
        article_col = None
        for col in ["Артикул", "Article", "article", "артикул"]:
            if col in df.columns:
                article_col = col
                break
        
        if not article_col:
            raise ValueError(f"Article column not found. Available: {list(df.columns)}")
        
        # ============================================================
        # 2. Поиск колонки с полом (используем "пол NAV")
        # ============================================================
        gender_col = None
        # Прямое соответствие
        if "пол_NAV" in df.columns:
            gender_col = "пол_NAV"
        elif "пол NAV" in df.columns:
            gender_col = "пол NAV"
        elif "Пол_для_сайта" in df.columns:
            gender_col = "Пол_для_сайта"
        elif "gender" in df.columns:
            gender_col = "gender"
        
        # ============================================================
        # 3. Поиск колонки с категорией (используем "Подгруппа" или "Наименование")
        # ============================================================
        category_col = None
        # Сначала пробуем Подгруппа (там более точная категория)
        if "Подгруппа" in df.columns:
            category_col = "Подгруппа"
        elif "подгруппа" in df.columns:
            category_col = "подгруппа"
        # Затем Наименование
        elif "Наименование" in df.columns:
            category_col = "Наименование"
        elif "наименование" in df.columns:
            category_col = "наименование"
        # Затем Группа
        elif "Группа" in df.columns:
            category_col = "Группа"
        
        # ============================================================
        # 4. Поиск колонки с цветом
        # ============================================================
        color_col = None
        if "цвет_NAV" in df.columns:
            color_col = "цвет_NAV"
        elif "цвет NAV" in df.columns:
            color_col = "цвет NAV"
        elif "Цвет_для_Сайта" in df.columns:
            color_col = "Цвет_для_Сайта"
        
        # ============================================================
        # 5. Поиск колонки с брендом
        # ============================================================
        brand_col = None
        if "бренд_NAV" in df.columns:
            brand_col = "бренд_NAV"
        elif "бренд NAV" in df.columns:
            brand_col = "бренд NAV"
        
        # ============================================================
        # Очистка данных
        # ============================================================
        df[article_col] = df[article_col].astype(str).str.strip()
        df = df[df[article_col].notna()]
        df = df[df[article_col] != "nan"]
        df = df[df[article_col] != ""]
        
        # ============================================================
        # Нормализуем пол (прямое преобразование)
        # ============================================================
        if gender_col:
            # Берем значения как есть
            df["gender_raw"] = df[gender_col].astype(str).str.strip()
            
            # Прямой маппинг
            def map_gender(val):
                val_lower = val.lower()
                if val_lower in ["женский", "female", "ж", "жен"]:
                    return "female"
                elif val_lower in ["мужской", "male", "м", "муж"]:
                    return "male"
                else:
                    logger.warning(f"Unknown gender value: '{val}', defaulting to male")
                    return "male"
            
            df["gender"] = df["gender_raw"].apply(map_gender)
            logger.info(f"Gender distribution: {df['gender'].value_counts().to_dict()}")
        else:
            logger.warning("Gender column not found, using 'male'")
            df["gender"] = "male"
        
        # ============================================================
        # Нормализуем категорию
        # ============================================================
        if category_col:
            df["category_raw"] = df[category_col].astype(str).str.strip()
            
            # Прямой маппинг категорий
            def map_category(val):
                val_lower = val.lower()
                
                # Джинсы
                if "джинс" in val_lower:
                    return "Джинсы"
                # Юбки
                if "юбк" in val_lower:
                    return "Юбки"
                # Платья
                if "плать" in val_lower or "сарафан" in val_lower:
                    return "Платья"
                # Футболки
                if "футболк" in val_lower or "поло" in val_lower:
                    return "Футболки"
                # Свитшоты и худи
                if "свитшот" in val_lower or "худи" in val_lower or "толстовк" in val_lower:
                    return "Свитшоты и худи"
                # Брюки
                if "брюк" in val_lower:
                    return "Брюки"
                # Рубашки
                if "рубашк" in val_lower:
                    return "Рубашки"
                # Верхняя одежда
                if "куртк" in val_lower or "пальт" in val_lower or "пуховик" in val_lower:
                    return "Верхняя одежда"
                
                # Если не определили, возвращаем как есть
                return val
            
            df["category"] = df["category_raw"].apply(map_category)
            logger.info(f"Category distribution: {df['category'].value_counts().to_dict()}")
        else:
            logger.warning("Category column not found, using 'Джинсы'")
            df["category"] = "Джинсы"
        
        # ============================================================
        # Нормализуем цвет
        # ============================================================
        if color_col:
            df["color"] = df[color_col].astype(str).str.lower().str.strip()
            df["color"] = df["color"].replace(["nan", "none", "", "нет"], "black")
            logger.info(f"Color samples: {df['color'].value_counts().head(10).to_dict()}")
        else:
            df["color"] = "black"
        
        # ============================================================
        # Бренд
        # ============================================================
        if brand_col:
            df["brand"] = df[brand_col].astype(str).str.lower().str.strip()
            df["brand"] = df["brand"].replace(["nan", "none", ""], "unknown")
        else:
            df["brand"] = "unknown"
        
        # ============================================================
        # Остальные поля
        # ============================================================
        # Группа
        if "Группа" in df.columns:
            df["group"] = df["Группа"].astype(str)
        else:
            df["group"] = ""
        
        # Подгруппа
        if "Подгруппа" in df.columns:
            df["subcategory"] = df["Подгруппа"].astype(str)
        else:
            df["subcategory"] = ""
        
        # Наименование
        if "Наименование" in df.columns:
            df["name"] = df["Наименование"].astype(str)
        else:
            df["name"] = ""
        
        # Описание
        if "Описание_Товара" in df.columns:
            df["description"] = df["Описание_Товара"].astype(str)
        else:
            df["description"] = ""
        
        # Убираем дубликаты
        df = df.drop_duplicates(subset=[article_col])
        
        logger.info(f"✅ Loaded {len(df)} articles from Excel")
        
        # Выводим пример для проверки
        sample = df[[article_col, 'category', 'gender', 'color']].head(5)
        logger.info(f"\nSample data:\n{sample.to_string()}")
        
        return df[[article_col, "category", "gender", "color", "brand", "group", "subcategory", "name", "description"]]
    
    def discover_articles(self) -> Dict[str, Dict]:
        """Обходит папки и находит артикулы с изображениями."""
        articles = {}
        
        for article_dir in self.root_folder.iterdir():
            if not article_dir.is_dir():
                continue
            
            article_id = article_dir.name
            images = self._scan_article_images(article_dir, article_id)
            
            if images:
                articles[article_id] = {
                    'images': images,
                }
                logger.debug(f"Found article {article_id}: {list(images.keys())}")
        
        logger.info(f"✅ Discovered {len(articles)} articles with images")
        return articles
    
    def _scan_article_images(self, article_dir: Path, article_id: str) -> Dict[str, Path]:
        """
        Сканирует папку артикула и возвращает словарь {angle: path}.
        Ищет файлы: {article_id}_6.jpg (front), {article_id}_7.jpg (back)
        detail НЕ ищет, он будет создан автоматически из front.
        """
        images = {}
        
        # Ищем только файлы с суффиксами 6 и 7 (front и back)
        for suffix in ["6", "7"]:
            angle = self.SUFFIX_TO_ANGLE.get(suffix)
            if not angle:
                continue
            
            for ext in config.SUPPORTED_FORMATS:
                filename = f"{article_id}_{suffix}{ext}"
                file_path = article_dir / filename
                
                if file_path.exists():
                    images[angle] = file_path
                    logger.debug(f"  Found {angle}: {filename}")
                    break
        
        # detail будет создан автоматически из front (добавляем виртуальный угол)
        # даже если физического файла нет, мы будем генерировать detail
        if "front" in images:
            pass
        
        return images
    
    def load_all(self) -> List[ArticleData]:
        """Загружает все артикулы."""
        
        df = self.load_excel()
        articles_fs = self.discover_articles()
        
        articles = []
        
        for article_id, fs_data in articles_fs.items():
            # Ищем в Excel
            excel_row = df[df.iloc[:, 0] == article_id]
            
            if excel_row.empty and "_" in article_id:
                base_article = article_id.split("_")[0]
                excel_row = df[df.iloc[:, 0].str.startswith(base_article)]
            
            if excel_row.empty:
                logger.warning(f"Article {article_id} not found in Excel, using defaults")
                gender = "male"
                category = "Джинсы"
                color = "black"
                brand = "unknown"
                group = ""
                subcategory = ""
                name = ""
                description = ""
            else:
                row = excel_row.iloc[0]
                gender = row.get("gender", "male")
                category = row.get("category", "Джинсы")
                color = row.get("color", "black")
                brand = row.get("brand", "unknown")
                group = row.get("group", "")
                subcategory = row.get("subcategory", "")
                name = row.get("name", "")
                description = row.get("description", "")
            
            articles.append(ArticleData(
                article_id=article_id,
                gender=gender,
                category=category,
                color=color,
                brand=brand,
                group=group,
                subcategory=subcategory,
                name=name,
                description=description,
                images=fs_data['images'],
            ))
            
            logger.info(f"📦 Loaded: {article_id} | {category} | {color} | {gender} | angles: {list(fs_data['images'].keys())}")
        
        return articles
    
    @staticmethod
    def open_image(path: Path) -> Image.Image:
        return Image.open(path).convert("RGB")