import tkinter as tk

# Correction des importations
from cy2_image_process import image_process


def create_image_processor(root, config):
    """
    Factory function that creates the appropriate image processor based on the specified type
    """
    processor_type = config.get('processor_type', 'standard')
    # print(f"[INFO-012] Creating image processor of type: {processor_type}")
    # # Retourner le processeur adapté au type demandé
    # if processor_type == 'workflow':
    #     print(f"[INFO-012a] Creating workflow image processor")
    #     processor = images_workflow(root, config)
    # else:
    #     print(f"[INFO-012b] Creating standard image processor (type: {processor_type})")
    #     processor = image_process(root, config)
    processor = image_process(root, config)
    # IMPORTANT: Initialiser l'objet après sa création
    processor.initialize()
    
    return processor