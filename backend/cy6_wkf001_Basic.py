import random
import sys


#sys.path.append('G:/G_WCS/Comfyui_api')
from  cy6_task_comfyui import comfyui_task
from  cy6_websocket_api_client import server_run_now,update_workflow

#seed aleatoire
class comfyui_basic_task(comfyui_task):
    #update json
   
    name = "run_now"
    seednum = random.randint(0, 9999999)

    def run_now(self,fileworkflow,filevalues):
        json, updated_values = update_workflow(fileworkflow,filevalues)
        self.update_values(updated_values)
        self.last_workflow = json
        #mise à jour api run_basic avec le json modifié
        result =server_run_now(json)
        images = result['1']['output']

        if (images):
            for node_id in images:
                for image_data in images[node_id]:
                    from PIL import Image
                    import io
                    image = Image.open(io.BytesIO(image_data))
                    #Voir le résultat
                    image.show()
                    #Sauver le résultat
                    #image.save(f"./output/glass bottole-{self.seednum}-{node_id}.png")
                    return image.name
    

values={
        "1": {
            "id": "6", #node 6 corresponding to the positive prompt
            "type": "prompt",
            "value": "beautiful scenery nature glass bottle landscape, , purple galaxy bottle,"
        },
        "2": {
            "id": "7", #node 7 corresponding to the negative prompt
            "type": "prompt",
            "value": "text, watermark"
        },
        "3": {
            "id": "3",#node 3 corresponding to Ksample
            "type": "seed",
            "value": random.randint(0,9999999)
        }
    }

# if __name__ == "__main__":
#     tsk1 =  comfyui_run_now()
#     #fileworkflow = "wk000_basic.json"
#     #filevalues = "wk000_basic_values.json"

#     fileworkflow = "wk001_ponyRealism.json"
#     filevalues = "wk001_ponyRealism_values.json"

#     tsk1.run_now(fileworkflow,filevalues)
