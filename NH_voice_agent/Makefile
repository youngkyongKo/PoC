.PHONY: help install setup test clean run-pipeline run-agent run-app

help:
	@echo "NH Voice Agent - Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make setup           - Setup environment and directories"
	@echo "  make test            - Run tests"
	@echo "  make clean           - Clean temporary files"
	@echo "  make run-pipeline    - Run RAG pipeline"
	@echo "  make run-agent       - Run agent in interactive mode"
	@echo "  make run-app         - Run Streamlit app"

install:
	pip install -r requirements.txt

setup:
	@echo "Setting up environment..."
	cp -n .env.example .env || true
	mkdir -p data/raw data/processed
	@echo "✓ Setup complete"
	@echo "⚠️  Please edit .env file with your Databricks configuration"

test:
	@echo "Running tests..."
	cd 2_agent && python test_agent.py

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	find . -type f -name "*.tmp" -delete
	@echo "✓ Cleanup complete"

run-pipeline:
	@echo "Running RAG pipeline..."
	cd 1_rag_pipeline && python pipeline.py

run-agent:
	@echo "Running agent..."
	cd 2_agent && python supervisor_agent.py

run-app:
	@echo "Running Streamlit app..."
	cd 3_voice_app && streamlit run app.py

lint:
	@echo "Running linters..."
	black --check .
	flake8 .

format:
	@echo "Formatting code..."
	black .
