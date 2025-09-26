from flask import Flask
from flask_cors import CORS
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass
from dashboard.dashboard import dashboard  # import the Blueprint object

def create_app():
    app = Flask(__name__)
    app.static_folder = 'dashboard/static'
    
    # Enable CORS for Chrome extension
    CORS(app, origins=["chrome-extension://*", "http://localhost:*", "http://127.0.0.1:*"])
    
    app.register_blueprint(dashboard)
    return app

# Create app instance at module level for gunicorn
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
