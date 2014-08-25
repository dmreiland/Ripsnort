#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import os
import sys
import shutil
import logging


def dictTypeConversion(dictionaryCheck):
    for key in dictionaryCheck:
        val = dictionaryCheck[key]
        if type(val) == type({}):
            val = dictTypeConversion(val)
        elif type(val) == type(''):
            val = val.lower().strip()
            valHasDots = len(val.split('.')) > 1
            
            floatVal = None
            
            try:
                floatVal = float(val)
            except:
                pass

            intVal = None
            
            try:
                intVal = int(val)
            except:
                pass
            
            if val == 'no' or val == 'false' or val == 'off':
                val = False
            elif val == 'yes' or val == 'true' or val == 'on':
                val = True
            elif valHasDots and floatVal is not None:
                val = floatVal
            elif intVal is not None:
                val = intVal
            elif val == 'none' or val == 'nil' or val == 'null':
                val = None
            else:
                #undo val changes
                val = dictionaryCheck[key]

        else:
            #value is not dict or string
            pass
            
        dictionaryCheck[key] = val
        
    return dictionaryCheck


def loadFile(configFile,convertNativeTypes=True):
    import ConfigParser
    
    logging.debug('Loading file: ' + str(configFile))

    config = ConfigParser.RawConfigParser()
    config.read(configFile)
    
    d = dict(config._sections)
    for k in d:
        d[k] = dict(config._defaults, **d[k])
        d[k].pop('__name__', None)
    
    logging.debug('Loaded dictionary: ' + str(d))
    
    if convertNativeTypes == True:
        d = dictTypeConversion(d)

    return d