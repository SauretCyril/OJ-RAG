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
    dirRea=GetDirREA()
    filerea=os.getenv("REA_FILE")
    realizations_file_path=os.path.join(dirRea,filerea)
    print ("dbg4452 : loading.file rea....",realizations_file_path)
    if os.path.exists(realizations_file_path):
        print("dbg4453 : loading.....", realizations_file_path)
        with open(realizations_file_path, 'r') as file:
            realizations_data = json.load(file)
    else:
        realizations_data = []
    response = jsonify({"status": "success", "realizations": realizations_data})

    print("dbg4444 : realizations_data", response)
    return response


@realizations.route('/save_realizations', methods=['POST'])
def save_realizations():
    realizations = request.json.get('data')
   
    if realizations is None:
        print("error-125 No realizations provided")
        return jsonify({"status": "error-125", "message": "No realizations provided"}), 400
    
    file_path = GetDirREA()
    print("dbg4458 : file_path",file_path)
    filerea=os.getenv("REA_FILE")
    print("dbg4459 : filerea",filerea)
    realizations_file_path=os.path.join(file_path,filerea)
    print("dbg4447 : realizations_file_path",realizations_file_path)

    # Create the file if it does not exist
    if not os.path.exists(realizations_file_path):
        with open(realizations_file_path, 'w') as file:
            json.dump([], file)

    with open(realizations_file_path, 'w') as file:
        json.dump(realizations, file)

    logger.info("Realizations saved successfully.")
    return jsonify({"status": "success"})

