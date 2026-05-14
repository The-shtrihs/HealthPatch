.PHONY: dev lint test migrate docker-up

dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
migrate:
	docker compose exec api uv run alembic upgrade head

create-migration:
	docker compose exec api uv run alembic revision --autogenerate -m "$(name)"

lint:
	docker compose exec api uv run ruff check .
	docker compose exec api uv run ruff format .

docker-up:
	docker compose up -d

test:
	docker compose -f docker-compose_test.yml run test uv run pytest -v --tb=short tests/

test-unit:
	docker compose exec api uv run pytest -v --tb=short tests/unit/
	