.PHONY: install run mock test lint format typecheck clean

install:
	uv sync --all-extras

run:
	uv run aegis run

mock:
	uv run aegis mock-target --port 9000 --mode vulnerable

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check aegis/ tests/

format:
	uv run ruff format aegis/ tests/

typecheck:
	uv run mypy aegis/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache dist build
