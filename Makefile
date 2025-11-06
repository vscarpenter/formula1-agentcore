.PHONY: help install test lint format clean deploy destroy lambda-layer

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -e ".[dev,infra]"

test:  ## Run tests with coverage
	pytest --cov=src --cov=cli --cov-report=term-missing --cov-report=html

lint:  ## Run linting checks
	ruff check .
	mypy src cli

format:  ## Format code with black
	black .
	ruff check --fix .

lambda-layer:  ## Build Lambda layer with dependencies
	@echo "Creating Lambda layer..."
	@rm -rf lambda_layer
	@mkdir -p lambda_layer/python/lib/python3.11/site-packages
	pip install boto3 botocore requests pydantic python-dotenv \
		-t lambda_layer/python/lib/python3.11/site-packages/ \
		--upgrade
	@echo "Layer created at: lambda_layer/"
	@du -sh lambda_layer

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

setup-dev:  ## Complete development setup
	@echo "Setting up development environment..."
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"
	@echo "Then run: make install && make lambda-layer"
