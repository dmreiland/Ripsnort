#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import subprocess
import logging
import platform


OS_MAC='mac'
OS_WIN='win'
OS_LINUX='linux'


class DiscDrive:
    def __init__(self,deviceID):
        if DiscDrive.doesDeviceExist(deviceID) == False:
            raise Exception('Invalid disc device: ' + deviceID)
    
        self.deviceID = deviceID
        
        platformName = platform.system().lower().strip()

        if platformName == 'darwin':
            self.osType = OS_MAC

        elif platformName == 'windows':
            self.osType = OS_WIN
            logging.error( 'No windows support yet' )
            sys.exit(1)

        elif platformName == 'linux':
            self.osType = OS_LINUX
        
        logging.info('Initialised DiscDrive for device: ' + self.deviceID + ' on platform: ' + self.osType)

    def isOpen(self):
        return not self.isClosed()

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

        elif self.osType == OS_WIN:
            logging.error('No windows support yet')
            sys.exit(1)

        elif self.osType == OS_LINUX:
            #TODO Don't know how to check, instead check for media
            isClosed = self.isDiscInserted()

        else:
            logging.error('Undefined OS: ' + self.osType)
            sys.exit(1)            

        return isClosed
    
    def closeTray(self):
        if self.isClosed() == True:
            return
    
        if self.osType == OS_MAC:
            try:
                subprocess.check_output(['drutil','-drive',str(self._macDriveNumber()),'tray','close'])
            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to close tray ' + self.deviceID + ', reason: **' + str(e.output) + '**' )
                sys.exit(1)

        elif self.osType == OS_WIN:
            logging.error('No windows support yet')
            sys.exit(1)

        elif self.osType == OS_LINUX:
            try:
                subprocess.check_output(['eject','-T',self.deviceID])
            except subprocess.CalledProcessError as e:
                print( 'Failed to eject disc ' + self.deviceID + ', reason: **' + str(e.output) + '**' )
                sys.exit(1)

        else:
            logging.error('Undefined OS: ' + self.osType)
            sys.exit(1)

    #eject
    def openTray(self):
        if self.isOpen():
            return
    
        if self.osType == OS_MAC:
            try:
                subprocess.check_output(['drutil','-drive',str(self._macDriveNumber()),'tray','eject'])
            except subprocess.CalledProcessError as e:
                print( 'Failed to eject disc ' + self.deviceID + ', reason: **' + str(e.output) + '**' )
                sys.exit(1)

        elif self.osType == OS_WIN:
            logging.error('No windows support yet')
            sys.exit(1)

        elif self.osType == OS_LINUX:
            try:
                subprocess.check_output(['eject',self.deviceID])
            except subprocess.CalledProcessError as e:
                print( 'Failed to eject disc ' + self.deviceID + ', reason: **' + str(e.output) + '**' )
                sys.exit(1)

        else:
            logging.error('Undefined OS: ' + self.osType)
            sys.exit(1)

    def isDiscInserted(self):
        isInserted = False

        if self.osType == OS_MAC or self.osType == OS_LINUX:
            try:
                dfStdout = subprocess.check_output(['df','-h'])
            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to check disc status ' + self.deviceID + ', reason: **' + str(e.output) + '**' )
                sys.exit(1)
                
            for line in dfStdout.split('\n'):
                if line.startswith(self.deviceID):
                    isInserted = True
                    break

        elif self.osType == OS_WIN:
            logging.error('No windows support yet')
            sys.exit(1)

        else:
            logging.error('Undefined OS: ' + self.osType)
            sys.exit(1)        
        return isInserted
    
    def mountedPath(self):
        mountedPath = None
    
        if self.isDiscInserted():
            if self.osType == OS_MAC or self.osType == OS_LINUX:
                try:
                    mountStdout = subprocess.check_output(['mount'])
                except subprocess.CalledProcessError as e:
                    logging.error( 'Failed to eject disc ' + self.deviceID + ', reason: **' + str(e.output) + '**' )
                    sys.exit(1)

                for line in mountStdout.split('\n'):
                    if line.startswith(self.deviceID):
                        mountedPath = line.split('on')[1].split('(')[0].strip()
                        break

        elif self.osType == OS_WIN:
            logging.error('No windows support yet')
            sys.exit(1)

        else:
            logging.error('Undefined OS: ' + self.osType)
            sys.exit(1)

        return mountedPath
        
    def mountedDiscName(self):
        discName = None
    
        if self.isDiscInserted():
            mountPath = self.mountedPath()
            discName = os.path.basename(mountPath)

        return discName

    def _macDriveNumber(self):
        driveNumber = None
        
        #Loop through calling status on drives 1-9 until the output shows deviceID
        for driveCheck in range(1,9):
            driveOutput = subprocess.check_output(['drutil','status','-drive',str(driveCheck)])

            if self.deviceID in driveOutput:
                driveNumber = driveCheck
                break
        
        return driveNumber
        
    @staticmethod
    def doesDeviceExist(deviceName):
        doesExist = False
    
        platformName = platform.system().lower().strip()

        if platformName == 'darwin' or platformName == 'linux':
            doesExist = os.path.exists(deviceName)

        elif platformName == 'windows':
            logging.error( 'No windows support yet' )
            sys.exit(1)

        else:
            logging.error('Undefined OS: ' + self.osType)
            sys.exit(1)
            
        return doesExist

