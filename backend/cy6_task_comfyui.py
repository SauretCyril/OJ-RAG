import sys
import json
import os
#sys.path.append('G:/G_WCS/Comfyui_api')
from cy6_file import log_json

from  cy6_websocket_api_client import update_workflow,workflow_is_running,queue_add,server_connect

#seed aleatoire
class comfyui_task:
    name="Default"
    workflowRoot ="data/Workflows"
    
    def update_values(self, values):
        self.values = values

    def updateWorkflow(self,fileworkflow,filevalues):
        fileworkflow = self.workflowRoot + "/" + fileworkflow
        filevalues = self.workflowRoot + "/" + filevalues

        if os.path.exists(fileworkflow):
            if os.path.exists(filevalues):

                #values = self.values
                json = update_workflow(filevalues,fileworkflow)
                return json
            else:
                raise ValueError("Invalid values.")
        else:
            raise ValueError("Invalid workflow file does not exist : " + fileworkflow)

    def log_values(self):
        log_json('02_value_to_update',self.values)
     
    def addToQueue(self):
        json = self.updateWorkflow(self.file,self.values)
        print("--------------------------------")
         
        print (self.file)
        print (self.values)
        print (json)
        print("--------------------------------")
        prompt_list=[]
        prompt_list.append(queue_add(json))
        #prompt_list.append(queue_add(json))

        nbqueue = len(prompt_list)
        ws = server_connect()
        nb=0
        print (f"nb workflows = {nbqueue}")

    
        while nb!=nbqueue:
            nb=0
            for promptId in prompt_list:
                if not workflow_is_running(ws,promptId):
                    nb=+1
            print(f"workflow : {promptId}  ->  {nb}/{nbqueue}")