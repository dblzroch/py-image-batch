"""Tests for py-image-batch models, pipeline and CLI."""

from pathlib import Path

import pytest
from PIL import Image
from typer.testing import CliRunner

from py_image_batch.cli import app
from py_image_batch.models import BatchResult, ProcessingResult
from py_image_batch.pipeline import run_pipeline


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------
def test_processing_result_savings():
    r = ProcessingResult(
        source=Path("a.jpg"),
        destination=Path("b.jpg"),
        status="ok",
        bytes_before=1000,
        bytes_after=700,
    )
    assert r.savings == 300
    assert r.savings_percent == 30.0


def test_batch_result_totals():
    result = BatchResult(
        input_folder=Path("in"),
        output_folder=Path("out"),
        total=3,
    )
    result.results = [
        ProcessingResult(Path("a.jpg"), Path("out/a.jpg"), "ok", 1000, 700),
        ProcessingResult(Path("b.jpg"), Path("out/b.jpg"), "ok", 500, 400),
        ProcessingResult(
            Path("c.jpg"), Path("out/c.jpg"), "error", 300, 0, error="boom"
        ),
    ]
    result.processed = 2
    result.errors = 1
    result.bytes_before_total = 1800
    result.bytes_after_total = 1100
    assert result.total == 3
    assert result.total_savings == 700
    assert result.total_savings_percent == pytest.approx(38.89, rel=1e-2)


# ------------------------------------------------------------------
# Pipeline
# ------------------------------------------------------------------
def _make_images(folder: Path, names: list[str]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        img = Image.new("RGB", (200, 100), color="red")
        img.save(folder / name, quality=85)


def test_pipeline_serial(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    _make_images(src, ["a.jpg", "b.png"])

    result = run_pipeline(src, dst, max_width=100, quality=80, workers=1)

    assert result.total == 2
    assert result.processed == 2
    assert result.errors == 0
    assert (dst / "a.jpg").exists()
    assert (dst / "b.png").exists()


def test_pipeline_parallel(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    _make_images(src, ["a.jpg", "b.jpg", "c.jpg"])

    result = run_pipeline(src, dst, max_width=50, workers=2)

    assert result.total == 3
    assert result.processed == 3
    assert result.errors == 0


def test_pipeline_skips_non_images(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "readme.txt").write_text("not an image")

    result = run_pipeline(src, dst, workers=1)

    assert result.total == 0
    assert result.processed == 0


def test_pipeline_empty_folder(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()

    result = run_pipeline(src, dst, workers=1)

    assert result.total == 0
    assert result.processed == 0


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------
def test_cli_process(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    _make_images(src, ["a.jpg"])

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["process", str(src), str(dst), "--max-width", "100", "--quality", "80"],
    )
    assert result.exit_code == 0
    assert "Processed" in result.output


def test_cli_process_not_a_directory(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        app, ["process", str(tmp_path / "nope"), str(tmp_path / "out")]
    )
    assert result.exit_code == 1


def test_cli_report_no_run(tmp_path):
    import py_image_batch.cli as cli_mod

    cli_mod._LAST_RESULT = None
    runner = CliRunner()
    result = runner.invoke(app, ["report", str(tmp_path / "report.html")])
    assert result.exit_code == 1


def test_cli_report_after_run(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    _make_images(src, ["a.jpg"])

    runner = CliRunner()
    runner.invoke(app, ["process", str(src), str(dst), "--max-width", "100"])

    report_path = tmp_path / "report.html"
    result = runner.invoke(app, ["report", str(report_path)])
    assert result.exit_code == 0
    assert report_path.exists()
    assert "Image Batch Report" in report_path.read_text(encoding="utf-8")
