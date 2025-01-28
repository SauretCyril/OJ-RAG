from cookies import *
import os
import tkinter as tk
from tkinter import filedialog

def GetRoot():
    root_dir = os.getenv("ANNONCES_FILE_DIR")
    """ cookie_current_dir =get_cookie_value("current_dir")
    print (f"dbg147: ANNONCES_FILE_DIR = {cookie_current_dir}")
    if cookie_current_dir!=None:
        root_dir=cookie_current_dir
        print(f"dbg251: Cookie find = {root_dir}")
    else:
        print(f"dbg253: Cookie save= {root_dir}")
        set_cookie_value("current_dir", root_dir) """
        
        
    #print(f"dbg001: ANNOUNCES_FILE_DIR = {root_dir}")
     
    return root_dir

def GetDirFilter():
    path_filter =os.getenv("ANNONCES_DIR_FILTER")
    new_path=os.path.join(GetRoot(),  path_filter)
    #print("dbg649 filter dir = ",new_path)
    new_path = new_path.replace('\\', '/') 
    return new_path



def GetDirState():
    path_State =os.getenv("ANNONCES_DIR_STATE")
    new_path=os.path.join(GetRoot(),  path_State)
    #print("dbg649 filter dir = ",new_path)
    new_path = new_path.replace('\\', '/') 
    return new_path

def GetDirCRQ():
    path_CRQ =os.getenv("DIR_CRQ_FILE")
    new_path=os.path.join(GetRoot(),  path_CRQ)
    #print("dbg649 filter dir = ",new_path)
    new_path = new_path.replace('\\', '/') 
    return new_path



