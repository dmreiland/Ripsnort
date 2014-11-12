#!/usr/bin/env python
# -*- coding: utf-8 -*-


import subprocess
import re
import json
import shutil
import logging
import sys
import os
import md5


dirname = os.path.dirname(__file__)

sys.path.append(os.path.join(dirname,"..",".."))
from disc_track import *
import apppath

sys.path.append(os.path.join(dirname,"..","..","utils"))
import inireader


class MakeMKVDir:
    def __init__(self,filePath):
        if MakeMKVDir._hasMakeMkvKeyExpired():
            raise Exception('MakeMKV license key has expired. Manually run makemkv to update the key. (AppPath:' + apppath.makemkvcon() +')')
    
        #TODO replace is a workaround til I figure out naming scheme for devices
        filePath = filePath.replace('/dev/disk','/dev/rdisk')
    
        self.filePath = filePath

        self.mediaDiscTracks = []
        
        logging.debug('MakeMKVDir initialized with filePath' + str(filePath))
        
    def __repr__(self):
        return "<MakeMKVDir " +self.filePath+ " >"
    
    def hasLocatedMediaTracks(self):
        return False
    
    def tracks(self):
        return self.mediaDiscTracks

    def ripTracks(self,tracks,pathSave):
        didRip = True
        
        if not os.path.isdir(pathSave):
            os.makedirs(pathSave)
            
        for track in tracks:
            try:
                outputFile = os.path.join(pathSave,track.outputFileName)

                if os.path.exists(outputFile):
                    os.remove(outputFile)
                    
                ripType = 'file'

                logging.info('Started ripping track: ' + str(track))
                cmdargs = [apppath.makemkvcon(),'-r','--noscan','mkv',ripType + ':' + str(self.filePath),pathSave]
                logging.debug('Running command: ' + ' '.join(cmdargs))
                exitCode = subprocess.call(cmdargs)
                
                if exitCode is not 0:
                    didRip = False
                
                nfoFile = track.outputFileName.replace('.mkv','.nfo')
                
                with open(os.path.join(pathSave,nfoFile), 'w') as outfile:
                    json.dump(track.serialize(), outfile)

            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to save track ' + str(track) + ', reason: **' + str(e.output) + '**' )
                didRip = False
        
        if didRip:
            rippedTracks = tracks
        
        return rippedTracks

    def ripAllTracks(self,pathSave):
        didRip = True
        
        if not os.path.isdir(pathSave):
            os.makedirs(pathSave)
            
        try:
            
            ripType = 'file'

            logging.info('Started ripping all tracks to: ' + str(pathSave))
            cmdargs = [apppath.makemkvcon(),'-r','--noscan','mkv',ripType + ':' + str(self.filePath),'all',pathSave]
            logging.debug('Running command: ' + ' '.join(cmdargs))
            exitCode = subprocess.call(cmdargs)
                
            if exitCode is not 0:
                didRip = False

        except subprocess.CalledProcessError as e:
            logging.error( 'Failed to save track ' + str(track) + ', reason: **' + str(e.output) + '**' )
            didRip = False
        
        rippedTracks = []
        
        if didRip:
            for fileName in os.listdir(pathSave):
                if fileName.lower().endswith('.mkv'):
                    filePath = os.path.join(pathSave,fileName)
                    track = LocalTrackMkv(filePath)
                    rippedTracks.append(track)
        
        return rippedTracks

    @staticmethod
    def _hasMakeMkvKeyExpired():
        hasExpired = False
    
        try:
            cmdargs = [apppath.makemkvcon(),'--noscan','-r','info']
            logging.debug('Running command: ' + ' '.join(cmdargs))
            cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd.wait()
            response = cmd.communicate()
            
            if 'enter a registration key to continue' in response[0].lower():
                hasExpired = True

        except subprocess.CalledProcessError as e:
            logging.error( 'Failed to call makemkv: ' + str(e.output) )
            sys.exit(1)
        
        return hasExpired


