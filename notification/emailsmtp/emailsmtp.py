#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailSMTP:
    def __init__(self,params):
        self.server = params['smtp_server']
        self.username = params['smtp_username']
        self.password = params['smtp_password']
        self.port = params['smtp_port']
        self.destination_email = params['smtp_destination_email']
        self.source_email = params['smtp_source_email']
        
        logging.debug('EmailSMTP initialized with config: ' + str(params))
        
    def __repr__(self):
        return "<EmailSMTP>"

    def startedBackingUpDisc(self,discName):
        m = MIMEText(discName)

        m['Subject'] = 'Ripsnort - backup ' + discName + ' started'
        m['From'] = self.source_email
        m['To'] = self.destination_email
        
        self._sendMessage(m.as_string())

    def finishedBackingUpDisc(self,discName):
        m = MIMEText(discName)

        m['Subject'] = 'Ripsnort - backup ' + discName + ' finished'
        m['From'] = self.source_email
        m['To'] = self.destination_email
        
        self._sendMessage(m.as_string())
        
    def startedRippingTracks(self,tracks,discName):
        message = "Started ripping tracks: <br>\n"

        for track in tracks:
            message += "  <strong>" + track.outputFileName + "</strong>, " + str(track.chapters) + "chapters, " + str(track.durationS/60) + "minutes<br>\n"

        m = MIMEMultipart('alternate')
        m.attach( MIMEText(message, 'html') )

        m['Subject'] = 'Ripsnort - ripping ' + discName + ' started'
        m['From'] = self.source_email
        m['To'] = self.destination_email
        
        self._sendMessage(m.as_string())
        
    def finishedRippingTracks(self,tracks,discName,ripTracksDict={}):
        message = "Finished ripping tracks: <br><br>\n"
        
        if ripTracksDict is None:
            message += "  <strong> Failed to rip any disc tracks </strong>"
        elif len(ripTracksDict.values()) == 0:
            message += "  <strong> Failed to rip any disc tracks </strong>"
        else:
            ripTracksOrderedList = ripTracksDict.values()
            
            allTracksHaveEpisodeNumber = True
            
            for mediaObj in ripTracksOrderedList:
                if not hasattr(mediaObj,'episode_number'):
                    allTracksHaveEpisodeNumber = False

            if allTracksHaveEpisodeNumber:
                ripTracksOrderedList.sort(key=lambda x: x.episode_number)
                ripTracksOrderedList.reverse()

            for mediaObj in ripTracksOrderedList:
                
                track = None
                
                for key in ripTracksDict.keys():
                    mediaObjCmp = ripTracksDict[key]
                    if mediaObjCmp == mediaObj:
                        track = key

                message += "  <strong>" + str(track.filepath) + "</strong>, " + str(track.chapters) + "chapters, " + str(track.durationS/60) + "minutes<br>\n"

                if mediaObj is None:
                    message += "  <strong> Failed to find a match for this video file </strong>"
                else:
                    message += str(mediaObj.title) + " (" + str(mediaObj.production_year) + ") <br>\n"

                    if hasattr(mediaObj,'episode_number') and mediaObj.episode_number is not None:
                        message += "Episode: " + str(mediaObj.episode_number) + "<br>\n"
                    if hasattr(mediaObj,'episode_title') and mediaObj.episode_title is not None:
                        message += "Episode Title: " + str(mediaObj.episode_title) + "<br>\n"
                    if hasattr(mediaObj,'season_number') and mediaObj.season_number is not None:
                        message += "Season: " + str(mediaObj.season_number) + "<br>\n"

                    message += mediaObj.plot_outline + "<br>\n"
                    message += "Genres: " + " ".join( mediaObj.genres ) + "<br>\n"

                    if mediaObj.public_url is not None:
                        message += "<a href=" + mediaObj.public_url + ">Public link</a>"

                    message += "<br><hr><br>\n"

        m = MIMEMultipart('alternate')
        m.attach( MIMEText(message, 'html') )

        m['Subject'] = 'Ripsnort - ripping ' + discName + ' finished'
        m['From'] = self.source_email
        m['To'] = self.destination_email
        
        self._sendMessage(m.as_string())

    def failure(self,discName,errorMessage):
        m = MIMEMultipart('alternate')
        m.attach( MIMEText(errorMessage, 'html') )

        m['Subject'] = 'Ripsnort ' + discName + ' error'
        m['From'] = self.source_email
        m['To'] = self.destination_email

        self._sendMessage(m.as_string())

    def _sendMessage(self,message):
        logging.info('Sending email to \'' + str(self.destination_email) + '\'')
        logging.info('Sending email: ' + message)
        self.smtp = smtplib.SMTP_SSL(self.server,self.port)
        self.smtp.login(self.username,self.password)
        self.smtp.sendmail(self.source_email,self.destination_email,message)
        self.smtp.quit()


def test(email_source,email_password,email_server):
     email_port = 465
     s = EmailSMTP({'smtp_server':email_server,'smtp_username':email_source,'smtp_password':email_password,'smtp_port':email_port,'smtp_source_email':email_source,'smtp_destination_email':email_source})
     s.startedBackingUpDisc('DiscName')
     s.finishedBackingUpDisc('DiscName')
     s.startedRippingTracks([],'DiscName')

     import os
     import sys
     dirname = os.path.dirname(os.path.realpath( __file__ ))

     sys.path.append( os.path.join(dirname,"..","..","scraper") )
     import MediaContent
     
     m = MediaContent.MediaContent()
     m.title = 'The Ant Bully'
     m.production_year = 2006
     m.plot_outline = """Plot line movie"""
     m.genres = ['Comedy','Animation']
     m.public_url = 'http://www.imdb.com/title/tt0429589'

     
     s.finishedRippingTracks([],'DiscName',[m])


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test()

