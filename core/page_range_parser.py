"""Shared page-range parsing logic (no Flask, no I/O).

Moved verbatim from the original run.py so both the web splitter and the
standalone CLI (cli_splitter.py) can reuse it.
"""


def parse_single_range(part_str, total_pages):
    """Parses a single chunk like '1-5' or '10' and returns 0-indexed page numbers."""
    pages = []
    clean_part = part_str.strip()

    if "-" in clean_part:
        start_str, end_str = clean_part.split("-")
        start = int(start_str) - 1  # Convert to 0-indexed
        end = int(end_str)          # Keep inclusive for range

        # Bound checks to make sure we don't crash on short PDFs
        start = max(0, min(start, total_pages))
        end = max(0, min(end, total_pages))

        pages.extend(list(range(start, end)))
    else:
        page_num = int(clean_part) - 1
        if 0 <= page_num < total_pages:
            pages.append(page_num)

    return pages
