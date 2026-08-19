venv:
	# Install https://github.com/astral-sh/uv on macOS and Linux:
	# $ curl -LsSf https://astral.sh/uv/install.sh | sh
	# Other recommended libraries, add with `uv add <library>`:
	# tenacity, joblib, jupyterlab, litellm, datasets, pytorch, fastapi, uvicorn, rich
	uv sync --all-extras --all-groups
	uv pip install -e .

clean:
	rm -rf .venv

download:
	# Download source files
	uv run python scripts/fetch_sources.py

build:
	# Build all datasets
	uv run python -m builders.build_eva_lines
	uv run python -m builders.build_metadata
	uv run python -m builders.build_mismatch_index

notebook:
	uv run jupyter lab

test:
	uv run pytest -vv --capture=no --no-cov tests
