#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import logging


class Ripper:

    def __init__(self,params,ripPath,ripType):
        dirname = os.path.dirname(os.path.realpath( __file__ ))
        
        scraperType = params['type']

        if scraperType.lower() == 'makemkv':
            sys.path.append(dirname + "/makemkv")
            if ripType == 'disc':
                import makemkvdisc
                self.api = makemkvdisc.MakeMKVDisc(ripPath)
            elif ripType == 'dir':
                import makemkvdir
                self.api = makemkvdir.MakeMKVDir(ripPath)
            elif ripType == 'file':
                import makemkvfile
                self.api = makemkvfile.MakeMKVFile(ripPath)

        logging.debug('Initialized with api: ' + str(self.api))
        
    def __repr__(self):
        return "<Ripper>"
    
    def tracks(self):
        return self.api.tracks()
        
    def hasLocatedMediaTracks(self):
        return self.api.hasLocatedMediaTracks()

    def ripTracks(self,tracks,pathSave):
        return self.api.ripTracks(tracks,pathSave)
    
    def ripAllTracks(self,pathSave):
        return self.api.ripAllTracks(pathSave)




