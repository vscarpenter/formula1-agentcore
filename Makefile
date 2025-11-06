.PHONY: help install test lint format clean deploy destroy lambda-layer uv-install

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

uv-install:  ## Install uv if not present
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }

install: uv-install  ## Install dependencies with uv
	uv pip install -e ".[dev,infra]"

test:  ## Run tests with coverage
	pytest --cov=src --cov=cli --cov-report=term-missing --cov-report=html

lint:  ## Run linting checks
	ruff check .
	mypy src cli

format:  ## Format code with black
	black .
	ruff check --fix .

lambda-layer:  ## Build Lambda layer with Linux-compatible dependencies
	@echo "Creating Lambda layer for AWS Lambda (Linux)..."
	@rm -rf lambda_layer
	@mkdir -p lambda_layer/python/lib/python3.11/site-packages
	python3.11 -m pip install --platform manylinux2014_x86_64 --only-binary=:all: \
		boto3 botocore requests pydantic python-dotenv \
		--target lambda_layer/python/lib/python3.11/site-packages/ \
		--upgrade 2>&1 | grep -v "dependency conflicts" || true
	@echo "✅ Lambda layer created with Linux binaries at: lambda_layer/"
	@du -sh lambda_layer
	@find lambda_layer -name "*.so" | head -3 | xargs -I {} sh -c 'echo "Sample binary: {}"; file {}'

export-schemas:  ## Export OpenAPI schemas for agent creation
	python -m cli.main export-schemas

deploy:  ## Deploy infrastructure with CDK
	cd infrastructure && cdk deploy

destroy:  ## Destroy infrastructure
	cd infrastructure && cdk destroy

diff:  ## Show CDK diff
	cd infrastructure && cdk diff

synth:  ## Synthesize CDK stack
	cd infrastructure && cdk synth

clean:  ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf lambda_layer
	rm -rf infrastructure/cdk.out

calendar:  ## Show F1 calendar
	f1-agent calendar

next-race:  ## Show next race
	f1-agent next-race

setup-dev: uv-install  ## Complete development setup with uv
	@echo "Setting up development environment with uv..."
	uv venv
	@echo "Virtual environment created. Activate with: source .venv/bin/activate"
	@echo "Then run: make install && make lambda-layer"
