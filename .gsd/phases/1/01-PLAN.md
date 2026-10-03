---
phase: 1
plan: 1
wave: 1
depends_on: []
files_modified:
  - docs/synopsis.pdf
  - pyproject.toml
  - Makefile
  - .gitignore
  - src/prescriptxai/__init__.py
  - src/prescriptxai/config.py
  - configs/default.yaml
autonomous: true
user_setup: []
must_haves:
  truths:
    - The project installs as a Python 3.11+ src-layout package with pinned runtime and dev dependencies.
    - Configuration is loaded from YAML, validated, and contains research thresholds rather than embedded results.
    - Raw/processed data and artifacts are ignored while required .gitkeep files remain trackable.
  artifacts:
    - docs/synopsis.pdf
    - pyproject.toml
    - configs/default.yaml
    - src/prescriptxai/config.py
---

# Plan 1.1: Package foundation

## Objective

Create an installable, lintable package foundation and preserve the user-supplied synopsis at its required repository path.

## Context

- `.gsd/SPEC.md`
- `docs/synopsis.pdf`
- `PROJECT_RULES.md`

## Tasks

<task type="auto">
  <name>Create package metadata and configuration loader</name>
  <files>pyproject.toml, Makefile, .gitignore, configs/default.yaml, src/prescriptxai/__init__.py, src/prescriptxai/config.py</files>
  <action>Define pinned project dependencies and tool configuration, package entry points, YAML configuration schema/loading, and stable defaults. Keep every operational threshold configurable. AVOID inventing benchmark outcomes or implicit default paths that write into source control. USE validation that rejects malformed and out-of-range configuration.</action>
  <verify>uv run ruff check .; uv run mypy src; uv run pytest --cov=prescriptxai</verify>
  <done>The package installs from src layout; configuration loads valid defaults and rejects malformed values with typed errors.</done>
</task>

<task type="auto">
  <name>Preserve synopsis and establish ignored data directories</name>
  <files>docs/synopsis.pdf, data/raw/.gitkeep, data/processed/.gitkeep, artifacts/.gitkeep</files>
  <action>Copy the provided PDF byte-for-byte to `docs/synopsis.pdf`; create the required data/artifact folders and ignore their contents while retaining .gitkeep. AVOID editing or paraphrasing the source PDF.</action>
  <verify>Compare source and destination SHA-256 hashes; inspect `git check-ignore` behavior after repository initialization.</verify>
  <done>The required source document is present unchanged and data/artifact directories are ready without tracking generated data.</done>
</task>

## Must-Haves

- [ ] The source synopsis is preserved unchanged.
- [ ] Package metadata and YAML config are valid and tested.
- [ ] Data and artifact ignore behavior preserves only placeholders.
