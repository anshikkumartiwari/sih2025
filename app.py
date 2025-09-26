from flask import Flask
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass
from dashboard.dashboard import dashboard  # import the Blueprint object

def create_app():
    app = Flask(__name__)
    app.static_folder = 'dashboard/static'
    app.register_blueprint(dashboard)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", debug=True)
