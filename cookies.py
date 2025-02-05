from flask import request, make_response, Blueprint, jsonify
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cookies = Blueprint('cookies', __name__)


@cookies.route('/save_cookie', methods=['POST'])
def save_cookie():
    cookie_value = request.json.get('cookie_value')  # Fix typo here
    cookie_name = request.json.get('cookie_name')
    max_age = 60 * 60 * 24 * 30  # Cookie will be valid for 30 days

    if cookie_value is None or cookie_name is None:
        return jsonify({"error": "cookie_name and cookie_value are required"}), 400

    response = make_response(jsonify({"message": "done"}))  # Include JSON message in response
    response.set_cookie(cookie_name, cookie_value, max_age=max_age)
    logger.info(f"dbg5642 Cookie set: {cookie_name} = {cookie_value}")
    return response  # Ensure the response is returned

@cookies.route('/get_cookie', methods=['POST'])
def get_cookie():
    cookie_name = request.json.get('cookie_name')  # Changed to get from JSON body
    cookies = request.cookies
   
    Value = cookies.get(cookie_name)
    logger.info(f"dbg5641 cookies :{cookie_name} value = {Value}" )
    return jsonify({cookie_name: Value})  # Return the cookie name and value
