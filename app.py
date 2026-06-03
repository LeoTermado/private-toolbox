"""Private Toolbox — Flask application factory.

Builds the app, wires up the shared tool registry (used by the sidebar and the
dashboard cards), and registers every tool blueprint. Only the PDF Splitter is
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

# Single source of truth for the sidebar + dashboard cards.
# endpoint -> Flask endpoint for url_for; path -> resolved URL (for active highlight).
TOOLS = [
    {"endpoint": "pdf_splitter.index",     "path": "/pdf/splitter/",     "label": "PDF Splitter",      "icon": "📄", "implemented": True},
    {"endpoint": "pdf_merger.index",       "path": "/pdf/merger/",       "label": "PDF Merger",        "icon": "🔗", "implemented": False},
    {"endpoint": "pdf_compressor.index",   "path": "/pdf/compressor/",   "label": "PDF Compressor",    "icon": "🗜️", "implemented": False},
    {"endpoint": "image_to_pdf.index",     "path": "/image/to-pdf/",     "label": "Image to PDF",      "icon": "🖼️", "implemented": False},
    {"endpoint": "pdf_to_image.index",     "path": "/pdf/to-image/",     "label": "PDF to Image",      "icon": "🏞️", "implemented": False},
    {"endpoint": "file_renamer.index",     "path": "/files/renamer/",    "label": "File Renamer",      "icon": "✏️", "implemented": False},
    {"endpoint": "text_cleaner.index",     "path": "/text/cleaner/",     "label": "Text Cleaner",      "icon": "🧹", "implemented": False},
    {"endpoint": "zip_splitter.index",     "path": "/files/zip-splitter/", "label": "ZIP Splitter",    "icon": "📦", "implemented": False},
    {"endpoint": "ocr_organizer.index",    "path": "/ocr/organizer/",    "label": "OCR Organizer",     "icon": "🔍", "implemented": False},
    {"endpoint": "document_redactor.index", "path": "/privacy/redactor/", "label": "Document Redactor", "icon": "🕵️", "implemented": False},
]


def create_app():
    app = Flask(__name__)
    app.secret_key = "super_secret_key_for_flash_messages"

    # Make sure input/, output/ and old/ exist on startup.
    ensure_folders()

    # Expose the tool registry to every template (sidebar + cards).
    @app.context_processor
    def inject_tools():
        return {"tools": TOOLS}

    # Homepage / dashboard.
    @app.route('/')
    def index():
        return render_template('index.html')

    # Register all tool blueprints.
    for bp in (
        pdf_splitter_bp, pdf_merger_bp, pdf_compressor_bp, image_to_pdf_bp,
        pdf_to_image_bp, file_renamer_bp, text_cleaner_bp, zip_splitter_bp,
        ocr_organizer_bp, document_redactor_bp,
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
