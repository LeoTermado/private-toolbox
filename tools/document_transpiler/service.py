"""Advanced Document Transpiler logic (no Flask).

Scoped, reliable conversion: Markdown -> standalone HTML using the installed
`markdown` package. More source/target formats can be added later; the UI is
honest about what is currently supported.
"""
import os

import markdown

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_upload as _save_upload
from core.filenames import sanitize_filename, unique_path

TOOL_SLUG = "document_transpiler"

DOC_INPUT = tool_input_dir(TOOL_SLUG)
DOC_OUTPUT = tool_output_dir(TOOL_SLUG)

# Currently supported conversions (value -> label). Kept explicit/honest.
CONVERSIONS = [("md_to_html", "Markdown → HTML")]
DEFAULT_CONVERSION = "md_to_html"

INPUT_EXTENSIONS = {".md", ".markdown", ".txt"}

_MD_EXTENSIONS = ["extra", "fenced_code", "tables", "toc", "sane_lists"]

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  body {{ max-width: 820px; margin: 2rem auto; padding: 0 1rem;
         font-family: system-ui, -apple-system, Segoe UI, sans-serif; line-height: 1.6; color: #222; }}
  pre {{ background: #f4f4f4; padding: 1rem; overflow: auto; border-radius: 6px; }}
  code {{ font-family: ui-monospace, Consolas, monospace; }}
  table {{ border-collapse: collapse; }}
  th, td {{ border: 1px solid #ccc; padding: 4px 8px; }}
  blockquote {{ border-left: 4px solid #ddd; margin: 0; padding-left: 1rem; color: #555; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def ensure_doc_folders():
    return ensure_tool_folders(TOOL_SLUG)


def save_upload(file_storage):
    ensure_doc_folders()
    return _save_upload(file_storage, DOC_INPUT, default_name="document.md")


def markdown_to_html(text):
    """Convert Markdown text to an HTML body fragment."""
    return markdown.markdown(text, extensions=_MD_EXTENSIONS)


def build_document(body_html, title="Document"):
    """Wrap an HTML body fragment in a minimal standalone HTML document."""
    return _HTML_TEMPLATE.format(title=title, body=body_html)


def convert(text, output_basename):
    """Convert Markdown text to a standalone HTML file; return (output_path, html)."""
    ensure_doc_folders()
    body = markdown_to_html(text)
    title = sanitize_filename(output_basename, default="document") or "document"
    html = build_document(body, title=title)
    out_path = unique_path(DOC_OUTPUT, f"{title}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path, html
