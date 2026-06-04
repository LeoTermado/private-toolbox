"""Shared PyPDF2 helpers for splitting, merging and compressing PDFs.

Page-range parsing is NOT duplicated here — it is reused from
core.page_range_parser. Compression reuses core.process_utils (for the optional
external Ghostscript engine) and core.file_size (for size reporting).
"""
import os
from dataclasses import dataclass
from typing import Optional

from PyPDF2 import PdfReader, PdfWriter

from core import file_size
from core.page_range_parser import parse_single_range
from core.process_utils import ProcessResult, resolve_command, run_command


def get_page_count(input_path):
    """Return the number of pages in the PDF at input_path."""
    return len(PdfReader(input_path).pages)


def write_pages(input_path, page_indexes, output_path):
    """Write the given zero-based page indexes from input_path to output_path.

    Returns output_path. The source file is only read, never modified.
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for idx in page_indexes:
        writer.add_page(reader.pages[idx])

    with open(output_path, "wb") as out_file:
        writer.write(out_file)

    return output_path


def split_pdf_by_ranges(input_path, range_string, output_folder):
    """Create one PDF per comma-separated range part and return the output paths.

    Each part (e.g. '1-10' or '15') is named '<part>.pdf' in output_folder.
    Empty, invalid, or empty-result parts are skipped — matching the original
    PDF Splitter behavior exactly.
    """
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)

    created_files = []
    for part in range_string.split(","):
        part = part.strip()
        if not part:
            continue

        try:
            target_pages = parse_single_range(part, total_pages)
        except ValueError:
            continue

        if not target_pages:
            continue

        writer = PdfWriter()
        for page_num in target_pages:
            writer.add_page(reader.pages[page_num])

        output_filename = os.path.join(output_folder, f"{part}.pdf")
        with open(output_filename, "wb") as out_file:
            writer.write(out_file)
        created_files.append(output_filename)

    return created_files


def merge_pdfs(input_paths, output_path):
    """Merge the PDFs at input_paths (in order) into one PDF at output_path.

    Reads each source PDF, appends all its pages, writes the result, and returns
    output_path. Source files are only read, never modified.
    """
    writer = PdfWriter()
    for path in input_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as out_file:
        writer.write(out_file)

    return output_path


# --- PDF compression ---------------------------------------------------------
# Added for the upcoming PDF Compressor. Existing functions above are unchanged.

# Ghostscript -dPDFSETTINGS presets, ordered smallest -> highest quality.
GHOSTSCRIPT_QUALITIES = ("screen", "ebook", "printer", "prepress", "default")
DEFAULT_COMPRESSION_QUALITY = "ebook"

# Ghostscript executable names by platform (Windows console builds first).
_GHOSTSCRIPT_CANDIDATES = ("gswin64c", "gswin32c", "gs")


@dataclass
class CompressionResult:
    """Structured result of a PDF compression attempt."""
    ok: bool = False
    engine: Optional[str] = None        # "ghostscript" | "basic"
    quality: Optional[str] = None       # only meaningful for the ghostscript engine
    output_path: Optional[str] = None
    original_bytes: Optional[int] = None
    output_bytes: Optional[int] = None
    saved_bytes: Optional[int] = None
    saved_percent: Optional[float] = None
    smaller: bool = False
    error: Optional[str] = None
    process: Optional[ProcessResult] = None


def ghostscript_command():
    """Return the available Ghostscript executable name, or None if not installed."""
    return resolve_command(*_GHOSTSCRIPT_CANDIDATES)


def _finalize_result(result, input_path):
    """Fill in size-comparison fields when an output file was produced."""
    if result.output_path and os.path.exists(result.output_path):
        sizes = file_size.compare_files(input_path, result.output_path)
        result.original_bytes = sizes["original_bytes"]
        result.output_bytes = sizes["output_bytes"]
        result.saved_bytes = sizes["saved_bytes"]
        result.saved_percent = sizes["saved_percent"]
        result.smaller = sizes["smaller"]
    return result


def compress_pdf_ghostscript(input_path, output_path,
                             quality=DEFAULT_COMPRESSION_QUALITY, timeout=180):
    """Compress a PDF with Ghostscript. Returns a CompressionResult.

    `quality` must be one of GHOSTSCRIPT_QUALITIES. This engine gives real size
    reduction (including image downsampling) but requires Ghostscript installed.
    """
    if quality not in GHOSTSCRIPT_QUALITIES:
        return CompressionResult(
            ok=False, engine="ghostscript", quality=quality, output_path=output_path,
            error=f"Unknown quality '{quality}'. Use one of {GHOSTSCRIPT_QUALITIES}.",
        )

    gs = ghostscript_command()
    if gs is None:
        return CompressionResult(
            ok=False, engine="ghostscript", quality=quality, output_path=output_path,
            error="Ghostscript not found on PATH.",
        )

    args = [
        gs,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{quality}",
        "-dNOPAUSE",
        "-dBATCH",
        "-dQUIET",
        "-dSAFER",
        f"-sOutputFile={output_path}",
        input_path,
    ]
    proc = run_command(args, timeout=timeout)
    result = CompressionResult(
        ok=bool(proc.ok and os.path.exists(output_path)),
        engine="ghostscript",
        quality=quality,
        output_path=output_path,
        process=proc,
        error=None if proc.ok else (proc.error or proc.stderr.strip() or "Ghostscript failed"),
    )
    return _finalize_result(result, input_path)


def compress_pdf_basic(input_path, output_path):
    """Dependency-free fallback compression using PyPDF2 only.

    Rewrites the PDF and recompresses page content streams. Gains are modest (no
    image downsampling) but it needs no external tools. Returns a CompressionResult.
    """
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        for page in writer.pages:
            try:
                page.compress_content_streams()
            except Exception:
                # Some pages/streams cannot be recompressed; skip them safely.
                pass
        with open(output_path, "wb") as out_file:
            writer.write(out_file)
    except Exception as exc:
        return CompressionResult(ok=False, engine="basic", output_path=output_path,
                                 error=str(exc))

    result = CompressionResult(ok=True, engine="basic", output_path=output_path)
    return _finalize_result(result, input_path)


def compress_pdf(input_path, output_path, quality=DEFAULT_COMPRESSION_QUALITY,
                 engine="auto", timeout=180):
    """Compress a PDF and return a CompressionResult.

    engine:
      - "auto" (default): use Ghostscript if available, else the PyPDF2 fallback.
      - "ghostscript": force Ghostscript (errors cleanly if not installed).
      - "basic": force the PyPDF2-only fallback.
    """
    if engine == "ghostscript":
        return compress_pdf_ghostscript(input_path, output_path, quality=quality, timeout=timeout)
    if engine == "basic":
        return compress_pdf_basic(input_path, output_path)
    if engine == "auto":
        if ghostscript_command() is not None:
            return compress_pdf_ghostscript(input_path, output_path, quality=quality, timeout=timeout)
        return compress_pdf_basic(input_path, output_path)
    return CompressionResult(
        ok=False, output_path=output_path,
        error=f"Unknown engine '{engine}'. Use 'auto', 'ghostscript' or 'basic'.",
    )
