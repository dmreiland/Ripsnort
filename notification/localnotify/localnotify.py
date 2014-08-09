#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging


class LocalNotify:
    def __init__(self,params):
        logging.debug('LocalNotify initialized with config: ' + str(params))
        
    def __repr__(self):
        return "<LocalNotify>"

    def startedBackingUpDisc(self,discName):
        title = "Started backing up: " + discName        
        self._notify(title,'','')

    def finishedBackingUpDisc(self,discName):
        title = "Finished backing up: " + discName        
        self._notify(title,'','')

    def startedRippingTracks(self,tracks,discName):
        title = "Started ripping: " + discName
        
        totalDurationMins = 0

        for track in tracks:
            totalDurationMins += int(track.durationS/60)
        
        subtitle = str(len(tracks)) + " tracks, total duration " + str(totalDurationMins) + " minutes"
        
        self._notify(title,subtitle,'')

    def finishedRippingTracks(self,tracks,discName,mediaObjects=[]):
        title = "Finished ripping: " + discName
        
        totalDurationMins = 0

        for track in tracks:
            totalDurationMins += int(track.durationS/60)
        
        subtitle = str(len(tracks)) + " tracks, total duration " + str(totalDurationMins) + " minutes"
        message = "Tracks: \n"

        for track in tracks:
            message += "  " + track.outputFileName + ", " + str(track.chapters) + ", " + str(track.durationS/60) + "minutes\n"
        
        self._notify(title,subtitle,message)

    def failure(self,discName,errorMessage):
        self._notify('Error with disc: ' + discName,'',errorMessage)

    def _notify(self, title, subtitle, info_text):
        import platform

        platformName = platform.system().lower().strip()

        if platformName == 'darwin':
            import Foundation
            import objc
            import AppKit

            NSUserNotification = objc.lookUpClass('NSUserNotification')
            NSUserNotificationCenter = objc.lookUpClass('NSUserNotificationCenter')
            NSImage = objc.lookUpClass('NSImage')
            NSURL = objc.lookUpClass('NSURL')

            notification = NSUserNotification.alloc().init()

            if title is not None:
                notification.setTitle_(title)

            if subtitle is not None:
                notification.setSubtitle_(subtitle)
            
            if info_text is not None:
                notification.setInformativeText_(info_text)
            
            urlObj = NSURL.alloc().initWithString_('https://raw.githubusercontent.com/Ryandev/Ripsnort/master/assets/logo200px.png')
            imageObj = NSImage.alloc().initWithContentsOfURL_(urlObj)
            
            notification.set_identityImage_(imageObj)
            notification.setSoundName_("NSUserNotificationDefaultSoundName")
            delay = 0
            notification.setDeliveryDate_(Foundation.NSDate.dateWithTimeInterval_sinceDate_(delay, Foundation.NSDate.date()))
            NSUserNotificationCenter.defaultUserNotificationCenter().scheduleNotification_(notification)
            logging.info("Notification sent: " + title)
        elif platformName == 'linux':
            import subprocess
            subprocess.check_output(['notify-send','-u','normal',title,subtitle])

        
def test():
     m = LocalNotify({})
     m.startedBackingUpDisc('MOVIENAME')
     m.finishedBackingUpDisc('MOVIENAME')
     m.startedRippingTracks([],'MOVIENAME')
     m.finishedRippingTracks([],'MOVIENAME')


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test()

