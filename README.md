# Private Toolbox

Private Toolbox is a local, privacy-friendly web app for file, document, PDF, image, archive, text, and security utilities.

Instead of uploading private files to random online tools, you run Private Toolbox on your own machine, open it in your browser, process your files locally, and download the result.

It is designed to become a large free toolbox with many practical tools in one clean dashboard.

---

## Why Private Toolbox?

Most people use online tools for simple file tasks.

Compress a PDF.
Merge documents.
Convert images.
Clean text.
Generate a secure password.
Inspect an archive.
Remove metadata.

That works, but it often comes with problems:

* You upload private files to third-party websites.
* You deal with ads, limits, waiting screens, and account walls.
* You need a different website for every task.
* You rely on tools that can change, disappear, or lock features later.
* You depend on your operating system having the right built-in utility.

Private Toolbox gives you a different approach.

One local app.
Many useful tools.
Your files stay on your machine.

---

## What it does

Private Toolbox collects practical everyday utilities into one local dashboard.

The project currently includes tools across several categories:

* PDF tools
* image tools
* text and data tools
* security tools
* archive tools
* document tools
* planned media tools
* planned OCR and automation tools

The focus is not only PDF processing. The long-term goal is to build a broad local utility suite that can replace dozens of small websites and one-off apps.

---

## Core benefits

### Private by default

Private Toolbox processes files locally. Your documents, images, archives, and generated files stay on your own machine.

### No random upload websites

You do not need to send sensitive files to unknown online converters, PDF tools, compression services, or metadata removers.

### One place for many tools

Private Toolbox brings common file utilities together in a single browser-based dashboard.

### Built to grow

The project is structured so new tools can be added cleanly. Each tool lives in its own module, while shared behavior stays in reusable core helpers.

### Free and open-source friendly

Private Toolbox is intended to be free for users and source-available for people who want to inspect, learn from, or contribute to the project.

A final license will be selected before the first proper public release. Until then, attribution and project credit should remain attached to the original project.

---

## Project vision

Private Toolbox aims to become a powerful local alternative to online utility websites.

The goal is to grow from a small collection of tools into a complete personal toolbox with many practical utilities for files, documents, media, developers, students, and everyday users.

The long-term direction is simple:

* keep it free
* keep it local
* keep it useful
* keep it expandable
* keep it clean enough for real users
* keep private files away from random web services

At some point, Private Toolbox should be the kind of app people install once and keep using because it handles many small tasks they normally search online for.

---

## Current status

Private Toolbox is already functional and includes multiple implemented tools.

The app currently has:

* a local Flask web interface
* a dashboard with tool categories
* a light/dark theme
* implemented tools across PDF, image, text, archive, document, and security workflows
* planned placeholder tools for heavier future features
* local input and output folders
* archive support for completed sessions
* reusable shared helper modules
* a structure designed for long-term expansion

Some advanced tools are intentionally planned instead of rushed. Features such as OCR, media conversion, true secure redaction, background removal, and PDF-to-image rendering may need heavier dependencies or deeper safety checks.

---

## Tech stack

Private Toolbox currently uses:

* Python
* Flask
* Werkzeug
* PyPDF2
* Pillow
* Markdown
* Python standard library

Optional external tools may be used for stronger results in specific workflows. For example, PDF compression works best when Ghostscript is installed.

---

## Installation

Private Toolbox needs Python 3.9 or newer.

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

## How it works

1. Start the app locally.
2. Open the dashboard in your browser.
3. Choose a tool.
4. Upload files or paste input.
5. Run the operation.
6. Download the result.
7. Archive the current session when you are done.

The app stores current source files and generated files locally in project folders. Archived sessions are moved into timestamped archive folders.

---

## Project structure

```text
app.py              Flask app factory, tool registry, categories, blueprint wiring
run.py              Local launcher
cli_splitter.py     Standalone command-line PDF splitter
requirements.txt    Pinned Python dependencies
core/               Shared helper modules
tools/              One folder per toolbox tool
templates/          Jinja templates
static/             CSS and JavaScript
input/              Uploaded and source files
output/             Generated files
old/                Archived sessions
```

Most implemented tools follow this pattern:

```text
tools/<tool_slug>/
  routes.py         Flask routes, validation, flash messages, downloads
  service.py        Tool logic, kept separate from Flask where possible
  __init__.py

templates/<tool_slug>.html
```

Each tool also uses its own `input/<tool_slug>/` and `output/<tool_slug>/` subfolders, so different tools never mix files. This structure keeps the app maintainable as more tools are added.

---

## Design philosophy

Private Toolbox follows a practical rule:

Useful local tools first.
Clean structure always.
No fake safety claims.
No rushed heavy features.

Some features are easy to build locally. Others need external engines, careful file handling, or extra security work. Private Toolbox should be honest about that.

For example, a basic metadata remover is different from true secure redaction. A simple PDF fallback is different from high-quality Ghostscript compression. A basic PDF password is different from strong modern encryption. A placeholder is better than a dangerous half-working feature.

---

## Security and privacy note

Private Toolbox is currently designed as a local private app.

It is not a hardened public web application.

At the current development stage:

* the app is meant to run on your own machine
* uploaded and generated files are stored locally
* debug settings may be used during development
* the app should not be exposed to the public internet without proper hardening
* sensitive workflows should be implemented carefully and tested before release

Use it as a local tool, not as a public hosted service.

---

## Roadmap

The project is built for long-term expansion.

Planned growth areas include:

* more PDF tools
* more image tools
* OCR tools
* media tools
* archive tools
* document conversion tools
* developer utilities
* batch-processing tools
* privacy and security utilities
* productivity helpers

The long-term goal is to grow Private Toolbox into a large local toolbox with dozens of practical utilities.

---

## Contributing

Contributions should keep the project clean and expandable.

Good additions should:

* follow the existing tool structure
* keep processing logic separate from Flask routes
* reuse shared helpers from `core/`
* validate uploads carefully
* organize input and output files clearly
* avoid silent overwrites
* explain external dependencies
* avoid pretending risky features are safer than they are

The project should stay practical, readable, and useful.

---

## License

Private Toolbox is intended to be free and open-source friendly.

A final license has not been selected yet. The license will be added before the first proper public release.

Until then, please keep project credit and attribution attached to the original project.

---

## Credits

Created by Leo Termado.

Private Toolbox exists to make everyday file work easier, safer, and more independent from online utility websites.
