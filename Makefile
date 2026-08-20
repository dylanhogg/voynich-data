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

corpora:
	# Fetch and verify the reference corpora used as baselines (plan 001, Phase 0)
	uv run python scripts/fetch_corpora.py

phase0:
	# Verify inputs, summarise strata + corpora, write output/translation/phase0_manifest.json
	uv run python -m translations.phase0

analyse1:
	# Phase 1 analysis suite -> reports/phase1/ (~100s; fails if the landmark gate is red)
	uv run python -m translations.phase1

decipher:
	# Phase 2 hypothesis search -> reports/phase2/ (budgeted; ~40 min at current grids)
	uv run python -m translations.phase2

analyse2:
	# Phase 3 gap remediation + analysis round 2 + re-scoring -> reports/phase3/
	# (budgeted; ~2 h at current grids; --analysis-only skips the re-scoring)
	uv run python -m translations.phase3

calibrate:
	# Phase 4 confidence calibration on synthetic ciphertexts -> output/translation/calibration.json
	# (blind key search per hypothesis; ~2 min, ceiling 4 h)
	uv run python -m translations.calibrate

translate:
	# Phase 4 translation pipeline -> output/translation/ + reports/translation/ (~35 s)
	uv run python -m translations.phase4
	uv run python -m validators.validate_translation_outputs

audit:
	# Phase 5 adversarial self-audit -> reports/translation/strengths_weaknesses.md
	# (re-searches every keyed hypothesis under fresh seeds and perturbed
	#  training subsets; budgeted, ~1 h at current settings, ceiling 2 h)
	uv run python -m translations.phase5

viewer:
	# Render the two browser-loadable HTML views -> output/viewer/ (~5 s)
	# `uv run python -m viewer.iiif` refreshes the Beinecke folio-image map.
	uv run python -m viewer.build

quick-analysis:
	uv run python scripts/quick_analysis.py

deep-analysis:
	uv run python scripts/deep_analysis.py

notebook:
	uv run jupyter lab

test:
	uv run pytest -vv --capture=no --no-cov tests

agent-skills-symlink:
	ln -s AGENTS.md CLAUDE.md
	ln -s ../.agents/skills ./.claude/skills
	ln -s ../.agents/skills ./.codex/skills

agent-skills-verify:
	ls -la CLAUDE.md
	ls -la ./.claude/skills ./.codex/skills
