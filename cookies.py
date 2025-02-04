from flask import request, make_response, Blueprint, jsonify
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cookies = Blueprint('cookies', __name__)

@cookies.route('/get_current_instruction_cookie', methods=['POST'])
def get_current_instruction_cookie():
    cookie_name = request.json.get('cookie_name')  # Changed to get from JSON body
    cookies = request.cookies
    Value = cookies.get(cookie_name)
    return jsonify({cookie_name: Value})  # Return the cookie name and value

@cookies.route('/set_current_instruction_cookie', methods=['POST'])
def set_current_instruction_cookie():
    cookie_value = request.json.get('current_instruction')
    max_age = 60 * 60 * 24 * 30  # Cookie will be valid for 30 days

    response = make_response(jsonify({"message": "Cookie set successfully"}))  # Include JSON message in response
    response.set_cookie('current_instruction', cookie_value, max_age=max_age)
    print(f"dbg5643 current_instruction :{cookie_value}")
    return response  # Ensure the response is returned

@cookies.route('/get_cookie', methods=['POST'])
def get_cookie():
    cookie_name = request.json.get('cookie_name')  # Changed to get from JSON body
    cookies = request.cookies
   
    Value = cookies.get(cookie_name)
    logger.info(f"dbg5641 cookies :{cookie_name} value = {Value}" )
    return jsonify({cookie_name: Value})  # Return the cookie name and value