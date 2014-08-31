#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import logging


class Notification:

    def __init__(self,params):
        self.apis = []

        dirname = os.path.dirname(__file__)
        
        notifyType = params['type']

        if 'email' in notifyType:
            sys.path.append(dirname + "/emailsmtp/")
            import emailsmtp
            self.apis.append( emailsmtp.EmailSMTP(params) )

        if 'localnotify' in notifyType:
            sys.path.append(dirname + "/localnotify/")
            import localnotify
            self.apis.append( localnotify.LocalNotify(params) )

        if 'audionotify' in notifyType:
            sys.path.append(dirname + "/audionotify/")
            import audionotify
            self.apis.append( audionotify.AudioNotify(params) )
            
        logging.debug("Initialized with apis: " + str(self.apis))

    def startedBackingUpDisc(self,discName):
        for api in self.apis:
            api.startedBackingUpDisc(discName)

    def endedBackingUpDisc(self,discName):
        for api in self.apis:
            api.endedBackingUpDisc(discName)
        
    def startedRippingTracks(self,tracks,discName):
        for api in self.apis:
            api.startedRippingTracks(tracks,discName)
        
    def finishedRippingTracks(self,tracks,discName,ripTracksDict={}):
        for api in self.apis:
            api.finishedRippingTracks(tracks,discName,ripTracksDict)

    def failure(self,discName,errorMessage):
        for api in self.apis:
            api.failure(discName,errorMessage)
