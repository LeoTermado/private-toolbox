"""Private Toolbox — Flask application factory.

Builds the app, wires up the shared tool registry (used by the sidebar and the
dashboard cards), and registers every tool blueprint. Only the PDF Splitter and Merger are
functional; the rest render a placeholder page.
"""
from flask import Flask, render_template, redirect, url_for

from core.file_utils import ensure_folders

# Tool blueprints
from tools.pdf_splitter.routes import bp as pdf_splitter_bp
from tools.pdf_merger.routes import bp as pdf_merger_bp
from tools.pdf_compressor.routes import bp as pdf_compressor_bp
from tools.image_to_pdf.routes import bp as image_to_pdf_bp
from tools.pdf_to_image.routes import bp as pdf_to_image_bp
from tools.file_renamer.routes import bp as file_renamer_bp
from tools.text_cleaner.routes import bp as text_cleaner_bp
from tools.zip_splitter.routes import bp as zip_splitter_bp
from tools.ocr_organizer.routes import bp as ocr_organizer_bp
from tools.document_redactor.routes import bp as document_redactor_bp
from tools.pdf_password_guard.routes import bp as pdf_password_guard_bp
from tools.pdf_metadata_purge.routes import bp as pdf_metadata_purge_bp
from tools.image_format_changer.routes import bp as image_format_changer_bp
from tools.image_resizer_compressor.routes import bp as image_resizer_compressor_bp
from tools.photo_exif_scrubber.routes import bp as photo_exif_scrubber_bp
from tools.structured_data_beautifier.routes import bp as structured_data_beautifier_bp
from tools.file_checksum_generator.routes import bp as file_checksum_generator_bp
from tools.secure_key_generator.routes import bp as secure_key_generator_bp
from tools.archive_content_inspector.routes import bp as archive_content_inspector_bp
from tools.media_converter.routes import bp as media_converter_bp
from tools.video_trimmer_animation.routes import bp as video_trimmer_animation_bp
from tools.background_eraser.routes import bp as background_eraser_bp
from tools.document_transpiler.routes import bp as document_transpiler_bp

# Single source of truth for the sidebar + dashboard cards.
# endpoint -> Flask endpoint for url_for; path -> resolved URL (for active highlight).
TOOLS = [
    {"endpoint": "pdf_splitter.index",     "path": "/pdf/splitter/",     "label": "PDF Splitter",      "icon": "📄", "implemented": True},
    {"endpoint": "pdf_merger.index",       "path": "/pdf/merger/",       "label": "PDF Merger",        "icon": "🔗", "implemented": True},
    {"endpoint": "pdf_compressor.index",   "path": "/pdf/compressor/",   "label": "PDF Compressor",    "icon": "🗜️", "implemented": True},
    {"endpoint": "image_to_pdf.index",     "path": "/image/to-pdf/",     "label": "Image to PDF",      "icon": "🖼️", "implemented": False},
    {"endpoint": "pdf_to_image.index",     "path": "/pdf/to-image/",     "label": "PDF to Image",      "icon": "🏞️", "implemented": False},
    {"endpoint": "file_renamer.index",     "path": "/files/renamer/",    "label": "File Renamer",      "icon": "✏️", "implemented": True},
    {"endpoint": "text_cleaner.index",     "path": "/text/cleaner/",     "label": "Text Cleaner",      "icon": "🧹", "implemented": False},
    {"endpoint": "zip_splitter.index",     "path": "/files/zip-splitter/", "label": "ZIP Splitter",    "icon": "📦", "implemented": False},
    {"endpoint": "ocr_organizer.index",    "path": "/ocr/organizer/",    "label": "OCR Organizer",     "icon": "🔍", "implemented": False},
    {"endpoint": "document_redactor.index", "path": "/privacy/redactor/", "label": "Document Redactor", "icon": "🕵️", "implemented": False},
    {"endpoint": "pdf_password_guard.index", "path": "/pdf/password-guard/", "label": "PDF Password Guard", "icon": "🔒", "implemented": False},
    {"endpoint": "pdf_metadata_purge.index", "path": "/pdf/metadata-purge/", "label": "PDF Metadata Purge", "icon": "🧽", "implemented": False},
    {"endpoint": "image_format_changer.index", "path": "/image/format-changer/", "label": "Universal Image Format Changer", "icon": "🔄", "implemented": True},
    {"endpoint": "image_resizer_compressor.index", "path": "/image/resizer-compressor/", "label": "Image Resizer & Compressor", "icon": "📐", "implemented": True},
    {"endpoint": "photo_exif_scrubber.index", "path": "/image/exif-scrubber/", "label": "Photo EXIF Scrubber", "icon": "🧼", "implemented": False},
    {"endpoint": "structured_data_beautifier.index", "path": "/data/beautifier/", "label": "Structured Data Beautifier", "icon": "✨", "implemented": False},
    {"endpoint": "file_checksum_generator.index", "path": "/files/checksum/", "label": "File Checksum Generator", "icon": "🔢", "implemented": True},
    {"endpoint": "secure_key_generator.index", "path": "/security/key-generator/", "label": "Secure Key Generator", "icon": "🔑", "implemented": False},
    {"endpoint": "archive_content_inspector.index", "path": "/files/archive-inspector/", "label": "Archive Content Inspector", "icon": "🗃️", "implemented": True},
    {"endpoint": "media_converter.index", "path": "/media/converter/", "label": "Audio & Video Converter", "icon": "🎬", "implemented": False},
    {"endpoint": "video_trimmer_animation.index", "path": "/media/video-trimmer/", "label": "Video Snippet Trimmer & Animation Creator", "icon": "✂️", "implemented": False},
    {"endpoint": "background_eraser.index", "path": "/image/background-eraser/", "label": "Automated Asset Background Eraser", "icon": "🪄", "implemented": False},
    {"endpoint": "document_transpiler.index", "path": "/documents/transpiler/", "label": "Advanced Document Transpiler", "icon": "📑", "implemented": False},
]

