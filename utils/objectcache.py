#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import shelve
import tempfile


def pathTemporary(subFolder=None):
    tempDir = tempfile.gettempdir()
    
    if subFolder is not None:
        tempDir = os.path.join(tempDir,subFolder)
        
    if os.path.exists(tempDir) == False:
        os.makedirs(tempDir)
    
    return tempDir


def _openShelveDbForCaller(caller):
    tempDir = os.path.join(tempfile.gettempdir(),'cache')
    tempFile = os.path.join(tempDir,caller+'.db')
    
    if os.path.exists(tempDir) == False:
        os.makedirs(tempDir)
    
    s = shelve.open(tempFile)
    
    return s


def saveObject(caller,key,obj):
    didSave = True
    
    try:
        s = _openShelveDbForCaller(caller)
        s[key] = obj
    except e:
        didSave = False
    
    return didSave


def searchCache(caller,key):
    retObject = None
    
    try:
        s = _openShelveDbForCaller(caller)    
        retObject = s[key]
    except:
        pass

    return retObject

