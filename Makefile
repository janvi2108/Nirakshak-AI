.PHONY: up down build logs test migrate shell ps clean

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose up -d --build

logs:
	docker-compose logs -f fastapi

test:
	docker-compose exec fastapi pytest tests/ -v

migrate:
	docker-compose exec fastapi alembic upgrade head

shell:
	docker-compose exec fastapi bash

ps:
	docker-compose ps

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

train-complaints:
	python ml/training/train_complaint.py

train-fraud:
	python ml/training/train_fraud.py

train-delay:
	python ml/training/train_delay.py

ingest-docs:
	python ml/pipelines/ingest_docs.py
