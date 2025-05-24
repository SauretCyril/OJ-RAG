"""
Example of improved route implementation using the new utilities
"""
from flask import Blueprint, request, jsonify
from cy_error_handler import handle_api_errors, validate_json_input, ErrorHandler, APIError
from cy_security import SecurityValidator
from cy_data_layer import AnnonceManager, ConfigManager
from cy_file_manager import AsyncFileManager
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

# Initialize data managers (should be done in app initialization)
annonce_manager = AnnonceManager('data')
config_manager = ConfigManager('config')

improved_routes = Blueprint('improved_routes', __name__)

@improved_routes.route('/api/v2/annonces', methods=['GET'])
@handle_api_errors
async def get_annonces_v2():
    """
    Improved version of read_annonces_json with better error handling and performance
    """
    try:
        # Get query parameters
        status_filter = request.args.get('status')
        excluded_file = request.args.get('excluded', 'excluded_annonces.json')
        
        # Validate excluded file parameter
        if not SecurityValidator.validate_filename(excluded_file):
            raise APIError("Invalid excluded file name", 400, "INVALID_FILENAME")
        
        # Build filters
        filters = {}
        if status_filter:
            filters['etat'] = status_filter
        
        # Get announcements with caching
        annonces = await annonce_manager.get_annonces_list(filters)
        
        # Apply exclusion criteria if needed
        if excluded_file:
            try:
                exclusion_config = await config_manager.get_config(f'exclusions_{excluded_file}', {})
                if exclusion_config:
                    annonces = [a for a in annonces if not _is_excluded(a, exclusion_config)]
            except Exception as e:
                logger.warning(f"Could not apply exclusion criteria: {e}")
        
        return jsonify(ErrorHandler.create_success_response(
            data=annonces,
            meta={"count": len(annonces), "filters": filters}
        ))
        
    except Exception as e:
        logger.error(f"Error in get_annonces_v2: {e}")
        raise

@improved_routes.route('/api/v2/annonces/<dossier_id>', methods=['GET'])
@handle_api_errors
async def get_annonce_v2(dossier_id: str):
    """Get a single announcement by ID"""
    # Validate dossier_id
    if not dossier_id or len(dossier_id) > 50:
        raise APIError("Invalid dossier ID", 400, "INVALID_ID")
    
    annonce = await annonce_manager.get_annonce(dossier_id)
    if not annonce:
        raise APIError(f"Announcement {dossier_id} not found", 404, "NOT_FOUND")
    
    return jsonify(ErrorHandler.create_success_response(data=annonce))

@improved_routes.route('/api/v2/annonces/<dossier_id>', methods=['PUT'])
@handle_api_errors
@validate_json_input(['etat'])
async def update_annonce_v2(dossier_id: str):
    """Update announcement status"""
    data = request.get_json()
    new_status = data['etat']
    
    # Validate status
    valid_statuses = ['New', 'Processing', 'Completed', 'DELETED']
    if new_status not in valid_statuses:
        raise APIError(f"Invalid status. Must be one of: {valid_statuses}", 400, "INVALID_STATUS")
    
    success = await annonce_manager.update_annonce_status(dossier_id, new_status)
    if not success:
        raise APIError("Failed to update announcement", 500, "UPDATE_FAILED")
    
    return jsonify(ErrorHandler.create_success_response(
        message=f"Announcement {dossier_id} status updated to {new_status}"
    ))

@improved_routes.route('/api/v2/open-url', methods=['POST'])
@handle_api_errors
@validate_json_input(['url'])
async def open_url_v2():
    """Securely open URL in browser"""
    data = request.get_json()
    url = data['url']
    
    # Validate and safely open URL
    if not SecurityValidator.safe_open_url(url):
        raise APIError("Invalid or unsafe URL", 400, "INVALID_URL")
    
    return jsonify(ErrorHandler.create_success_response(
        message="URL opened successfully"
    ))

@improved_routes.route('/api/v2/open-directory', methods=['POST'])
@handle_api_errors
@validate_json_input(['directory_path'])
async def open_directory_v2():
    """Securely open directory in file explorer"""
    data = request.get_json()
    directory_path = data['directory_path']
    base_dir = os.environ.get('BASE_DIR', os.getcwd())
    
    # Safely open directory
    if not SecurityValidator.safe_open_directory(directory_path, base_dir):
        raise APIError("Invalid or unsafe directory path", 400, "INVALID_PATH")
    
    return jsonify(ErrorHandler.create_success_response(
        message="Directory opened successfully"
    ))

@improved_routes.route('/api/v2/file-exists', methods=['POST'])
@handle_api_errors
@validate_json_input(['file_path'])
async def check_file_exists_v2():
    """Check if file exists securely"""
    data = request.get_json()
    file_path = data['file_path']
    base_dir = os.environ.get('BASE_DIR', os.getcwd())
    
    # Validate and check file path
    safe_path = SecurityValidator.sanitize_path(file_path, base_dir)
    if not safe_path:
        raise APIError("Invalid file path", 400, "INVALID_PATH")
    
    exists = os.path.exists(safe_path)
    
    return jsonify(ErrorHandler.create_success_response(
        data={"exists": exists, "path": safe_path}
    ))

def _is_excluded(annonce: dict, exclusion_config: dict) -> bool:
    """Check if announcement should be excluded based on criteria"""
    try:
        exclude_rules = exclusion_config.get('exclude', [])
        for rule in exclude_rules:
            for key, values in rule.items():
                if annonce.get(key) in values:
                    return True
        return False
    except Exception as e:
        logger.warning(f"Error checking exclusion criteria: {e}")
        return False

# Utility function to run async routes in Flask
def run_async(f):
    """Helper to run async functions in Flask routes"""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(f(*args, **kwargs))
    return wrapper

# Apply async wrapper to all async routes
for rule in improved_routes.url_map.iter_rules():
    view_func = improved_routes.view_functions.get(rule.endpoint)
    if view_func and asyncio.iscoroutinefunction(view_func):
        improved_routes.view_functions[rule.endpoint] = run_async(view_func)
