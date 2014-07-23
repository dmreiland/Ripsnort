#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import subprocess
import logging


OS_MAC='mac'
OS_WIN='win'
OS_LINUX='linux'


class DiscDrive:
    def __init__(self,deviceID):
        self.deviceID = deviceID
        
        import platform
        platformName = platform.system().lower().strip()

        if platformName == 'darwin':
            self.osType = OS_MAC
        elif platformName == 'windows':
            self.osType = OS_WIN
            logging.error( 'No windows support yet' )
            sys.exit(1)
        elif platformName == 'linux':
            self.osType = OS_LINUX
            logging.error( 'No linux support yet' )
            sys.exit(1)
            
        #mac only supported at the moment
        assert self.osType == OS_MAC

    def isOpen(self):
        isOpen = False
        if self.osType == OS_MAC:
            try:
                statusStdout = subprocess.check_output(['drutil','-drive',str(self._macDriveNumber()),'status'])
            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to check if tray open ' + self.deviceID + ', reason: **' + str(e.output) + '**' )
                sys.exit(1)
                
            if 'No Media Inserted' in statusStdout:
                isOpen = True

        return isOpen

    def isClosed(self):
        isClosed = False
        if self.osType == OS_MAC:
            try:
                statusStdout = subprocess.check_output(['drutil','-drive',str(self._macDriveNumber()),'status'])
            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to read closed status ' + self.deviceID + ', reason: **' + str(e.output) + '**' )
                sys.exit(1)
                
            if 'No Media Inserted' not in statusStdout:
                isClosed = True

        return isClosed
    
    def closeTray(self):
        if self.osType == OS_MAC:
            try:
                subprocess.check_output(['drutil','-drive',str(self._macDriveNumber()),'tray','close'])
            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to close tray ' + self.deviceID + ', reason: **' + str(e.output) + '**' )
                sys.exit(1)

    #eject
    def openTray(self):
        if self.osType == OS_MAC:
            try:
                subprocess.check_output(['drutil','-drive',str(self._macDriveNumber()),'tray','eject'])
            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to eject disc ' + self.deviceID + ', reason: **' + str(e.output) + '**' )
                sys.exit(1)

    def isDiscInserted(self):
        isInserted = False

        if self.osType == OS_MAC:
            try:
                dfStdout = subprocess.check_output(['df','-h'])
            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to check disc status ' + self.deviceID + ', reason: **' + str(e.output) + '**' )
                sys.exit(1)
                
            for line in dfStdout.split('\n'):
                if line.startswith(self.deviceID):
                    isInserted = True
                    break
        
        return isInserted
    
    def mountedPath(self):
        mountedPath = None
    
        if self.isDiscInserted():
            if self.osType == OS_MAC:
                try:
                    mountStdout = subprocess.check_output(['mount'])
                except subprocess.CalledProcessError as e:
                    logging.error( 'Failed to eject disc ' + self.deviceID + ', reason: **' + str(e.output) + '**' )
                    sys.exit(1)

                for line in mountStdout.split('\n'):
                    if line.startswith(self.deviceID):
                        mountedPath = line.split('on')[1].split('(')[0].strip()
                        break

        return mountedPath
        
    def mountedDiscName(self):
        discNath = None
    
        if self.isDiscInserted(self):
            mountPath = self.mountedPath()
            discName = os.path.basename(mountPath)

        return mountedPath
        
    def _macDriveNumber(self):
        return 1

