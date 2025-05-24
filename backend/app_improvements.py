# Add to your backend/app.py
from cy_app_config import app_config
from cy_improved_routes import improved_routes
from cy_error_handler import ErrorHandler

# Setup logging
app_config.setup_logging()

# Register improved routes
app.register_blueprint(improved_routes)

# Add global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    return ErrorHandler.create_error_response(
        "An unexpected error occurred",
        500,
        "INTERNAL_ERROR"
    )
