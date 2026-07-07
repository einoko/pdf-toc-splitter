.PHONY: format test

format:
	uv run ruff check --select I --fix .
	uv run ruff format .

test:
	uv run python -m unittest
