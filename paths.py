from cookies import *
import os
import tkinter as tk
from tkinter import filedialog

def GetRoot():
    root_dir = os.getenv("ANNONCES_FILE_DIR")
    newroot=get_cookie_value("current_dossier")
    print(f"dbg5698: newroot = {newroot}")
    if os.path.exists(newroot):
        root_dir = newroot
    root_dir = root_dir.replace('\\', '/') 
    print(f"dbg5698: ANNOUNCES_FILE_DIR = {root_dir}")
    return root_dir

def GetDirFilter():
    print("dbg647 Get Dir Filter")
    path_filter =os.getenv("ANNONCES_DIR_FILTER")
    print("dbg648 path_filter",path_filter)
    dirroot = GetRoot()
    print("dbg648 dirroot",dirroot)
    
    new_path=os.path.join(dirroot,  path_filter)
    print("dbg649 filter dir = ",new_path)
    new_path = new_path.replace('\\', '/') 
    return new_path



def GetDirState():
    path_State =os.getenv("ANNONCES_DIR_STATE")
    dirroot = GetRoot()
    new_path=os.path.join(dirroot,  path_State)
    #print("dbg649 filter dir = ",new_path)
    new_path = new_path.replace('\\', '/') 
    return new_path

def GetDirCRQ():
    path_CRQ =os.getenv("DIR_CRQ_FILE")
    dirroot = GetRoot()
    new_path=os.path.join(dirroot,  path_CRQ)
    #print("dbg649 filter dir = ",new_path)
    new_path = new_path.replace('\\', '/') 
    return new_path


def GetDirREA():
    path_REA =os.getenv("DIR_REA_FILE")
    dirroot = GetRoot()
    new_path=os.path.join(dirroot,  path_REA)
    #print("dbg649 filter dir = ",new_path)
    new_path = new_path.replace('\\', '/') 
    return new_path


def buildAllPaths():
    ''' repertoire principal des dossiers'''
    dirroot = GetRoot()
    MakeNecessariesDir(dirroot)
    ''' Repertoire des criteres d'exclusion '''
    dirstate= GetDirState()
    MakeNecessariesDir(dirstate)
    '''repertoire des requetes pour extraire les infos de classements'''
    DirCRQ = GetDirCRQ()
    MakeNecessariesDir(DirCRQ)
    
    '''repertoire des realisations'''
    DirREA = GetDirREA()
    MakeNecessariesDir(DirREA)
    
    
    
    
def MakeNecessariesDir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    
