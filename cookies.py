from flask import request, make_response, Blueprint, jsonify

cookies = Blueprint('cookies', __name__)
""" 
@cookies.route('/get_cookie', methods=['POST'])
def get_cookie():
    cookie_name = request.args.get('cookie_name')
    cookie_value = get_cookie_value(cookie_name)
    return jsonify(cookie_value)

def get_cookie_value(cookie_name):
    cookies = request.cookies
    Value=cookies.get(cookie_name)
    return Value
 """

@cookies.route('/set_cookie', methods=['POST'])
def set_cookie():
     
    cookie_name = request.args.get('cookie_name')
    cookie_value = request.args.get('cookie_value')
    print ("dbg5643 :"+ cookie_name)
    """  if cookie_value is None:
        raise ValueError(f"Cookie value for {cookie_name} is None")
    response = set_cookie_value(cookie_name, cookie_value)
    return response """

def set_cookie_value(cookie_name, value):
    response = make_response()
    # Log the cookie value before setting it
    print(f"dbg554 : Setting cookie: {cookie_name} = {value}")
    response.set_cookie(cookie_name, value)
    
    # Log the cookie value after setting it
    #print(f"dbg223 Cookie set: {cookie_name} = {response.headers.get('Set-Cookie')}")
    return response
