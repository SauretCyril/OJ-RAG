import json 
 
def load_json(fileToOpen):
         #print(f"open file {file }")
         with open(fileToOpen, "r",encoding="utf-8") as f:
               worflow_json_data=f.read()
               jsonf=json.loads( worflow_json_data)
               return jsonf
           
def  save_json(fileToSave,data):
        with open(f"{fileToSave}", "w") as json_file:
            json.dump(data, json_file, indent=4)

def log_json(name,data):
   
    with open(f"G:/out/{name}.json", "w") as json_file:
            json.dump(data, json_file, indent=4)
            