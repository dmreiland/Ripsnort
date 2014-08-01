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

sys.path.append(os.path.join(dirname, "../.."))
sys.path.append(os.path.join(dirname, "../../dependancies"))

from disc_track import disc_track
from config_to_dict import *


class MakeMKV:
    newlinechar = '\n'
    colpattern = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')
    binpath=None
    server_settings = config_to_dict().do(os.path.join(dirname,'makemkv.ini'))
    attributeids = server_settings['attibute_ids']

    def __init__(self,deviceID):
        #TODO replace is a workaround til I figure out naming scheme for devices
        deviceID = deviceID.replace('/dev/disk','/dev/rdisk')
    
        if MakeMKV.binpath == None:
            MakeMKV.binpath = MakeMKV._makeMkvPath()
    
        self.deviceID = deviceID
        self.discInfoRaw = MakeMKV._discInfoRawFromDevice(deviceID)
        
        self.mediaDiscTracks = MakeMKV._discTracksFromDictionary( MakeMKV._deserializeDiscInfo(self.discInfoRaw) )
        
        driveInfo = MakeMKV._driveInfoRawFromDevice(deviceID)

        self.driveNumber = MakeMKV._driveNumber(driveInfo,deviceID)
        
    def __repr__(self):
        return "<MakeMKV>"
    
    def discTracks(self):
        return self.mediaDiscTracks

    def ripDiscTracks(self,tracks,pathSave):
        if not os.path.isdir(pathSave):
            os.makedirs(pathSave)
            
        for track in tracks:
            try:
                save = subprocess.check_output([MakeMKV.binpath,'-r','--noscan','mkv','disc:' + str(self.driveNumber),str(track.trackNumber),pathSave])
                
                nfoFile = track.outputFileName.replace('.mkv','.nfo')
                
                with open(os.path.join(pathSave,nfoFile), 'w') as outfile:
                    json.dump(track.serialize(), outfile)

            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to save track ' + str(track) + ', reason: **' + str(e.output) + '**' )


    def ripDiscBackup(self,pathSave):
        if not os.path.isdir(pathSave):
            os.makedirs(pathSave)
            
        try:
            save = subprocess.check_output([MakeMKV.binpath,'-r','--noscan','--decrypt','disc:' + str(self.driveNumber),pathSave])
        except subprocess.CalledProcessError as e:
            logging.error( 'Failed to save track ' + str(track) + ', reason: **' + str(e.output) + '**' )
            sys.exit(1)
            
    def __repr__(self):
        return "<MakeMKV device:" + self.deviceID +">"

    @staticmethod
    def _makeMkvPath():
        filepath = None

        import platform
        platformName = platform.system().lower().strip()

        if platformName == 'darwin':
            filepath = '/Applications/MakeMKV.app/Contents/MacOS/makemkvcon'

        elif platformName == 'windows':
            logging.error( 'No windows support yet' )
            sys.exit(1)

        elif platformName == 'linux':
            try:
                filepath = subprocess.check_output(['which','makemkvcon']).strip()
            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to call makemkv: ' + str(e.output) )
                sys.exit(1)

            
        return filepath

    @staticmethod
    def _discInfoRawFromDevice(deviceName):
        try:
            disc_info = subprocess.check_output([MakeMKV.binpath,'--noscan','-r','info','dev:%s' % deviceName])
        except subprocess.CalledProcessError as e:
            logging.error( 'Failed to call makemkv: ' + str(e.output) )
            sys.exit(1)
        
        return disc_info
        
    @staticmethod
    def _driveInfoRawFromDevice(deviceName):
        try:
            discs = subprocess.check_output([MakeMKV.binpath,'-r','info','disc:%d' % 9999])
        except subprocess.CalledProcessError as e:
            logging.error( 'Failed to call makemkv: ' + str(e.output) )
            sys.exit(1)
            
        return discs
        
    @staticmethod
    def _driveNumber(deviceInfo,deviceName):
        for line in deviceInfo.split(MakeMKV.newlinechar):
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

        for line in discInfoRaw.split(MakeMKV.newlinechar):
            split_line = MakeMKV.colpattern.split(line)[1::2]
            if len(split_line) > 1 and split_line[0] != 'TCOUNT':
                
                #<  Disc Info
                if line.startswith('CINFO'):
                    try:
                        info_out['disc'][MakeMKV.attributeids[split_line[0].split(':')[-1]]] = split_line[-1].replace('"','')
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
                        track_info[MakeMKV.attributeids[split_line[1]]] = split_line[-1].replace('"','')
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
                        track_info[MakeMKV.attributeids[split_line[1]]] = split_line[-1].replace('"','')
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
            
            chapters = int(track['Chapter Count'])
            bytes = int(track['Disk Size Bytes'])
            titleId = int(track['Original Title ID'])
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
            
            track = disc_track()
            
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


