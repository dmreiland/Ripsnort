#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import logging


class Ripper:

    def __init__(self,params,deviceID):
        dirname = os.path.dirname(os.path.realpath( __file__ ))
        
        scraperType = params['type']

        if scraperType.lower() == 'makemkv':
            sys.path.append(dirname + "/makemkv")
            import makemkv
            self.api = makemkv.MakeMKV(deviceID)
            
        logging.debug('Initialized with api: ' + str(self.api))
        
    def __repr__(self):
        return "<Ripper>"

    def ripDiscTracks(self,tracks,pathSave):
        return self.api.ripDiscTracks(tracks,pathSave)

    def ripDiscBackup(self,pathSave):
        return self.api.ripDiscBackup(pathSave)
    
    def discTracks(self):
        return self.api.discTracks()

