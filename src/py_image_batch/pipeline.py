"""Image processing pipeline: resize, watermark, optimize, report."""

import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from py_image_batch.models import BatchResult, ProcessingResult

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def _process_single(
    source: Path,
    destination: Path,
    max_width: int | None,
    max_height: int | None,
    quality: int,
    watermark: str | None,
) -> ProcessingResult:
    """Resize, optionally watermark, and save a single image."""
    try:
        with Image.open(source) as img:
            bytes_before = source.stat().st_size
            rgb_img = img.convert("RGB")

            # Resize keeping aspect ratio
            if max_width or max_height:
                rgb_img.thumbnail(
                    (max_width or rgb_img.width, max_height or rgb_img.height)
                )

            # Watermark
            if watermark:
                draw = ImageDraw.Draw(rgb_img)
                try:
                    font = ImageFont.load_default()
                except Exception:
                    font = None
                draw.text((10, 10), watermark, fill=(255, 255, 255, 128), font=font)

            destination.parent.mkdir(parents=True, exist_ok=True)
            rgb_img.save(destination, quality=quality, optimize=True)
            bytes_after = destination.stat().st_size

            return ProcessingResult(
                source=source,
                destination=destination,
                status="ok",
                bytes_before=bytes_before,
                bytes_after=bytes_after,
            )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to process %s", source)
        return ProcessingResult(
            source=source,
            destination=destination,
            status="error",
            error=str(exc),
        )


def run_pipeline(
    input_folder: Path,
    output_folder: Path,
    max_width: int | None = None,
    max_height: int | None = None,
    quality: int = 85,
    watermark: str | None = None,
    workers: int = 1,
) -> BatchResult:
    """Process all images in ``input_folder`` and write results to ``output_folder``.

    Uses ``ProcessPoolExecutor`` when ``workers > 1`` for parallel execution.
    """
    input_folder = input_folder.resolve()
    output_folder = output_folder.resolve()

    images = sorted(
        p
        for p in input_folder.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    result = BatchResult(
        input_folder=input_folder, output_folder=output_folder, total=len(images)
    )

    if not images:
        return result

    tasks = [
        (
            img,
            output_folder / img.relative_to(input_folder),
            max_width,
            max_height,
            quality,
            watermark,
        )
        for img in images
    ]

    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(_process_single, *task) for task in tasks]
            for future in as_completed(futures):
                single = future.result()
                result.results.append(single)
                if single.status == "ok":
                    result.processed += 1
                    result.bytes_before_total += single.bytes_before
                    result.bytes_after_total += single.bytes_after
                else:
                    result.errors += 1
    else:
        for task in tasks:
            single = _process_single(*task)
            result.results.append(single)
            if single.status == "ok":
                result.processed += 1
                result.bytes_before_total += single.bytes_before
                result.bytes_after_total += single.bytes_after
            else:
                result.errors += 1

    return result
