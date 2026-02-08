.PHONY: install format lint fix readme

install:
	pip install ruff grip

readme:
	grip README.md

format:
	ruff format .
	ruff check --fix .

lint:
	ruff check .

fix:
	ruff check --fix --unsafe-fixes .
