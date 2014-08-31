#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import re
import sys
import json
import logging
import subprocess

import apppath


dirname = os.path.dirname(os.path.realpath( __file__ ))

sys.path.append( os.path.join(dirname,"subtitle") )
import caption


class VideoTrack(object):

    def __init__(self):
        self.bytes=0
        self.megabytes=0.0
        self.gigabytes=0.0
        self.chapters=0.0
        self.durationS=0.0
        self.subtitles=[]

    def serialize(self):
        retDict = {}
        
        retDict['discname'] = self.disc_name
        retDict['bytes'] = self.bytes
        retDict['chapters'] = self.chapters
        retDict['duration'] = self.durationS
        retDict['segmentsmap'] = self.segmentsMap
        retDict['titleid'] = self.titleID
        
        return json.dumps(retDict)

    def __hash__(self):
        return hash((self.bytes, self.durationS, str(self.subtitles)))

    def __repr__(self):
        retStr = '<track '
        retStr += 'Megabytes: ' + str(self.megabytes) + ', '
        retStr += 'DurationS: ' + str(self.durationS) + ', '
        retStr += 'Subtitles: ' + str(self.subtitles) + '>'        
        return retStr


class LocalTrackMkv(VideoTrack):

    def __init__(self,filepath):
        if os.path.exists(filepath) == False:
            raise Exception('Cannot create LocalTrackMkv object when file does not exist: ' + str(filepath))

        super(LocalTrackMkv, self).__init__()

        self.filepath=filepath
        self.bytes=float(os.path.getsize(filepath))
        self.megabytes=self.bytes/1024.0
        self.gigabytes=self.bytes/1024.0/1024.0
        self.chapters=0.0 #TODO
        
        mkvInfo = self._loadMkvInfo()
        
        if mkvInfo is not None:
            self.durationS= int( re.findall(r'\+\ Duration\:\ (\d+)',mkvInfo)[0] )
        
        self._loadSubtitles()
        
    def _loadMkvInfo(self):
        cmdargs = [apppath.mkvinfo(),self.filepath]
        logging.debug('Running command ' + ' '.join(cmdargs))
        cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd.wait()
        response = cmd.communicate()
        info = response[0].strip()
        
        if '(MKVInfo) Error: Couldn\'t open input file' in info:
            logging.error('Failed to load mkvInfo: ' + info)
            info = None
        else:
            logging.debug('Loaded track info: ' + str(info))

        return info
        
    def vobsubDataForTrackNumber(self,trackNumber):
        tmpDir = apppath.pathTemporary('disk_track')
        vobsubFile = os.path.join(tmpDir,'tmpFile.sub')
        
        if os.path.exists(vobsubFile):
            os.remove(vobsubFile)
        
        idxFile = os.path.join(tmpDir,'tmpFile.idx')
        
        if os.path.exists(idxFile):
            os.remove(idxFile)
        
        cmdargs = [apppath.mkvextract(),'tracks',self.filepath,str(trackNumber)+':'+vobsubFile]
        logging.debug('Running command ' + ' '.join(cmdargs))
        cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         cmd.wait()
        response = cmd.communicate()
        
        vobsubdata = None
        idxdata = None
        
        if os.path.exists(vobsubFile) and os.path.exists(idxFile):
            logging.debug('Found vob sub file ' + vobsubFile)
            fSub = open(vobsubFile,'r')
            vobsubdata = fSub.read()
            fSub.close()

            fIdx = open(idxFile,'r')
            idxdata = fIdx.read()
            fIdx.close()
        else:
            logging.error('Failed to file vobsub file')

        return [vobsubdata,idxdata]

        
    def _loadSubtitles(self,languages=['eng']):
        logging.debug('Loading subtitles for ' + self.filepath)
        mkvInfo = self._loadMkvInfo()
        
        segmentTracks = mkvInfo[mkvInfo.find('| + A track'):len(mkvInfo)]
        
        for segment in segmentTracks.split('| + A track'):
            if '|  + Track type: subtitles' in segment:
                lang = re.findall(r'Language\:\ ...?',segment)[0].replace('Language: ','').strip()
                codec = re.findall(r'Codec ID\:\ \w+?\n',segment)[0].replace('Codec ID: ','').strip()
                tracknum = int( re.findall(r'Track\ number\:\ \d+',segment)[0].replace('Track number: ','').strip() )
                
                logging.debug('Found subtitle codec: ' + codec + ' language: ' + lang + ' track: ' + str(tracknum))
                
                if lang not in languages:
                    continue

                if codec.lower() == 's_vobsub':
                    logging.debug('Loading vobsub data for tracknum ' + str(tracknum) + ' language ' + str(lang))
                
                    '''sub subtract 1 from tracknumber when called mkextract'''
                    vobsubdata, idxdata = self.vobsubDataForTrackNumber(tracknum-1)
                    
                    subtitle = caption.VobSubCaption(vobsubdata,idxdata,lang)
                    subtitle.data_source = 'makemkv'


                    self.subtitles.append(subtitle)

                elif codec.lower() == 's_text/utf8':
                    logging.debug('Loading srt data for tracknum ' + str(tracknum) + ' language ' + str(lang))
                
                    '''sub subtract 1 from tracknumber when called mkextract'''
