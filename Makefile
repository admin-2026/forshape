.PHONY: install format lint

install:
	pip install ruff

format:
	ruff format .
	ruff check --fix .

lint:
	ruff check .
