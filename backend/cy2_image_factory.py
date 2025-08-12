import tkinter as tk

from cy2_image_process import image_process

def create_image_processor(root, config):
    """
    Factory function that creates the appropriate image processor based on the specified type
    """
    processor_type = config.get('processor_type', 'explorer')
    # Import here to avoid circular imports
    return image_process(root, config)
    # if processor_type == 'explorer':
    #     # Import only when needed
    #     return explorer_process(root, config)
    # elif processor_type == 'collecter':
    #     return image_process(root, config)
    # else:
    #     # Default to explorer image processor if type is unknown
    #     print(f"[WARNING] Unknown processor type: {processor_type}, using explorer")
    #     return explorer_process(root, config)