#                     vobsubdata, idxdata = self.vobsubDataForTrackNumber(tracknum-1)
#                     
#                     subtitle = caption.VobSubCaption(vobsubdata,idxdata,lang)
#                     
#                     self.subtitles.append(subtitle)
#                    subtitle.data_source = 'makemkv'

                else:
                    logging.warn('Unrecognised subtitles codec: ' + codec)



class DiscTrack(VideoTrack):

    def __init__(self,dictLoad=None):

        super(DiscTrack, self).__init__()

        self.disc_name=''
        self.segmentsMap=[]
        self.titleID=0
        self.trackNumber=0
        self.outputFileName=''
        
        if ( dictLoad is not None ) and ( type(dictLoad) == type({}) ):
            self.disc_name = dictLoad['discname']
            self.bytes = float(dictLoad['bytes'])
            self.megabytes = self.bytes / 1024.0 / 1024.0
            self.gigabytes = self.bytes / 1024.0 / 1024.0 / 1024.0
            self.chapters = dictLoad['chapters']
            self.durationS = dictLoad['duration']
            self.segmentsMap = dictLoad['segmentsmap']
            self.titleID = dictLoad['titleid']
            self.trackNumber = dictLoad['tracknumber']
            self.outputFileName = dictLoad['filename']

    def __repr__(self):
        retStr = '<track '
        retStr += 'DiscName: ' + self.disc_name + ', '
        retStr += 'DeviceName: ' + self.disc_device + ', '
        retStr += 'Gigabytes: ' + str(self.gigabytes) + ', '
        retStr += 'Chapters: ' + str(self.chapters) + ', '
        retStr += 'Duration: ' + str(self.durationS) + ', '
        retStr += 'SegmentsMap: ' + str(self.segmentsMap) + ', '
        retStr += 'TitleID: ' + str(self.titleID) + ', '
        retStr += 'TrackNumber: ' + str(self.trackNumber) + ', '
        retStr += 'Filename: ' + self.outputFileName + '>'
        
        return retStr


def tracksOverDuration(durationMin,discTracks):
    tracksRet = []
    
    for track in discTracks:
        if track.durationS >= durationMin:
            tracksRet.append(track)
    
    return tracksRet


def tracksUnderDuration(durationMax,discTracks):
    tracksRet = []
    
    for track in discTracks:
        if track.durationS <= durationMax:
            tracksRet.append(track)
    
    return tracksRet


def tracksBetweenDurationMinMax(tracks,durationMin,durationMax):
    return tracksUnderDuration(durationMax, tracksOverDuration(durationMin,tracks))


def test():
    dictLoad = {}

    dictLoad['discname'] = 'disc'
    dictLoad['bytes'] = 999
    dictLoad['chapters'] = 10
    dictLoad['duration'] = 300
    dictLoad['segmentsmap'] = [[0,1],[2,3]]
    dictLoad['titleid'] = 1
    dictLoad['filename'] = 'file1'
    dictLoad['tracknumber'] = 'file1'

    track = DiscTrack(dictLoad)

    assert track.disc_name == 'disc'
    assert track.bytes == 999
    assert track.chapters == 10
    assert track.durationS == 300
    assert track.segmentsMap == [[0,1],[2,3]]
    assert track.titleID == 1
    assert track.outputFileName == 'file1'


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test()

