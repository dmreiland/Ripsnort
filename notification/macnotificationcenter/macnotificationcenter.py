#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging


class MacNotify:
    def __init__(self,params):
        logging.debug('MacNotify initialized with config: ' + str(params))

    def startedBackingUpDisc(self,discName):
        title = "Started backing up: " + discName        
        self._notify(title,'','',0,True)

    def finishedBackingUpDisc(self,discName):
        title = "Finished backing up: " + discName        
        self._notify(title,'','',0,True)

    def startedRippingTracks(self,tracks,discName):
        title = "Started ripping: " + discName
        
        totalDurationMins = 0

        for track in tracks:
            totalDurationMins += int(track.durationS/60)
        
        subtitle = str(len(tracks)) + " tracks, total duration " + str(totalDurationMins) + " minutes"
        
        self._notify(title,subtitle,'',0,True)

    def finishedRippingTracks(self,tracks,discName,mediaObjects=[]):
        title = "Finished ripping: " + discName
        
        totalDurationMins = 0

        for track in tracks:
            totalDurationMins += int(track.durationS/60)
        
        subtitle = str(len(tracks)) + " tracks, total duration " + str(totalDurationMins) + " minutes"
        message = "Tracks: \n"

        for track in tracks:
            message += "  " + track.outputFileName + ", " + str(track.chapters) + ", " + str(track.durationS/60) + "minutes\n"
        
        self._notify(title,subtitle,message,0,True)

    def _notify(self, title, subtitle, info_text, delay=0, sound=False):
        import platform

        platformName = platform.system().lower().strip()

        #Can only run on Macs
        if platformName == 'darwin':
            import Foundation
            import objc
            import AppKit

            NSUserNotification = objc.lookUpClass('NSUserNotification')
            NSUserNotificationCenter = objc.lookUpClass('NSUserNotificationCenter')
            NSImage = objc.lookUpClass('NSImage')
            NSURL = objc.lookUpClass('NSURL')

            notification = NSUserNotification.alloc().init()
            notification.setTitle_(title)
            notification.setSubtitle_(subtitle)
            notification.setInformativeText_(info_text)
            
            urlObj = NSURL.alloc().initWithString_('https://raw.githubusercontent.com/Ryandev/Ripsnort/master/assets/logo200px.png')
            imageObj = NSImage.alloc().initWithContentsOfURL_(urlObj)
            
            notification.set_identityImage_(imageObj)

            if sound:
                notification.setSoundName_("NSUserNotificationDefaultSoundName")

            notification.setDeliveryDate_(Foundation.NSDate.dateWithTimeInterval_sinceDate_(delay, Foundation.NSDate.date()))
            NSUserNotificationCenter.defaultUserNotificationCenter().scheduleNotification_(notification)
            logging.info("Notification sent: " + title)

        
if __name__ == "__main__":     
     m = MacNotify({})
     m.startedBackingUpDisc('MOVIENAME')
     m.finishedBackingUpDisc('MOVIENAME')
     m.startedRippingTracks([],'MOVIENAME')
     m.finishedRippingTracks([],'MOVIENAME')
