"""CLI entry point for py-image-batch."""

import logging
from pathlib import Path
from typing import Annotated

import typer

from py_image_batch.models import BatchResult
from py_image_batch.pipeline import run_pipeline

app = typer.Typer(
    help="Batch image resize, watermark and optimization with HTML report."
)
console = typer.echo
logger = logging.getLogger(__name__)

_LAST_RESULT: BatchResult | None = None

_INPUT_ARG = typer.Argument(..., help="Folder with source images.")
_OUTPUT_ARG = typer.Argument(..., help="Folder for processed images.")
_REPORT_ARG = typer.Argument(..., help="Output HTML report path.")


@app.command()
def process(
    input_folder: Path = _INPUT_ARG,
    output_folder: Path = _OUTPUT_ARG,
    max_width: Annotated[
        int | None, typer.Option("--max-width", "-w", help="Max width in pixels.")
    ] = None,
    max_height: Annotated[
        int | None, typer.Option("--max-height", "-H", help="Max height in pixels.")
    ] = None,
    quality: int = typer.Option(85, "--quality", "-q", help="JPEG quality (1-100)."),
    watermark: str | None = typer.Option(
        None, "--watermark", "-m", help="Watermark text."
    ),
    workers: int = typer.Option(
        1, "--workers", "-j", help="Parallel workers (1 = serial)."
    ),
) -> None:
    """Process images in parallel: resize, optional watermark, optimize."""
    global _LAST_RESULT

    if not input_folder.is_dir():
        console(f"[red]Not a directory:[/red] {input_folder}")
        raise typer.Exit(code=1)

    result = run_pipeline(
        input_folder,
        output_folder,
        max_width=max_width,
        max_height=max_height,
        quality=quality,
        watermark=watermark,
        workers=workers,
    )
    _LAST_RESULT = result

    console(f"Processed {result.processed}/{result.total} images")
    console(f"Errors: {result.errors}")
    console(
        f"Size: {result.bytes_before_total:,} -> {result.bytes_after_total:,} bytes"
    )
    console(f"Savings: {result.total_savings_percent:.1f}%")


@app.command()
def report(
    path: Path = _REPORT_ARG,
) -> None:
    """Write an HTML report of the last run."""
    global _LAST_RESULT

    if _LAST_RESULT is None:
        console("[red]No batch run yet.[/red] Run 'process' first.")
        raise typer.Exit(code=1)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_LAST_RESULT.to_html(), encoding="utf-8")
    console(f"Report written to {path}")


if __name__ == "__main__":
    app()
