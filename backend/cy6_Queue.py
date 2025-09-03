import random
import sys

sys.path.append('G:/G_WCS/Comfyui_api')
from cy6_task_comfyui import comfyui_task
from cy6_websocket_api_client import queue_add,workflow_is_running,get_history_images,server_connect

#seed aleatoire

class comfyui_Queue(comfyui_task):
    
    file ="wkf001_api_basic.json"
    seednum =random.randint(0,9999999)
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
        "value": seednum
    }
}
    




#tsk1 =  comfyui_addToQueue()
#tsk1.addToQueue()