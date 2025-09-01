
import sys
import json
sys.path.append('G:/G_WCS/Comfyui_api')
from utils.file import log_json
from  Client.websocket_api_client import update_workflow,workflow_is_running,queue_add,server_connect

#seed aleatoire
class comfyui_task:
     
     name="Default"
     workFlowRoot ="G:/G_WCS/Comfyui_api/WorkFlowFile"
     

     def update_values(self,values):
        self.values=values
    
     def updateWorkflow(self,file,values):

         json = update_workflow(values,self.workFlowRoot + "/" + file)
         #print(f"{json}")
         return json
        
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