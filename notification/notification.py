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

    def notifyEvent(self,title,message):
        self.api.notifyEvent(title,message)