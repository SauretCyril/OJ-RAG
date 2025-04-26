from cookies import *
import os
import tkinter as tk
from tkinter import filedialog

def GetRoot():
    root_dir = os.getenv("ANNONCES_FILE_DIR")
    newroot = get_cookie_value("current_dossier")
    #print(f"dbg5698: newroot = {newroot}")
    if os.path.exists(newroot):
        root_dir = newroot
    root_dir = root_dir.replace('\\', '/') 
    #print(f"dbg5698: ANNOUNCES_FILE_DIR = {root_dir}")
    return root_dir

def GetDirFilter():
    #print("dbg647 Get Dir Filter")
    path_filter =os.getenv("ANNONCES_DIR_FILTER")
    #print("dbg648 path_filter",path_filter)
    dirroot = GetRoot()
    #print("dbg648 dirroot",dirroot)
    
    new_path=os.path.join(dirroot,path_filter)
    
    new_path = os.path.join(dirroot, path_filter)
    new_path = new_path.replace('\\', '/')
    #print("dbg649 filter dir = ", new_path)
    return new_path



def GetDirState():
    path_State =os.getenv("ANNONCES_DIR_STATE")
    #dirroot = GetRoot()
    #new_path=os.path.join(dirroot,path_State)
    #print("dbg659filter dir = ",new_path)
    new_path =  path_State.replace('\\', '/') 
    return new_path

def GetDirCRQ(dir):
    path_CRQ =os.getenv(dir)
    dirroot = GetRoot()
    new_path=os.path.join(dirroot,path_CRQ)
    print("dbg652 filter dir = ",new_path)
    new_path = new_path.replace('\\', '/') 
    return new_path


def GetDirREA():
    path_REA =os.getenv("DIR_REA_FILE")
    dirroot = GetRoot()
    #print("dbg651d root = ",dirroot)
    new_path=os.path.join(dirroot,path_REA)
    new_path = new_path.replace('\\', '/')
    #print("dbg651c realisation dir = ",new_path)
    return new_path

def GetDirSoft_Sk():
    path_soft_sk = os.getenv("DIR_SOFT_SK_FILE")
    dirroot = GetRoot()
    #print("dbg651a root = ",dirroot)
    new_path=os.path.join(dirroot,path_soft_sk)
    new_path = new_path.replace('\\', '/')
    #print("dbg651b realisation dir = ",new_path)
    return new_path


def GetOneDir(envName):
    dirroot = GetRoot()
    #print("dbg651f root = ",dirroot)
    
    path = os.getenv(envName)
    print(f"dbg651e path de {envName} = ",path )
    
    new_path=os.path.join(dirroot,path)
    new_path = new_path.replace('\\', '/')
    
    #print(f"dbg651g GetOneDir ({envName}) => ",new_path)
    return new_path



def buildAllPaths():
    ''' repertoire principal des dossiers'''
    dirroot = GetRoot()
    MakeNecessariesDir(dirroot)
    ''' Repertoire des criteres d'exclusion '''
    dirstate= GetDirState()
    MakeNecessariesDir(dirstate)
    '''repertoire des requetes pour extraire les infos de classements'''
    #DirCRQ = GetDirCRQ()
    #MakeNecessariesDir(DirCRQ)
    
    '''repertoire des realisations'''
    DirREA = GetDirREA()
    MakeNecessariesDir(DirREA)
    
def GetDirRQ():
    path_request =os.getenv("DIR_RQ_FILE")
    #dirroot = GetRoot()
    #print("dbg234d root = ",dirroot)
    #new_path=os.path.join(dirroot,path_request)
    new_path = path_request.replace('\\', '/')
    #print("dbg234c requests dir = ",new_path)
    return new_path
    
    
def MakeNecessariesDir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    
