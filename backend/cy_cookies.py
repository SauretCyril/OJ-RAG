from flask import request,  Blueprint, jsonify
import logging
import json
import os

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cy_cookies = Blueprint('cy_cookies', __name__)
need_reload=True
# Define the path to the JSON file
data_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(data_directory, exist_ok=True)
json_file_path = os.path.join(data_directory, 'cookies.json')

@cy_cookies.route('/save_cookie', methods=['POST'])
def save_cookie():
    global cookies_data
    cookie_value = request.json.get('cookie_value')
    cookie_name = request.json.get('cookie_name')
    
    if cookie_value is None or cookie_name is None:
        return jsonify({"error": "cookie_name and cookie_value are required"}), 400

    # Load existing cookies from the JSON file
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as file:
            cookies_data = json.load(file)
    else:
        cookies_data = {}

    # Save the new cookie
    cookies_data[cookie_name] = cookie_value

    # Write the updated cookies back to the JSON file
    with open(json_file_path, 'w') as file:
        json.dump(cookies_data, file)
   
    #logger.info(f"dbg5642 Cookie saved: {cookie_name} = {cookie_value}")
    
    return jsonify({"message": "done"})

@cy_cookies.route('/load_cookies', methods=['GET'])
def load_cookies():
    global cookies_data
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as file:
            cookies_data = json.load(file)
       #logger.info("Cookies loaded successfully from the JSON file.")
        return jsonify({"message": "Cookies loaded successfully", "cookies_data": cookies_data})
    else:
        #logger.warning("JSON file does not exist.")
        return jsonify({"error": "JSON file does not exist"}), 404

@cy_cookies.route('/get_cookie', methods=['POST'])
def get_cookie():
    cookie_name = request.json.get('cookie_name')
    if cookie_name is None:
        return jsonify({"error": "cookie_name is required"}), 400
 
        # Load existing cookies from the JSON file
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as file:
                cookies_data = json.load(file)
    else:
        cookies_data = {}
    
    # Get the cookie value
    cookie_value = cookies_data.get(cookie_name)
    #logger.info(f"dbg5641 cookies :{cookie_name} value = {cookie_value}")
        
    return jsonify({cookie_name: cookie_value})

#@cookies.route('/get_cookie_value', methods=['POST'])
def get_cookie_value(key_name):
    try:
        if key_name is None:
            return jsonify({"error": "key_name is required"}), 400
        
        # Initialiser cookies_data en lisant le fichier
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                cookies_data = json.load(file)
        else:
            cookies_data = {}
            
        # Get the value for the provided key
        value = cookies_data.get(key_name)
        #logger.info(f"dbg5643 Key: {key_name}, Value: {value}")
        return value
    except Exception as e:
        logger.error(f"Error-3345 getting cookie value for key {key_name}: {e}")
        return None

