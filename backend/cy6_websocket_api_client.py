#This is an example that uses the websockets api to know when a prompt execution is done
#Once the prompt execution is done it downloads the images using the /history endpoint

import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse
from cy6_file import load_json,log_json
import os
from urllib import request
import random

server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())

def socket_queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())


def socket_get_images(ws,prompt_id):
    try:
        output_paths = []
        base_dir_map = {
            "output": os.getenv("IMAGES_COLLECTE"),
            "temp": os.getenv("IMAGES_TRASH"),
            "input": os.getenv("IMAGES_CENTRAL"),
            "central": os.getenv("IMAGES_CENTRAL"),
        }
        default_base = os.getenv("IMAGES_COLLECTE")

        def resolve_path(image_info):
            filename = image_info.get('filename')
            if not filename:
                return None
            folder_type = image_info.get('type')
            base_dir = base_dir_map.get(folder_type) or default_base
            subfolder = image_info.get('subfolder') or ''
            parts = []
            if base_dir:
                parts.append(base_dir)
            if subfolder:
                normalized_subfolder = subfolder.replace('/', os.sep).strip()
                if normalized_subfolder:
                    parts.append(normalized_subfolder)
            parts.append(filename)
            try:
                return os.path.normpath(os.path.join(*parts))
            except TypeError:
                return None

        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break #Execution is done
            else:
                continue #previews are binary data

        history = get_history(prompt_id)[prompt_id]

        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]

            if 'images' in node_output:
                for image in node_output['images']:
                    resolved_path = resolve_path(image)
                    if resolved_path:
                        output_paths.append(resolved_path)
        return output_paths

    except Exception as exc:
        print(f"Get image Error: {exc}")
        return []


def update_workflow(filevalues,fileworkflow):
    print(f"dbg-4514 => open file workflow -- {fileworkflow }")
    #il faut ouvrir filevalues
    if  not os.path.exists(filevalues):
        raise ValueError(f"Invalid values file : {filevalues}")
    if  not os.path.exists(fileworkflow):
        raise ValueError(f"Invalid workflow file : {fileworkflow}")

    with open(filevalues, "r",encoding="utf-8") as f:
        values_json_data=f.read()
    
    print(f"dbg-4514 =>values ={values_json_data}")

    values=json.loads( values_json_data)

    data_updated={}
   
    try:
        # with open(file, "r",encoding="utf-8") as f:
        #     worflow_json_data=f.read()
        jsonf = load_json(fileworkflow)
       
        for val in values:
           
            typ = values[val]['type']
            node =values[val]['id']
            
            print (f"dbg-4514 = node {node} : type {typ}:")
            #print(f"............set value to node={node} - typ={typ}")
            #print(f"................value ={values[val]}")
            
            #data_updated.update(f"{#node}:{'type':{typ}}") # type: ignore
            #data_updated.update(f"{node}:{'value':{values[val]}}")
           
            match typ: 
                
                case "image":
                    jsonf[node]['inputs']['image'] =  values[val]['value']
                case "CLIPTextEncode":
                    jsonf[node]['inputs']['text'] =  values[val]['value']
                    print (f"dbg-4515-1 = ok")
                    
                case "prompt":
                    jsonf[node]['inputs']['text'] =  values[val]['value']

                    print (f"dbg-4515-2 = ok")
                case "seed" :
                    #seednum=124578
                    seednum = random.randint(0, 9999999)
                    jsonf[node]['inputs']['seed'] = seednum
                    values[val]['value'] = seednum
                    print (f"dbg-4515-3 = {str(seednum)} ")

                case "PortraitMasterStylePose.pose" :
                    jsonf[node]['inputs']['model_pose'] = values[val]['model_pose']
                case "BilboXPhotoPrompt.style" :
                    
                    #print(f"{jsonf[node]}")
                    '''  
                    jsonf[node]['inputs']['style'] = values[val]['style']
                    jsonf[node]['inputs']['framing'] = values[val]['framing']
                    jsonf[node]['inputs']['lighting'] = values[val]['lighting']
                    jsonf[node]['inputs']['camera_angle'] = values[val]['camera_angle']
                    jsonf[node]['inputs']['lenses'] = values[val]['lenses']
                    jsonf[node]['inputs']['filters_effects'] = values[val]['overexposed']
                    jsonf[node]['inputs']['photographers'] = values[val]['photographers'] 
                    '''
                case "SDXLPromptStylerbyMood" :
                    jsonf[node]['inputs']['style'] = values[val]['style']
                case "GoogleTranslateTextNode":
                    jsonf[node]['inputs']['text'] =  values[val]['text']
                case "LoraLoaderTagsQuery":
                    jsonf[node]['inputs']['lora_name'] =  values[val]['lora_name']
                case "SaveImage":
                    jsonf[node]['inputs']['filename_prefix'] =  values[val]['value']
                    print (f"dbg-4515-4 = {values[val]['value']} ")

                case "LoraInfo":
                     jsonf[node]['inputs']['lora_name'] =  values[val]['lora_name']
                case _:
                    print(f"Invalid type {typ}")
                    return
    except Exception as e:
        print("---Error---------------------------------------")
        print(f"update worflow Error: {e}")
        #log_json('current_workflow_data_updated',data_updated)
        # print ("\n")
        # print (file)
        # exit(None)
    
    #print (f"........END update node ----------------")  
    #log_json('current_workflow_data_updated',data_updated)
    return jsonf, values

    #set the text prompt for our positive CLIPTextEncode

