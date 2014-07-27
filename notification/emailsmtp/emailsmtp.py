#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import smtplib
from email.mime.text import MIMEText


class EmailSMTP:
    def __init__(self,params):
        self.server = params['smtp_server']
        self.username = params['smtp_username']
        self.password = params['smtp_password']
        self.port = params['smtp_port']
        self.destination_email = params['smtp_destination_email']
        self.source_email = params['smtp_source_email']
        
        logging.debug('EmailSMTP initialized with config: ' + str(params))

    def startedBackingUpDisc(self,discName):
        m = MIMEText(discName)

        m['Subject'] = 'Ripsnort - backup started'
        m['From'] = self.source_email
        m['To'] = self.destination_email
        
        self._sendMessage(m.as_string())

    def finishedBackingUpDisc(self,discName):
        m = MIMEText(discName)

        m['Subject'] = 'Ripsnort - backup finished'
        m['From'] = self.source_email
        m['To'] = self.destination_email
        
        self._sendMessage(m.as_string())
        
    def startedRippingTracks(self,tracks,discName):
        message = "Started ripping " + str(len(tracks)) + " tracks. \n"

        for track in tracks:
            message += "    -" + str(track)

        m = MIMEText(message)
        m['Subject'] = 'Ripsnort - ripping started'
        m['From'] = self.source_email
        m['To'] = self.destination_email
        
        self._sendMessage(m.as_string())
        
    def finishedRippingTracks(self,tracks,discName):
        message = "Finished ripping " + str(len(tracks)) + " tracks. \n"

        for track in tracks:
            message += "    -" + track.outputFileName + ", " + str(track.chapters) + "chapters, " + str(track.durationS/60) + "minutes\n"

        m = MIMEText(message)

        m['Subject'] = 'Ripsnort - ripping finished'
        m['From'] = self.source_email
        m['To'] = self.destination_email
        
        self._sendMessage(m.as_string())
        
    def _sendMessage(self,message):
        self.smtp = smtplib.SMTP_SSL(self.server,self.port)
        self.smtp.login(self.username,self.password)
        self.smtp.sendmail(self.source_email,self.destination_email,message)
        self.smtp.quit()
        
if __name__ == "__main__":
     email_source='myemail@gmail.com'
     email_password='mypassword'
     email_server='smtp.gmail.com'
     email_port=465
     
     s = EmailSMTP({'smtp_server':email_server,'smtp_username':email_source,'smtp_password':email_password,'smtp_port':email_port,'smtp_source_email':email_source,'smtp_destination_email':email_source})
     s.startedBackingUpDisc('test message')
     s.finishedBackingUpDisc('test message')
     s.startedRippingTracks([],'test message')
     s.finishedRippingTracks([],'test message')