# Category grouping for the sidebar accordion and the home dashboard sections.
# Both render from this single ordering, so they always match. Each entry is
# (category name, [tool endpoints in display order]).
TOOL_CATEGORIES = [
    ("Document & PDF Tools", [
        "pdf_splitter.index", "pdf_merger.index", "pdf_compressor.index",
        "pdf_password_guard.index", "pdf_metadata_purge.index",
        "image_to_pdf.index", "pdf_to_image.index", "document_redactor.index",
        "document_transpiler.index",
    ]),
    ("Image Tools", [
        "image_format_changer.index", "image_resizer_compressor.index",
        "photo_exif_scrubber.index", "background_eraser.index",
    ]),
    ("Text, Data & Security", [
        "text_cleaner.index", "structured_data_beautifier.index",
        "file_checksum_generator.index", "secure_key_generator.index",
    ]),
    ("File & Archive Tools", [
        "file_renamer.index", "zip_splitter.index", "archive_content_inspector.index",
    ]),
    ("OCR & Media Tools", [
        "ocr_organizer.index", "media_converter.index", "video_trimmer_animation.index",
    ]),
]

_TOOLS_BY_ENDPOINT = {tool["endpoint"]: tool for tool in TOOLS}


def build_categories():
    """Resolve TOOL_CATEGORIES into [{name, tools: [tool dict, ...]}, ...]."""
    categories = []
    for name, endpoints in TOOL_CATEGORIES:
        items = [_TOOLS_BY_ENDPOINT[e] for e in endpoints if e in _TOOLS_BY_ENDPOINT]
        categories.append({"name": name, "tools": items})
    return categories


def create_app():
    app = Flask(__name__)
    app.secret_key = "super_secret_key_for_flash_messages"

    # Make sure input/, output/ and old/ exist on startup.
    ensure_folders()

    # Expose the tool registry to every template (sidebar + cards).
    @app.context_processor
    def inject_tools():
        return {"tools": TOOLS, "categories": build_categories()}

    # Homepage / dashboard.
    @app.route('/')
    def index():
        return render_template('index.html')

    # Register all tool blueprints.
    for bp in (
        pdf_splitter_bp, pdf_merger_bp, pdf_compressor_bp, image_to_pdf_bp,
        pdf_to_image_bp, file_renamer_bp, text_cleaner_bp, zip_splitter_bp,
        ocr_organizer_bp, document_redactor_bp,
        pdf_password_guard_bp, pdf_metadata_purge_bp, image_format_changer_bp,
        image_resizer_compressor_bp, photo_exif_scrubber_bp,
        structured_data_beautifier_bp, file_checksum_generator_bp,
        secure_key_generator_bp, archive_content_inspector_bp, media_converter_bp,
        video_trimmer_animation_bp, background_eraser_bp, document_transpiler_bp,
    ):
        app.register_blueprint(bp)

    # Backwards-compatible redirects for the original splitter URLs.
    # 307 preserves the POST method and body so uploads re-post correctly.
    @app.route('/split', methods=['POST'])
    def legacy_split():
        return redirect(url_for('pdf_splitter.split'), code=307)

    @app.route('/archive', methods=['POST'])
    def legacy_archive():
        return redirect(url_for('pdf_splitter.archive'), code=307)

    return app


# Module-level app for tooling that expects `app` (e.g. `flask run`).
app = create_app()


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
