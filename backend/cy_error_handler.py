"""
Centralized error handling and response utilities
"""
import logging
import traceback
from functools import wraps
from flask import jsonify, request
from typing import Dict, Any, Optional, Tuple

# Configure logger
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom API exception"""
    def __init__(self, message: str, status_code: int = 500, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def create_error_response(
        message: str, 
        status_code: int = 500, 
        error_code: str = None,
        details: Dict[str, Any] = None
    ) -> Tuple[Dict[str, Any], int]:
        """Create standardized error response"""
        response = {
            "status": "error",
            "message": message,
            "error_code": error_code or f"ERR_{status_code}",
            "timestamp": str(int(time.time()))
        }
        
        if details:
            response["details"] = details
            
        logger.error(f"API Error: {error_code} - {message}", extra={
            "status_code": status_code,
            "details": details,
            "endpoint": request.endpoint if request else None
        })
        
        return response, status_code
    
    @staticmethod
    def create_success_response(
        data: Any = None, 
        message: str = "Success",
        meta: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create standardized success response"""
        response = {
            "status": "success",
            "message": message
        }
        
        if data is not None:
            response["data"] = data
            
        if meta:
            response["meta"] = meta
            
        return response

def handle_api_errors(f):
    """Decorator for consistent error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            return ErrorHandler.create_error_response(
                e.message, 
                e.status_code, 
                e.error_code
            )
        except ValueError as e:
            return ErrorHandler.create_error_response(
                f"Invalid input: {str(e)}", 
                400, 
                "INVALID_INPUT"
            )
        except FileNotFoundError as e:
            return ErrorHandler.create_error_response(
                f"File not found: {str(e)}", 
                404, 
                "FILE_NOT_FOUND"
            )
        except PermissionError as e:
            return ErrorHandler.create_error_response(
                f"Permission denied: {str(e)}", 
                403, 
                "PERMISSION_DENIED"
            )
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            return ErrorHandler.create_error_response(
                "An unexpected error occurred", 
                500, 
                "INTERNAL_ERROR"
            )
    return decorated_function

def validate_json_input(required_fields: list = None):
    """Decorator to validate JSON input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                raise APIError("Content-Type must be application/json", 400, "INVALID_CONTENT_TYPE")
            
            data = request.get_json()
            if not data:
                raise APIError("Request body must contain valid JSON", 400, "INVALID_JSON")
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    raise APIError(
                        f"Missing required fields: {', '.join(missing_fields)}", 
                        400, 
                        "MISSING_FIELDS"
                    )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

import time
