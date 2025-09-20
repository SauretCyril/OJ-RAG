import sys
import json
import os
#sys.path.append('G:/G_WCS/Comfyui_api')
from cy6_file import log_json
from  cy6_websocket_api_client import update_workflow,socket_queue_prompt,server_connect,workflow_is_running,socket_get_images

#seed aleatoire
class comfyui_task:
    name="Default"
    
    def update_values(self, values):
        self.values = values

   

    def log_values(self):
        log_json('02_value_to_update',self.values)
     
    def addToQueue(self,fileworkflow,filevalues):
        json, updated_values = update_workflow(filevalues,fileworkflow)
        self.update_values(updated_values)
        self.last_workflow = json

        prompt_list=[]
        prompt_id = socket_queue_prompt(json)['prompt_id']
        prompt_list.append(prompt_id)

        nbqueue = len(prompt_list)
        self.ws = server_connect()
        nb=0
        print (f"nb workflows = {nbqueue}")

    
        while nb!=nbqueue:
            nb=0
            for promptId in prompt_list:
                if not workflow_is_running(self.ws ,promptId):
                    nb+=1
            print(f"workflow : {promptId}  ->  {nb}/{nbqueue}")
        return promptId

    def GetImages(self, key):
        output_images = socket_get_images(self.ws, key)
        self.output_images = output_images
        return output_images
