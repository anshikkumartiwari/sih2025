# AI Agent Instructions for Automated Compliance Checker

## Architecture Overview

This project is a **Flask-based web application** designed to automatically verify **Legal Metrology declarations** on e-commerce platforms. The application follows a modular architecture with a clear separation between:

* **Web Interface**: `dashboard/`
* **Business Logic & AI Modules**: `core/`

The design supports easy expansion for additional e-commerce platforms, OCR/AI models, and rule engines. The **primary source of compliance data is the product label image**, with textual product information used only as supplementary reference.

---

## Key Components

* **app.py**: Flask application entry point; registers the `dashboard` blueprint and starts the server.

* **dashboard/dashboard.py**: Blueprint containing web routes:

  * `/` → Home page introducing the problem
  * `/process` → Input product URL and start compliance checking
  * `/report` → View compliance results

* **core/master.py**: Orchestrator that routes product URLs to the appropriate platform-specific crawler, coordinates image download, OCR, and compliance checks.

* **core/crawlers/**: Platform-specific crawlers (currently `amazon.py` with dummy product data) that download product images for label analysis.

* **core/ocr.py, vision.py, rules.py**: AI/ML modules for:

  * OCR extraction of label text
  * Computer vision to segment the declaration region on the packaging
  * Rule engine to validate each extracted field against Legal Metrology requirements

---

## Data Flow Pattern

1. User submits a product URL through the `/process` form.

2. `master.process_product()` directs the URL to the appropriate crawler.

3. Crawler **downloads product image(s)** and optionally collects textual fields from the listing.

4. AI/ML pipeline processes the image:

   * Segments the label using computer vision
   * Extracts text using OCR
   * Validates extracted fields against Legal Metrology rules, including:

     * Product title
     * Name and address of the manufacturer/packer/importer
     * Net quantity (standard units)
     * Retail sale price (MRP, inclusive of taxes)
     * Consumer care details
     * Date of manufacture/import
     * Country of origin

5. Extracted and validated data is temporarily stored in `temp/output.txt`.

6. `/report` route reads and displays the data for review.

---

## Development Workflow

* **Run locally**:

```bash
python app.py
```

Flask development server runs on `http://127.0.0.1:5000`.

* **Environment**: Virtual environment (`.venv/` recommended)

```bash
pip install -r requirements.txt
```

* **Debug mode**: Enabled by default in `app.py`.

---

## Code Patterns

* **Blueprints**: All dashboard routes are organized using a Flask blueprint in `dashboard/dashboard.py`.
* **Platform Routing**: `master.py` uses URL string matching (e.g., `"amazon" in url.lower()`) to dispatch to crawlers.
* **Temporary Storage**: Intermediate data is saved in the `temp/` folder:

```python
os.makedirs(TEMP_DIR, exist_ok=True)
```

* **Data Persistence**: Currently file-based; no database dependencies for MVP.
* **Error Handling**: Unsupported platforms return:

```python
{"error": "Unsupported platform"}
```

---

## File Structure Conventions

* `core/`: Contains all business logic and AI/ML modules, focused on image-based OCR and validation.
* `dashboard/`: Flask blueprint with `templates/` and `static/` folders for frontend.
* `temp/`: Temporary storage for crawled images and extracted data (excluded from Git).
* `core/__init__.py` and `dashboard/__init__.py`: Minimal; only for package recognition.

---

## Adding New Features

* **New crawler**: Add module to `core/crawlers/` to handle new e-commerce sites, and update routing in `master.py`.
* **New core module**: Create in `core/` (e.g., improved OCR, label segmentation, rule engine) and import in `master.py`.
* **New route/page**: Add to `dashboard/dashboard.py` blueprint.
* **Dependencies**: Add to `requirements.txt` and document usage in module docstrings.

---

## Testing Approach

* **Manual Testing** via web interface.
* **Test URLs**: Use live product URLs to validate image-based OCR and label extraction.
* **Data Validation**: Check contents of `temp/output.txt` after processing to ensure extracted fields match label data.

---

## Deployment Notes

* **Static Files**: Served from `dashboard/static/`.
* **Templates**: Jinja2 templates in `dashboard/templates/`.
* **Database**: Not required for MVP; file-based storage for images and extracted data.

---
