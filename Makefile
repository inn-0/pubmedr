.PHONY: install install-dev test run

# Default install using pip and pyproject.toml   -   Type:   `make install`
install:
	uv sync
	uv pip install -e .

# Development dependencies   -   Type:   `make install-dev`
install-dev:
	uv sync --all-extras
	uv pip install -e .

# Run tests with pytest   -   Type:   `make test`
test:
	uv run pytest --cov=. --cov-fail-under=70

# Run the application   -   Type:   `make run`
run:
	uv run streamlit run ./src/pubmedr/streamlit_main.py
