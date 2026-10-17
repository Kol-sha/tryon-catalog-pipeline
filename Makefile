.PHONY: install install-dev models generate test lint format clean help

help:
	@echo "TryOn Catalog Pipeline — команды:"
	@echo "  make install      — установить зависимости"
	@echo "  make install-dev  — установить + dev-зависимости"
	@echo "  make models       — сгенерировать эталонные модели"
	@echo "  make generate     — запустить пайплайн"
	@echo "  make test         — запустить тесты"
	@echo "  make lint         — проверить код"
	@echo "  make format       — отформатировать код"
	@echo "  make clean        — очистить временные файлы"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"

models:
	python generate_models.py

generate:
	python run_lamoda.py

test:
	pytest tests/ -v

lint:
	ruff check src/ config.py run_lamoda.py generate_models.py

format:
	black src/ config.py run_lamoda.py generate_models.py
	ruff check --fix src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov build dist *.egg-info
