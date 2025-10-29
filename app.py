import os
import logging
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure CORS for Android WebView and local network access
# This enables cross-origin requests from the WebView client
CORS(app, 
     supports_credentials=True, 
     origins=[
         "http://tvcon.trinity.local",
         "http://localhost:5000",
         "http://127.0.0.1:5000"
     ],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     expose_headers=["Content-Type", "Authorization"],
     max_age=3600  # Cache preflight requests for 1 hour
)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///signage.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure session cookies for HTTP (not HTTPS) on local network
# Required for Android WebView to accept cookies
app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow cookies on all subdomains
app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP (local network)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS attacks
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cross-origin with credentials
app.config['SESSION_COOKIE_PATH'] = '/'  # Cookie available for all paths
app.config['REMEMBER_COOKIE_DOMAIN'] = None
app.config['REMEMBER_COOKIE_SECURE'] = False  # Allow HTTP for "remember me"
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_PATH'] = '/'

# Configure file uploads
upload_folder = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['UPLOAD_FOLDER'] = upload_folder
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300  # 5 minutes for large files

# Ensure upload directory exists and is writable
os.makedirs(upload_folder, exist_ok=True)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global middleware to inject CORS and cache-control headers
@app.after_request
def after_request(response):
    """Add CORS and cache-control headers to every response"""
    # Get the origin from the request
    origin = request.headers.get('Origin')
    
    # Allow specified origins with credentials
    allowed_origins = [
        'http://tvcon.trinity.local',
        'http://localhost:5000',
        'http://127.0.0.1:5000'
    ]
    
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    else:
        # Default to tvcon.trinity.local if no origin header
        response.headers['Access-Control-Allow-Origin'] = 'http://tvcon.trinity.local'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Vary'] = 'Origin'
    
    # No-cache for control and API endpoints to prevent stale data in WebView
    if request.path.startswith('/control') or request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

@app.before_request
def before_request():
    """Handle OPTIONS preflight and log cookies for debugging"""
    # Debug logging for API requests to verify cookies are being sent
    if request.path.startswith('/api/'):
        logging.debug(f'API Request: {request.method} {request.path}')
        logging.debug(f'Cookies: {dict(request.cookies)}')
        logging.debug(f'Origin: {request.headers.get("Origin")}')
    
    # Handle OPTIONS preflight requests
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        
        origin = request.headers.get('Origin')
        allowed_origins = [
            'http://tvcon.trinity.local',
            'http://localhost:5000',
            'http://127.0.0.1:5000'
        ]
        
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = 'http://tvcon.trinity.local'
        
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Max-Age'] = '3600'
        
        return response

with app.app_context():
    # Import models here to ensure they're registered
    import models
    db.create_all()
    logging.info("Database tables created")

# Blueprints are registered in main.py
