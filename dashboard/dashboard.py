# Dashboard module
from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory
import os
from core import master
from core import normalize_image_to_jpeg
import json
from core import ocr
from core.master import process_uploaded_images
from core import manufacturer_tracker
from core import historical_data



dashboard = Blueprint(
    "dashboard",
    __name__,
    template_folder="templates",
    static_folder="static"
)

TEMP_DIR = os.path.join(os.getcwd(), "temp")
UPLOAD_DIR = os.path.join(TEMP_DIR, "uploads")


@dashboard.route("/")
def home():
    return render_template("landing.html")

@dashboard.route("/demo")
def demo():
    return render_template("index.html")


@dashboard.route("/process", methods=["GET", "POST"])
def process():
    if request.method == "POST":
        product_url = request.form.get("product_url")
        if product_url:
            data = master.process_product(product_url)
            # save raw data to temp (for now as a txt file)
            os.makedirs(TEMP_DIR, exist_ok=True)
            with open(os.path.join(TEMP_DIR, "output.txt"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return redirect(url_for("dashboard.report"))
    return render_template("process.html")


@dashboard.route("/report")
def report():
    data = None
    output_file = os.path.join(TEMP_DIR, "output.txt")
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    return render_template("report.html", data=data)


@dashboard.route("/upload", methods=["POST"])
def upload():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file = request.files.get("photo")
    if not file or file.filename == "":
        return redirect(url_for("dashboard.process"))

    # Save file
    filename = file.filename
    # Basic sanitize: keep base name only
    filename = os.path.basename(filename)
    save_path = os.path.join(UPLOAD_DIR, filename)
    file.save(save_path)

    # Normalize/convert to JPEG with correct orientation to avoid OpenCV resize errors
    normalized_path = normalize_image_to_jpeg(save_path)

    # Run full pipeline on the uploaded image
    try:
        data = process_uploaded_images([normalized_path])
        # Convert local file paths to served URLs for the report
        url_images = []
        for p in data.get("images", []):
            base = os.path.basename(p)
            url_images.append(url_for("dashboard.serve_upload", filename=base))
        data["images"] = url_images
    except Exception as e:
        data = {
            "title": "Uploaded Image",
            "images": [url_for("dashboard.serve_upload", filename=filename)],
            "ocr": {"extracted_text": ""},
            "missing_fields": [],
            "warnings": [f"Processing error: {e}"],
            "compliance_summary": {
                "total_fields_found": 0,
                "required_present": 0,
                "required_total": 4,
                "compliance_score": "0/4",
            },
        }

    # Persist to temp for the report page
    os.makedirs(TEMP_DIR, exist_ok=True)
    with open(os.path.join(TEMP_DIR, "output.txt"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return redirect(url_for("dashboard.report"))


@dashboard.route("/uploads/<path:filename>")
def serve_upload(filename: str):
    return send_from_directory(UPLOAD_DIR, filename)


@dashboard.route("/manufacturers")
def manufacturers():
    """Display manufacturer analytics dashboard."""
    try:
        manufacturers_list = manufacturer_tracker.get_all_manufacturers()
        comparison_data = manufacturer_tracker.get_manufacturer_comparison()
        return render_template("manufacturers.html", 
                             manufacturers=manufacturers_list, 
                             comparison=comparison_data)
    except Exception as e:
        return render_template("manufacturers.html", 
                             manufacturers=[], 
                             comparison={"error": str(e)})


@dashboard.route("/manufacturer/<manufacturer_name>")
def manufacturer_detail(manufacturer_name: str):
    """Display detailed analytics for a specific manufacturer."""
    try:
        analytics = manufacturer_tracker.get_manufacturer_analytics(manufacturer_name)
        return render_template("manufacturer_detail.html", analytics=analytics)
    except Exception as e:
        return render_template("manufacturer_detail.html", 
                             analytics={"error": str(e)})


@dashboard.route("/analytics")
def analytics():
    """Display comprehensive historical analytics dashboard."""
    try:
        analytics_data = historical_data.get_historical_analytics()
        return render_template("analytics.html", analytics=analytics_data)
    except Exception as e:
        return render_template("analytics.html", 
                             analytics={"error": str(e)})


@dashboard.route("/history")
def history():
    """Display scan history with filtering options."""
    try:
        manufacturer = request.args.get('manufacturer')
        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))
        
        history_data = historical_data.get_scan_history(limit=limit, manufacturer=manufacturer, category=category)
        analytics_data = historical_data.get_historical_analytics()
        
        return render_template("history.html", 
                             history=history_data, 
                             analytics=analytics_data,
                             filters={"manufacturer": manufacturer, "category": category, "limit": limit})
    except Exception as e:
        return render_template("history.html", 
                             history=[], 
                             analytics={"error": str(e)},
                             filters={})


@dashboard.route("/export")
def export_data():
    """Export historical data in various formats."""
    try:
        format_type = request.args.get('format', 'json')
        data = historical_data.export_historical_data(format=format_type)
        
        if format_type == 'json':
            return data, 200, {'Content-Type': 'application/json'}
        elif format_type == 'csv':
            return data, 200, {'Content-Type': 'text/csv'}
        else:
            return "Unsupported format", 400
    except Exception as e:
        return f"Export failed: {str(e)}", 500


@dashboard.route("/product/<scan_id>")
def product_detail(scan_id: str):
    """Display detailed information for a specific product scan."""
    try:
        # Load historical data and find the specific scan
        historical_data_obj = historical_data.load_historical_data()
        scan_record = None
        
        for scan in historical_data_obj["scan_history"]:
            if scan["scan_id"] == scan_id:
                scan_record = scan
                break
        
        if not scan_record:
            return render_template("product_detail.html", 
                                 product={"error": "Product not found"})
        
        return render_template("product_detail.html", product=scan_record)
    except Exception as e:
        return render_template("product_detail.html", 
                             product={"error": str(e)})
