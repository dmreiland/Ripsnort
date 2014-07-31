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
        #replace is a workaround til I figure out naming scheme for devices
        deviceID = deviceID.replace('/dev/disk','/dev/rdisk')
    
        MakeMKV.binpath = MakeMKV._makeMkvPath()
    
        self.deviceID = deviceID
        self.discInfoRaw = MakeMKV._discInfoRawFromDevice(deviceID)
        
        self.mediaDiscTracks = MakeMKV._discTracksFromDictionary( MakeMKV._deserializeDiscInfo(self.discInfoRaw) )
        
        driveInfo = MakeMKV._driveInfoRawFromDevice(deviceID)

        self.formattedDiscName = MakeMKV._cleanDiscName( MakeMKV._readTitleFromDriveInfo(driveInfo,deviceID) )
        self.driveNumber = MakeMKV._driveNumber(driveInfo,deviceID)
        
    def __repr__(self):
        return "<MakeMKV>"
        
    def formattedName(self):
        return self.formattedDiscName
    
    def discTracks(self):
        return self.mediaDiscTracks

    def ripDiscTracks(self,tracks,pathSave):
        if not os.path.isdir(pathSave):
            os.makedirs(pathSave)
            
        for track in tracks:
            try:
                save = subprocess.check_output([MakeMKV.binpath,'-r','--noscan','mkv','disc:' + str(self.driveNumber),str(track.trackNumber),pathSave])
                
                nfoFile = track.outputFileName.replace('.mkv','.nfo')
                
                with open(pathSave + '/' + nfoFile, 'w') as outfile:
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
            logging.error( 'No linux support yet' )
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
    def _readTitleFromDriveInfo(driveInfo,deviceName):
        
        for line in driveInfo.split(MakeMKV.newlinechar):
            line = line.strip().replace('"','')
            if line.startswith('DRV:') and line.endswith(deviceName):
                return line.split(',')[-2]
                
        import time
        import calendar
        epoch = calendar.timegm(time.gmtime())

        return "UNTITLED_" + str(epoch)
        
    @staticmethod
    def _driveNumber(deviceInfo,deviceName):
        for line in deviceInfo.split(MakeMKV.newlinechar):
            line = line.strip().replace('"','')
            if line.startswith('DRV:') and line.endswith(deviceName):
                return int( line.split(',')[0].split(':')[1] )

        return -1

    @staticmethod
    def _cleanDiscName(title):
        tmpName = title
    
        #remove 'editions' from title
        tmpName = re.sub('(?i)extended[_| ]?edition','',tmpName,re.IGNORECASE)
        tmpName = re.sub('(?i)special[_| ]?edition','',tmpName,re.IGNORECASE)
        tmpName = re.sub('(?i)limited[_| ]?edition','',tmpName,re.IGNORECASE)

        #remove PAL/NTSC
        tmpName = re.sub('(?i)[_| ]?pal','',tmpName,re.IGNORECASE)
        tmpName = re.sub('(?i)[_| ]?ntsc','',tmpName,re.IGNORECASE)
    
        #check for tv series S7D1 S7_D1
        seriesRegexShort = '(?i)s([\d{1,2}])_?d([\d{1,2}])'
        seriesCheckShortRE = re.compile(seriesRegexShort)
    
        if len(seriesCheckShortRE.findall(tmpName)) > 0:
            seriesSearch = seriesCheckShortRE.search(tmpName)
            tmpName = re.sub(seriesRegexShort,' - Season ' + seriesSearch.groups()[0] + ' Disc ' + seriesSearch.groups()[1],tmpName)

        #Season7_Disc1 Series7_Disc1
        seriesRegexLong = '(?:season|series)_?([\d{1,2}])_?(?:disc|disk|d)_?([\d{1,2}])'
        seriesCheckLongRE = re.compile(seriesRegexLong, re.IGNORECASE)
    
        if len(seriesCheckLongRE.findall(tmpName)) > 0:
            seriesSearch = seriesCheckLongRE.search(tmpName)
            tmpName = re.sub(seriesCheckLongRE,' - Season ' + seriesSearch.groups()[0] + ' Disc ' + seriesSearch.groups()[1],tmpName,re.IGNORECASE)
    
        #check for tv series with uncessary middle characters i.e. S7 F1 D1
        seriesRegexMiddle = '(?i)(?:s|series|season)_?([\d{1,2}]).*(?:d|disc|disk)_?([\d{1,2}])'
        seriesRegexMiddleRE = re.compile(seriesRegexMiddle)
    
        if len(seriesRegexMiddleRE.findall(tmpName)) > 0:
            seriesSearch = seriesRegexMiddleRE.search(tmpName)
            tmpName = re.sub(seriesRegexMiddle,' - Season ' + seriesSearch.groups()[0] + ' Disc ' + seriesSearch.groups()[1],tmpName)
            
        #look for numbers prepended to the end of the last word and add space
        numberWhitespacing = r'\b(\w+)(\d+)\b$'
        numberWhitespacingRE = re.compile(numberWhitespacing)
        
        if len(numberWhitespacingRE.findall(tmpName)) > 0:
            whitespaceSearch = numberWhitespacingRE.search(tmpName)
            tmpName = re.sub(numberWhitespacing,whitespaceSearch.groups()[0] + ' ' + whitespaceSearch.groups()[1],tmpName)
            

        # Clean up
        tmpName = tmpName.replace("\"", "")
        tmpName = tmpName.replace("_", " ")
        tmpName = tmpName.replace("  ", " ")
    
        #capitalize first letter of each word
        tmpName = tmpName.title()
        tmpName = tmpName.strip()
        
        logging.info('Converted disc name: ' +title+ ' to ' + tmpName)

        return tmpName

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



