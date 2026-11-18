# py-image-batch

> Batch image resize, watermark and optimization with HTML report.

[![CI](https://github.com/dblzroch/py-image-batch/actions/workflows/ci.yml/badge.svg)](https://github.com/dblzroch/py-image-batch/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](pyproject.toml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Process a folder of images in parallel: resize to a max dimension, add a watermark,
and save optimized copies. Generates an HTML report with size savings per file.

## Quickstart

```bash
# Clone
git clone https://github.com/dblzroch/py-image-batch.git
cd py-image-batch

# Install (uv)
uv sync --dev

# Resize and optimize all images in a folder
uv run image-batch process input/ output/ --max-width 1920 --quality 85

# With watermark and 4 parallel workers
uv run image-batch process input/ output/ --watermark "© Diego" --workers 4

# Generate HTML report
uv run image-batch report report.html
```

## Commands

| Command | Description |
|---|---|
| `image-batch process <in> <out> [--max-width] [--max-height] [--quality] [--watermark] [--workers]` | Process images in parallel |
| `image-batch report <file.html>` | Write HTML report of last run |

## How it works

- **CLI**: [Typer](https://typer.tiangolo.com/) commands.
- **Images**: [Pillow](https://python-pillow.org/) for resize, watermark and optimization.
- **Parallelism**: `ProcessPoolExecutor` across CPU cores.
- **Report**: HTML with before/after size and savings per file.
- **Tests**: `pytest` with coverage gate at 80%.
- **CI**: GitHub Actions runs ruff, mypy and pytest on every push/PR.

## Tests & quality

```bash
make test      # pytest with coverage
make lint      # ruff + mypy
make fmt       # ruff format
```

## License

MIT
