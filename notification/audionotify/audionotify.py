#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import logging


class AudioNotify:
    def __init__(self,params):
        self.temporaryDirectory = None
        
        import platform

        platformName = platform.system().lower().strip()
        
        if platformName == 'darwin' or platformName == 'linux':
            self.temporaryDirectory = '/tmp/ripsnort'
            
        if not os.path.isdir(self.temporaryDirectory):
            os.makedirs(self.temporaryDirectory)
        
        self.pathSoundClipBackupStarted = None

        if params['audionotify_url_backupstarted']:
            url = params['audionotify_url_backupstarted']
            self.pathSoundClipBackupStarted = os.path.join(self.temporaryDirectory,'audionotify_url_backupstarted')

            if not os.path.isfile(self.pathSoundClipBackupStarted):
                AudioNotify._loadSoundUrlToFile(url,self.pathSoundClipBackupStarted)

        self.pathSoundClipBackupFinished = None

        if params['audionotify_url_backupfinished']:
            url = params['audionotify_url_backupfinished']
            self.pathSoundClipBackupFinished = os.path.join(self.temporaryDirectory,'audionotify_url_backupfinished')

            if not os.path.isfile(self.pathSoundClipBackupFinished):
                AudioNotify._loadSoundUrlToFile(url,self.pathSoundClipBackupFinished)

        self.pathSoundClipRipStarted = None

        if params['audionotify_url_ripstarted']:
            url = params['audionotify_url_ripstarted']
            self.pathSoundClipRipStarted = os.path.join(self.temporaryDirectory,'audionotify_url_ripstarted')

            if not os.path.isfile(self.pathSoundClipRipStarted):
                AudioNotify._loadSoundUrlToFile(url,self.pathSoundClipRipStarted)

        self.pathSoundClipRipFinished = None

        if params['audionotify_url_ripsfinished']:
            url = params['audionotify_url_ripsfinished']
            self.pathSoundClipRipFinished = os.path.join(self.temporaryDirectory,'audionotify_url_ripsfinished')

            if not os.path.isfile(self.pathSoundClipRipFinished):
                AudioNotify._loadSoundUrlToFile(url,self.pathSoundClipRipFinished)

        logging.debug('AudioNotify initialized with config: ' + str(params))

    def startedBackingUpDisc(self,discName):
        if self.pathSoundClipBackupStarted is not None:
            self._playSound( self.pathSoundClipBackupStarted )

    def finishedBackingUpDisc(self,discName):
        if self.pathSoundClipBackupFinished is not None:
            self._playSound( self.pathSoundClipBackupFinished )

    def startedRippingTracks(self,tracks,discName):
        if self.pathSoundClipRipStarted is not None:
            self._playSound( self.pathSoundClipRipStarted )

    def finishedRippingTracks(self,tracks,discName):
        if self.pathSoundClipRipFinished is not None:
            self._playSound( self.pathSoundClipRipFinished )
        
    @staticmethod
    def _loadSoundUrlToFile(urlLoad,fileToSave):
        import urllib2
        
        response = urllib2.urlopen(urlLoad).read()
        
        f = open(fileToSave,'w')
        f.write(response)
        f.close()

    def _playSound(self, soundFile):
        import platform

        platformName = platform.system().lower().strip()
        
        import subprocess

        #Can only run on Macs
        if platformName == 'darwin':
            subprocess.check_output(['afplay',soundFile])

        
if __name__ == "__main__":
     params = {}
     params['audionotify_url_backupstarted'] = 'http://soundbible.com/grab.php?id=1997&type=wav'
     params['audionotify_url_backupfinished'] = None
     params['audionotify_url_ripstarted'] = 'http://soundbible.com/grab.php?id=1997&type=wav'
     params['audionotify_url_ripsfinished'] = None

     m = AudioNotify(params)
     m.startedBackingUpDisc('MOVIENAME')
     m.finishedBackingUpDisc('MOVIENAME')
     m.startedRippingTracks([],'MOVIENAME')
     m.finishedRippingTracks([],'MOVIENAME')
