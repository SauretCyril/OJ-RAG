from flask import Flask, request, jsonify, render_template,Blueprint
import os
import json
import logging
from paths import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

realizations = Blueprint('realisations', __name__)



@realizations.route('/read_realizations', methods=['GET'])
def read_realizations():
    
    realizations_file_path=GetDirREA()
    if os.path.exists(realizations_file_path):
        with open(realizations_file_path, 'r') as file:
            realizations_data = json.load(file)
    else:
        realizations_data = []

    return jsonify({"status": "success", "realizations": realizations_data})

@realizations.route('/save_realizations', methods=['POST'])
def save_realizations():
    realizations_file_path=GetDirREA()
    if realizations is None:
        return jsonify({"status": "error", "message": "No realizations provided"}), 400

    with open(realizations_file_path, 'w') as file:
        json.dump(realizations, file)

    return jsonify({"status": "success"})

