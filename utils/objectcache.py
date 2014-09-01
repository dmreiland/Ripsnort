#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import shelve
import tempfile


def _openShelveDbForCaller(caller):
    tempDir = os.path.join(tempfile.gettempdir(),'ripsnort','cache')
    tempFile = os.path.join(tempDir,caller)
    
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

