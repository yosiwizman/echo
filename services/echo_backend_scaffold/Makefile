.PHONY: install run lint typecheck test format clean all

# Default Python command
PYTHON ?= python

# Install dependencies
install:
	$(PYTHON) -m pip install -r requirements.txt

# Run the development server
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run linting with ruff
lint:
	ruff check .

# Run type checking with mypy
typecheck:
	mypy app

# Run tests with pytest
test:
	pytest

# Run tests with coverage
test-cov:
	pytest --cov=app --cov-report=html --cov-report=term

# Format code with ruff
format:
	ruff format .
	ruff check --fix .

# Clean up generated files
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run all checks
all: lint typecheck test
