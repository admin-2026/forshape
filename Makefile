.PHONY: install format lint fix

install:
	pip install ruff

format:
	ruff format .
	ruff check --fix .

lint:
	ruff check .

fix:
	ruff check --fix --unsafe-fixes .