#Run workflow and get images
def server_run_now(jsonf):
    try:
         ws = websocket.WebSocket()
         ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    except Exception:
         print(f"Error: {Exception}")
         exit(None) 
    
    result = get_images(ws, jsonf)
    return result


    
def server_get_prompt(ws,prompt,isList,node_id):
    print("sv:msg01")
    # ws = websocket.WebSocket()
    # ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    print(f"sv:msg02={prompt}")
    prompt_id = queue_prompt(prompt)['prompt_id']
    print(f"sv:msg03")
    output_text = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break #Execution is done
        else:
            continue #previews are binary data

    history = get_history(prompt_id)[prompt_id]
    if (isList):
        output=history['outputs'][node_id]['text']
    else: 
        output=history['outputs'][node_id]['text'][0]
        
    #output1=history['outputs'][node_id]
    # print(f"Output---------------------")
    # print(f"{output1}")
    # print(f"Output---------------------")  
    result={'0':{'prompt_id':prompt_id},
        '1':{'output':output}}
    return result
    #return 






def socket_queue_add(jsonf):
    # p = {"prompt": jsonf}
    # data = json.dumps(p).encode('utf-8')
    # req =  request.Request("http://127.0.0.1:8188/prompt", data=data)
    # request.urlopen(req)
    prompt_id = socket_queue_prompt(jsonf)['prompt_id']
    
    return prompt_id

def server_connect():
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    
    return ws


def workflow_is_running(ws,prompt_id):
    ret=False
    out = ws.recv()
    if isinstance(out, str):
        message = json.loads(out)
        if message['type'] == 'executing':
            data = message['data']
            if data['node'] is None and data['prompt_id'] == prompt_id:
                ret= True
    print(f"serveur : {ret}")
    return ret
       
           

def get_history_images(prompt_id):
    output_images = {}
    history = get_history(prompt_id)[prompt_id]
    for o in history['outputs']:
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            if 'images' in node_output:
                images_output = []
                for image in node_output['images']:
                    image_data = get_image(image['filename'], image['subfolder'], image['type'])
                    images_output.append(image_data)
                output_images[node_id] = images_output

    return output_images


def server_get_infLora(ws,prompt):
    print("sv:msg01")
    
    #print(f"sv:msg02={prompt}")
    prompt_id = queue_prompt(prompt)['prompt_id']
    #print(f"sv:msg03")
    output_text = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break #Execution is done
        else:
            continue #previews are binary data

    return  get_history(prompt_id)[prompt_id]['outputs']