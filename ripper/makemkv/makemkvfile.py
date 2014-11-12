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


class MakeMKVFile:
    def __init__(self,filePath):
        if MakeMKVFile._hasMakeMkvKeyExpired():
            raise Exception('MakeMKV license key has expired. Manually run makemkv to update the key. (AppPath:' + apppath.makemkvcon() +')')

        self.filePath = filePath
        
        self.mediaDiscTracks = []
        
        logging.debug('MakeMKVFile initialized with deviceID' + str(filePath))
        
    def __repr__(self):
        return "<MakeMKVFile " +self.filePath+ " >"
    
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
                cmdargs = [apppath.makemkvcon(),'-r','--noscan','mkv',ripType + ':' + str(self.filePath),str(track.trackNumber),pathSave]
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
            for track in tracks:
                filePath = os.path.join(pathSave,track.outputFileName)
                track = LocalTrackMkv(filePath)
                rippedTracks.append(track)

        return rippedTracks
        
    def ripAllTracks(self,pathSave):
        didRip = True
        
        if not os.path.isdir(pathSave):
            os.makedirs(pathSave)

        try:
           
            if '.' in self.filePath and self.filePath.split('.')[-1] == 'iso':
                ripType = 'iso'
            else:
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
