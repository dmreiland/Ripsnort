#!/usr/bin/env python
# -*- coding: utf-8 -*-


import subprocess
import re
import json
import shutil
import logging
import sys
import os
import md5


dirname = os.path.dirname(__file__)

sys.path.append(os.path.join(dirname,"..",".."))
from disc_track import *
import apppath

sys.path.append(os.path.join(dirname,"..","..","utils"))
import inireader


class MakeMKVDisc:
    newlinechar = '\n'
    colpattern = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')
    
    server_settings = inireader.loadFile(os.path.join(os.path.dirname(__file__),'makemkv.ini'),convertNativeTypes=False)
    attributeids = server_settings['attribute_ids']

    def __init__(self,deviceID):
        if MakeMKVDisc._hasMakeMkvKeyExpired():
            raise Exception('MakeMKV license key has expired. Manually run makemkv to update the key. (AppPath:' + apppath.makemkvcon() +')')
    
        #TODO replace is a workaround til I figure out naming scheme for devices
        deviceID = deviceID.replace('/dev/disk','/dev/rdisk')
    
        self.deviceID = deviceID
        self.discInfoRaw = MakeMKVDisc._discInfoRawFromDevice(deviceID)
        
        self.mediaDiscTracks = MakeMKVDisc._discTracksFromDictionary( MakeMKVDisc._deserializeDiscInfo(self.discInfoRaw) )
        
        driveInfo = MakeMKVDisc._driveInfoRawFromDevice(deviceID)

        self.driveNumber = MakeMKVDisc._driveNumber(driveInfo,deviceID)
        
        logging.debug('MakeMKVDisc initialized with deviceID' + str(deviceID))
        
    def __repr__(self):
        return "<MakeMKVDisc " +self.deviceID+ " >"
        
    def hasLocatedMediaTracks(self):
        return True

    def tracks(self):
        return self.mediaDiscTracks

    def ripTracks(self,tracks,pathSave):
        didRip = True
        
        if not os.path.isdir(pathSave):
            os.makedirs(pathSave)
            
        for track in tracks:
            try:
                outputFile = os.path.join(pathSave,track.outputFileName)

                if os.path.exists(outputFile):
                    os.remove(outputFile)
                    
                ripType = 'disc'

                logging.info('Started ripping track: ' + str(track))
                cmdargs = [apppath.makemkvcon(),'-r','--noscan','mkv',ripType + ':' + str(self.driveNumber),str(track.trackNumber),pathSave]
                logging.debug('Running command: ' + ' '.join(cmdargs))
                exitCode = subprocess.call(cmdargs)
                
                if exitCode is not 0:
                    didRip = False

            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to save track ' + str(track) + ', reason: **' + str(e.output) + '**' )
                didRip = False
        
        rippedTracks = []
        
        if didRip:
            for fileName in os.listdir(pathSave):
                if fileName.lower().endswith('.mkv'):
                    filePath = os.path.join(pathSave,fileName)
                    track = LocalTrackMkv(filePath)
                    rippedTracks.append(track)

        return rippedTracks

    def ripAllTracks(self,pathSave):
        didRip = True
        
        if not os.path.isdir(pathSave):
            os.makedirs(pathSave)
            
        try:
            
            ripType = 'dev'

            logging.info('Started ripping all tracks to: ' + str(pathSave))
            cmdargs = [apppath.makemkvcon(),'-r','--noscan','mkv',ripType + ':' + str(self.filePath),'all',pathSave]
            logging.debug('Running command: ' + ' '.join(cmdargs))
            exitCode = subprocess.call(cmdargs)
                
            if exitCode is not 0:
                didRip = False

        except subprocess.CalledProcessError as e:
            logging.error( 'Failed to save track ' + str(track) + ', reason: **' + str(e.output) + '**' )
            didRip = False
        
        rippedTracks = []
        
        if didRip:
            for fileName in os.listdir(pathSave):
                if fileName.lower().endswith('.mkv'):
                    filePath = os.path.join(pathSave,fileName)
                    track = DiscTrack.LocalTrackMkv(filePath)
                    rippedTracks.append(track)
        
        return rippedTracks

    def __repr__(self):
        return "<MakeMKV device:" + self.deviceID +">"
        
    @staticmethod
    def _hasMakeMkvKeyExpired():
        hasExpired = False
    
        try:
            cmdargs = [apppath.makemkvcon(),'--noscan','-r','info']
            logging.debug('Running command: ' + ' '.join(cmdargs))
            cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd.wait()
            response = cmd.communicate()
            
            if 'enter a registration key to continue' in response[0].lower():
                hasExpired = True

        except subprocess.CalledProcessError as e:
            logging.error( 'Failed to call makemkv: ' + str(e.output) )
            sys.exit(1)
        
        return hasExpired

    @staticmethod
    def _discInfoRawFromDevice(deviceName):
        try:
            cmdargs = [apppath.makemkvcon(),'--noscan','-r','info','dev:%s' % deviceName]
            logging.debug('Running command: ' + ' '.join(cmdargs))
            cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd.wait()
            response = cmd.communicate()
            disc_info = response[0]
        except subprocess.CalledProcessError as e:
            logging.error( 'Failed to call makemkv: ' + str(e.output) )
            sys.exit(1)
            
        logging.debug('Got disc info: ' + str(disc_info))
        
        return disc_info
        
    @staticmethod
    def _driveInfoRawFromDevice(deviceName):
        try:
            cmdargs = [apppath.makemkvcon(),'-r','info','disc:%d' % 9999]
            logging.debug('Running command: ' + ' '.join(cmdargs))
            cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd.wait()
            response = cmd.communicate()
            discs = response[0]
        except subprocess.CalledProcessError as e:
            logging.error( 'Failed to call makemkv: ' + str(e.output) )
            sys.exit(1)
            
        return discs
        
    @staticmethod
    def _driveNumber(deviceInfo,deviceName):
        for line in deviceInfo.split(MakeMKVDisc.newlinechar):
            line = line.strip().replace('"','')
            if line.startswith('DRV:') and line.endswith(deviceName):
                return int( line.split(',')[0].split(':')[1] )

        return -1

    @staticmethod
    def _deserializeDiscInfo(discInfoRaw):
        #Code used from Remote-MakeMKV project: https://code.google.com/p/remote-makemkv/
        info_out = {
            'disc'  :   {},
            'tracks':   {}
        }

        track_id = -1

        for line in discInfoRaw.split(MakeMKVDisc.newlinechar):
            split_line = MakeMKVDisc.colpattern.split(line)[1::2]
            if len(split_line) > 1 and split_line[0] != 'TCOUNT':
                
                #<  Disc Info
                if line.startswith('CINFO'):
                    try:
                        info_out['disc'][MakeMKVDisc.attributeids[split_line[0].split(':')[-1]]] = split_line[-1].replace('"','')
                    except KeyError:
                        info_out['disc'][split_line[0].split(':')[-1]] = split_line[-1].replace('"','')

                elif line.startswith('TINFO'):
                    track_id = split_line[0].split(':')[-1]
                    #<  If new track_id, dim var
                    try:    
                        track_info = info_out['tracks'][track_id]
                    except KeyError:
                        track_info = info_out['tracks'][track_id] = {'cnts':{'Subtitles':0,'Video':0,'Audio':0}}

                    try:
                        track_info[MakeMKVDisc.attributeids[split_line[1]]] = split_line[-1].replace('"','')
                    except KeyError:
                        track_info[split_line[1]] = split_line[-1].replace('"','')

                elif line.startswith('SINFO'):
                    track_part_id = split_line[1]
                    #<  If new track_id, dim var
                    try:    
                        info_out['tracks'][track_id]['track_parts']
                    except KeyError:
                        info_out['tracks'][track_id]['track_parts'] = {}

                    #<  If new track_id, dim var                        
                    try:    
                        track_info = info_out['tracks'][track_id]['track_parts'][track_part_id]
                    except KeyError:
                        track_info = info_out['tracks'][track_id]['track_parts'][track_part_id] = {}

                    try:
                        track_info[MakeMKVDisc.attributeids[split_line[1]]] = split_line[-1].replace('"','')
                    except KeyError:
                        track_info[split_line[1]] = split_line[-1].replace('"','')

        #   Count the track parts
        for track_id,track_info in info_out['tracks'].iteritems():
            for part_id, track_part in track_info['track_parts'].iteritems():
                try:
                    info_out['tracks'][track_id]['cnts'][track_part['Type']] += 1
                #<  Type not avail, should be good to ignore?                    
                except KeyError:    
                    pass
            
        return info_out

    @staticmethod
    def _discTracksFromDictionary(dictionaryInfo):
        
        tracks = []
        
        volumeName = dictionaryInfo['disc']['Volume Name']
        
        for key in dictionaryInfo['tracks'].keys():
            track = dictionaryInfo['tracks'][key]
            
            try:
                chapters = int(track['Chapter Count'])
            except:
                chapters = -1

            bytes = int(track['Disk Size Bytes'])
            
            try:
                titleId = int(track['Original Title ID'])
            except:
                titleId = -1

            filename = track['Output Filename']
            durationStr = track['Duration']
            durationHours = int(durationStr.split(':')[0])
            durationMinutes = int(durationStr.split(':')[1])
            durationSeconds = int(durationStr.split(':')[2])

            segmentsList = []
            
            #TODO can have odd looking segments map i.e. '1-7,(9,11)' remove '(' and ')'
            track['Segments Map'] = track['Segments Map'].replace('(','').replace(')','')
            
            #more than one segment map
            if ',' in track['Segments Map']:
                segmentsMapStrList = track['Segments Map'].split(',')
            
                for mapStr in segmentsMapStrList:
                    if '-' in mapStr:
                        segmentsList.append( [ int(mapStr.split('-')[0]) , int(mapStr.split('-')[1]) ] )
                    #single map segment
                    else:
                        segmentsList.append( int(mapStr) )
            else:
                mapStr = track['Segments Map']
                if '-' in mapStr:
                    segmentsList.append( [ int(mapStr.split('-')[0]) , int(mapStr.split('-')[1]) ] )
                else:
                    segmentsList.append( int(mapStr) )
            
            track = DiscTrack()
            
            track.disc_name = volumeName
            track.disc_device=''
            track.bytes = bytes
            track.megabytes = float(bytes / 1024 / 1024)
            track.gigabytes = float(bytes / 1024 / 1024 / 1024)
            track.chapters = chapters
            track.durationS = durationSeconds + (durationMinutes*60) + (durationHours*60*60)
            track.segmentsMap = segmentsList
            track.titleID = titleId
            #converts title02.mkv to 02
            track.trackNumber = int( re.sub('\D','',filename) )
            track.outputFileName = filename
            
            tracks.append(track)
        
        return tracks


