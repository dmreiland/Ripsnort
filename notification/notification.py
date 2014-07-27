#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys


class notification:

    def __init__(self,params):
        self.apis = []

        dirname = os.path.dirname(__file__)
        
        notifyType = params['type']

        if 'email' in notifyType:
            sys.path.append(dirname + "/emailsmtp/")
            import emailsmtp
            self.apis.append( emailsmtp.EmailSMTP(params) )

        if 'macnotify' in notifyType:
            sys.path.append(dirname + "/macnotificationcenter/")
            import macnotificationcenter
            self.apis.append( macnotificationcenter.MacNotify(params) )

    def startedBackingUpDisc(self,discName):
        for api in self.apis:
            api.startedBackingUpDisc(discName)

    def endedBackingUpDisc(self,discName):
        for api in self.apis:
            api.endedBackingUpDisc(discName)
        
    def startedRippingTracks(self,tracks,discName):
        for api in self.apis:
            api.startedRippingTracks(tracks,discName)
        
    def finishedRippingTracks(self,tracks,discName):
        for api in self.apis:
            api.finishedRippingTracks(tracks,discName)
