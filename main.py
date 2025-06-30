from app import app

# Import routes and auth modules
from routes import main, api
from auth import auth

# Register blueprints
app.register_blueprint(main)
app.register_blueprint(api)
app.register_blueprint(auth, url_prefix='/auth')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
