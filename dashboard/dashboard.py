# Dashboard module
from flask import Blueprint, render_template, request, redirect, url_for
import os
from core import master

dashboard = Blueprint(
    "dashboard",
    __name__,
    template_folder="templates",
    static_folder="static"
)

TEMP_DIR = os.path.join(os.getcwd(), "temp")


@dashboard.route("/")
def home():
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
                f.write(str(data))
            return redirect(url_for("dashboard.report"))
    return render_template("process.html")


@dashboard.route("/report")
def report():
    data = None
    output_file = os.path.join(TEMP_DIR, "output.txt")
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            data = f.read()
    return render_template("report.html", data=data)
