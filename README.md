# 🎯 TryOn Catalog Pipeline

> Автоматическая генерация каталожных изображений одежды на моделях в стиле Lamoda

[![CI](https://github.com/username/tryon-catalog-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/username/tryon-catalog-pipeline/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)]()

---

## 📖 О проекте

**TryOn Catalog Pipeline** превращает предметные фотографии одежды в готовые каталожные изображения на моделях в едином стиле, соответствующем стандарту Lamoda.

### Что делает пайплайн

- ✅ Одна эталонная модель для всех артикулов одного пола
- ✅ Три обязательных ракурса: **front** / **back** / **detail**
- ✅ Выходные файлы: **1524×2200 px, WebP, 300 DPI, sRGB**
- ✅ **Nano Banana 2** (Google Gemini) для высокого качества
- ✅ Автоматическая **QC-валидация** по матрице стандарта

### Зачем это нужно

Каталожная съёмка — дорого, долго и требует модели, студии и фотографа. Этот пайплайн позволяет:

- Генерировать 5–7 изображений на артикул за минуты
- Держать единый визуальный стиль для всего каталога
- Снижать долю ручной проверки до целевых 20%

---

## 🏗️ Архитектура

### Структура папок

```
Предметные фото/           models/             output_lamoda/
├── A4M10068_1HP/          ├── male_front.png  ├── A4M10068_1HP_front.webp
│   ├── ..._6.jpg    ───►  ├── male_back.png   ├── A4M10068_1HP_back.webp
│   └── ..._7.jpg          └── female_*.png    └── A4M10068_1HP_detail.webp
│                                                       ▲
└── articles.xlsx ──────────────────────────────────────┘
```

### Пайплайн

```
┌─────────────┐   ┌───────────────┐   ┌──────────────┐   ┌────────────┐   ┌──────────────┐
│ DataLoader  │──►│ ModelGenerator│──►│ GPTunnelClient│──►│ QCValidator│──►│ OutputManager│
│ (Excel+папки)│   │ (эталонные    │   │ (Nano Banana 2│   │ (стандарт  │   │ (WebP 300DPI)│
│             │   │  модели)      │   │  генерация)   │   │  Lamoda)   │   │              │
└─────────────┘   └───────────────┘   └──────────────┘   └────────────┘   └──────────────┘
```

### Компоненты

| Модуль | Назначение |
|--------|-----------|
| `DataLoader` | Читает Excel + папки, сопоставляет артикулы и ракурсы |
| `ModelGenerator` | Генерирует эталонных моделей (один раз) |
| `LamodaStyleClient` | Обёртка над GPTunnel API (Nano Banana 2) |
| `ColorAnalyzer` | Анализ цвета одежды |
| `QCValidator` | Проверка качества по матрице стандарта |
| `OutputManager` | Сохранение результатов и отчётов |

---

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- API-ключ [GPTunnel](https://gptunnel.ru)
- ~4 GB свободного места (для локальных моделей)

### Установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/username/tryon-catalog-pipeline.git
cd tryon-catalog-pipeline

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # macOS / Linux

# Для Windows:
# venv\Scripts\activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить API-ключи
cp .env.example .env
# Откройте .env и вставьте ваш ключ GPTunnel
```

### Получить API-ключ

1. Зарегистрируйтесь на [gptunnel.ru](https://gptunnel.ru)
2. Получите API-ключ в личном кабинете
3. Вставьте в `.env`:

```bash
GPTUNNEL_API_KEY=ваш_ключ_здесь
```

### Подготовка данных

**1. Excel-файл** (`articles.xlsx`) должен содержать колонки:

| Артикул | Группа | Подгруппа | Наименование | пол NAV | цвет NAV | бренд NAV |
|---------|--------|-----------|--------------|---------|----------|-----------|
| A4M10068_1HP | Джинсы | Прямые джинсы | Джинсы | Мужской | черный | K_LAGERFELD |
| A4M17072_999 | Футболки и поло | Футболки | Футболка | Мужской | черный | K_LAGERFELD |

**2. Папка `Предметные фото`** — для каждого артикула своя папка:

```
Предметные фото/
├── A4M10068_1HP/
│   ├── A4M10068_1HP_6.jpg   # front (обязательно)
│   └── A4M10068_1HP_7.jpg   # back  (обязательно)
└── A4M17072_999/
    └── A4M17072_999_6.jpg   # front (back опционально)
```

**Правила именования:**
- `{Артикул}_6.jpg` → front
- `{Артикул}_7.jpg` → back
- `detail` генерируется автоматически через API (крупный план)

### Запуск

```bash
# 1. Сгенерировать эталонные модели (только один раз)
python generate_models.py

# 2. Запустить пайплайн генерации
python run_lamoda.py
```

Или через `make`:

```bash
make install     # установить зависимости
make models      # сгенерировать модели
make generate    # запустить пайплайн
```

---

## 📁 Результаты

Готовые файлы появятся в `output_lamoda/`:

```
output_lamoda/
├── A4M10068_1HP_front.webp    # 1524×2200, 300 DPI
├── A4M10068_1HP_back.webp
├── A4M10068_1HP_detail.webp
├── A4M17072_999_front.webp
├── A4M17072_999_detail.webp
└── processing_report.txt       # отчёт о генерации
```

---

## ⚙️ Конфигурация

Все параметры в `config.py`:

| Параметр | Значение | Описание |
|----------|----------|----------|
| `OUTPUT_SIZE` | `(1524, 2200)` | Размер выходных изображений |
| `OUTPUT_DPI` | `300` | DPI для печати |
| `OUTPUT_FORMAT` | `"webp"` | Формат сохранения |
| `OUTPUT_QUALITY` | `95` | Качество сжатия |
| `API_STEPS` | `40` | Шагов генерации |
| `API_CFG_SCALE` | `7.5` | Точность следования промпту |
| `IMAGE_SIZE` | `(1024, 1024)` | Промежуточный размер для моделей |

### Переменные окружения (`.env`)

```bash
GPTUNNEL_API_KEY=...    # обязательно
DEVICE=cpu              # cpu / cuda / mps
```

## 📊 QC-валидация

Проект включает QC-матрицу по [стандарту Lamoda](docs/qc-standard.md).

### Уровни проверки

| Уровень | Условие | Решение |
|---------|---------|---------|
| **Auto-pass** | Все метрики выше порога, нет риск-флагов | `AUTO_PASS` |
| **Manual review** | Пограничные случаи или риск-флаги | `MANUAL_REVIEW` |
| **Auto-fail** | Критичные артефакты, метрики ниже hard-fail | `AUTO_FAIL` |

### Метрики

- `silhouette_score` — корректность силуэта
- `fit_score` — посадка одежды
- `texture_score` — точность фактуры
- `detail_integrity_score` — целостность деталей
- `lifestyle_score` — коммерческая пригодность
- `qc_ocr_confidence` — точность текста/принта

### Бизнес-флаги (маршрутизация в ручную проверку)

- Прозрачная ткань
- Мелкий принт
- Текст / логотип
- Сложная фурнитура

---

## 🗺️ Roadmap

- [x] Базовая генерация front/back/detail
- [x] Единые эталонные модели
- [x] QC-валидация по стандарту
- [x] Выходные файлы 300 DPI
- [ ] Мультиагентная архитектура (LangGraph)
- [ ] Веб-интерфейс для ручной проверки
- [ ] Поддержка lifestyle-кадров
- [ ] Интеграция с n8n
- [ ] Мультиязычные промпты

---

## ⭐ Поддержите проект

Если пайплайн оказался полезен — поставьте звезду на GitHub! Это помогает проекту расти.

[![Star History Chart](https://api.star-history.com/svg?repos=username/tryon-catalog-pipeline&type=Date)](https://star-history.com/#username/tryon-catalog-pipeline&Date)