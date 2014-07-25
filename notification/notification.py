#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys


class notification:

    def __init__(self,params):
        dirname = os.path.dirname(__file__)
        
        notifyType = params['type']

        if notifyType == 'email':
            sys.path.append(dirname + "/emailsmtp/")
            import emailsmtp
            self.api = emailsmtp.EmailSMTP(params)

    def startedBackingUpDisc(self,discName):
        self.api.startedBackingUpDisc(discName)

    def endedBackingUpDisc(self,discName):
        self.api.endedBackingUpDisc(discName)
        
    def startedRippingTracks(self,tracks,discName):
        self.api.startedRippingTracks(tracks,discName)
        
    def finishedRippingTracks(self,tracks,discName):
        self.api.finishedRippingTracks(tracks,discName)