if __name__ == "__main__":
    expectedText1 = 'Bones - Season 7 Disc 1'

    assert expectedText1 == MakeMKV._cleanDiscName('BONES_SEASON_7_DISC_1')
    assert expectedText1 == MakeMKV._cleanDiscName('bones_s7_d1')
    assert expectedText1 == MakeMKV._cleanDiscName('bones_season7_d1')
    assert expectedText1 == MakeMKV._cleanDiscName('bones_season_7_d1')
    assert expectedText1 == MakeMKV._cleanDiscName('bones_season_7_d_1')
    
    expectedText2 = 'Die Hard'
 
    assert expectedText2 == MakeMKV._cleanDiscName('Die Hard Limited Edition')
    assert expectedText2 == MakeMKV._cleanDiscName('Die Hard limited_Edition')
    assert expectedText2 == MakeMKV._cleanDiscName('Die Hard Special Edition')
    assert expectedText2 == MakeMKV._cleanDiscName('Die Hard special_edition')
    assert expectedText2 == MakeMKV._cleanDiscName('Die Hard Extended Edition')
    assert expectedText2 == MakeMKV._cleanDiscName('DIE_HARD_EXTENDED_EDITION')
    expectedText3 = 'Bones - Season 8 Disc 1'

    assert expectedText3 == MakeMKV._cleanDiscName('BONES_SEASON_8_F1_DISC_1')
    assert expectedText3 == MakeMKV._cleanDiscName('BONES_SEASON_8_F1_D_1')
    assert expectedText3 == MakeMKV._cleanDiscName('BONES_SEASON_8_F1_D1')

    expectedText4 = '24 - Season 2 Disc 2'

    assert expectedText4 == MakeMKV._cleanDiscName('24_SEASON2_DISC2')
    assert expectedText4 == MakeMKV._cleanDiscName('24_SEASON2_DISC_2')
    assert expectedText4 == MakeMKV._cleanDiscName('24SEASON2DISC2')
    assert expectedText4 == MakeMKV._cleanDiscName('24_SEASON_2_DISC_2')
    assert expectedText4 == MakeMKV._cleanDiscName('24_SEASON_2_DISK_2')

    expectedText5 = 'Die Hard 2'
 
    assert expectedText5 == MakeMKV._cleanDiscName('Die Hard 2')
    assert expectedText5 == MakeMKV._cleanDiscName('Die Hard  2')
    assert expectedText5 == MakeMKV._cleanDiscName('Die Hard2')

    expectedText6 = 'Little Mermaid 2'
 
    assert expectedText6 == MakeMKV._cleanDiscName('LITTLE_MERMAID2')


