#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import re


class Ripper:

    def __init__(self,params,deviceID):
        dirname = os.path.dirname(os.path.realpath( __file__ ))
        
        scraperType = params['type']

        if scraperType.lower() == 'makemkv':
            sys.path.append(dirname + "/makemkv")
            import makemkv
            self.api = makemkv.makeMKV(deviceID)

    def ripDiscTracks(self,tracks,pathSave):
        return self.api.ripDiscTracks(tracks,pathSave)

    def ripDiscBackup(self,pathSave):
        return self.api.ripDiscBackup(pathSave)
    
    def formattedName(self):
        return self.api.formattedName()
    
    def discTracks(self):
        return self.api.discTracks()

