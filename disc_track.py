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
        
    def numberOfSubtitles(self):
        return len(self.subtitles)
    
    def numberOfSubtitlesOfLanguage(self,lang):
        count = 0
        
        for i in range(0,self.numberOfSubtitles()):
            if self.subtitleLanguageAtIndex(i) == lang:
                count += 1
                
        return count

    def allSubtitleLanguages(self):
        langs = []
        
        for i in range(0,self.numberOfSubtitles()):
            langs.append(self.subtitleLanguageAtIndex(i))
            
        langs = list(set(langs))
        langs.sort()
        
        return langs

    def subtitleOfLanguageAtSubindex(self,lang,index):
        subLang = None
        count = 0

        for i in range(0,len(self.subtitles)):
            langAtIndex = self.subtitleLanguageAtIndex(i)
            if langAtIndex == lang:
                if index == count:
                    subLang = self.subtitleAtIndex(i)
                count += 1

        return subLang
    
    def subtitleLanguageAtIndex(self,index):
        lang = None
        try:
            lang = self.subtitleAtIndex(index).language
        except:
            pass
        return lang
    
    def subtitleAtIndex(self,index):
        subLang = None

        if index < len(self.subtitles):
            try:
                subLang = self.subtitles[index]
            except:
                pass

        return subLang

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
        
        self.mkvInfo = self._loadMkvInfo()
        
        if self.mkvInfo:
            self.subtitles = []
            for i in range(0,self.numberOfSubtitles()):
                self.subtitles.append(None)
        
        if self.mkvInfo:
            self.durationS = int( re.findall(r'\+\ Duration\:\ (\d+)',self.mkvInfo)[0] )
        
        logging.debug('LocalTrackMkv intialized for path ' + str(self.filepath))
            
    def numberOfSubtitles(self):
        numberOfSubtitles = len(re.findall(r'Track\ type\:\ subtitles',self.mkvInfo))
        return numberOfSubtitles

    def subtitleAtIndex(self,index):
        sub = None

        if index < len(self.subtitles):
            sub = self.subtitles[index]
            
            if sub == None:
                self._loadSubtitleAtIndex(index)
                sub = self.subtitles[index]
                logging.debug('Loaded sub at index: ' + str(index) + ', ' + str(sub))
                
            assert(sub)

        return sub

    def subtitleLanguageAtIndex(self,index):
        subLang = None

        if index < len(self.subtitles):
            if self.subtitles[index]:
                subLang = self.subtitles[index].language
            else:
                currentSubtitleIndex = 0

                if self.mkvInfo:
                    segmentTracks = self.mkvInfo[self.mkvInfo.find('| + A track'):len(self.mkvInfo)]

                    for segment in segmentTracks.split('| + A track'):
                        if len(re.findall(r'Track\ type\:\ subtitles',segment)) > 0:
                            
                            if index == currentSubtitleIndex:
                                try:
                                    subLang = re.findall(r'Language\:\ ...?',segment)[0].replace('Language: ','').strip()
                                except:
                                    #Language not set, assume english
                                    subLang = 'eng'
                                break

                            currentSubtitleIndex += 1

        return subLang

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
            logging.error('Failed to find vobsub file ' + str(vobsubFile))

        return [vobsubdata,idxdata]
    
    def pgsDataForTrackNumber(self,trackNumber):
        tmpDir = apppath.pathTemporary('disk_track')
        pgsFile = os.path.join(tmpDir,'tmpFile.sup')
        
        if os.path.exists(pgsFile):
            os.remove(pgsFile)
        
        cmdargs = [apppath.mkvextract(),'tracks',self.filepath,str(trackNumber)+':'+pgsFile]
        logging.debug('Running command ' + ' '.join(cmdargs))

        cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        response = cmd.communicate()
        
        pgsdata = None
        
        if os.path.exists(pgsFile):
            logging.debug('Found pgs file ' + pgsFile)
            fPgs = open(pgsFile,'r')
            pgsdata = fPgs.read()
            assert(len(pgsdata)>0)
            fPgs.close()
        else:
            logging.error('Failed to find PGS file ' + str(pgsFile))

        return pgsdata
        
    def _loadSubtitleAtIndex(self,subIndex):
        logging.debug('Loading subtitles for ' + str(self.filepath) + ', at index: ' + str(subIndex))
        
        currentSubtitleIndex = 0

        segmentTracks = self.mkvInfo[self.mkvInfo.find('| + A track'):len(self.mkvInfo)]
        
        for segment in segmentTracks.split('| + A track'):
            if '|  + Track type: subtitles' in segment:
                codec = re.findall(r'Codec ID\:\ .*\n',segment)[0].replace('Codec ID: ','').strip()
                tracknum = int( re.findall(r'track\ ID\ for\ mkvmerge\ \&\ mkvextract\:\ \d+',segment)[0].replace('track ID for mkvmerge & mkvextract: ','').strip() )
                
                if currentSubtitleIndex == subIndex:
                    lang = self.subtitleLanguageAtIndex(currentSubtitleIndex)
                    assert(lang)
                    
                    if codec.lower() == 's_vobsub':
                        logging.debug('Loading vobsub data for tracknum ' + str(tracknum) + ' language ' + str(lang))

                        vobsubdata, idxdata = self.vobsubDataForTrackNumber(tracknum)
                        assert(vobsubdata)
                        assert(idxdata)

                        newSub = caption.VobSubCaption(vobsubdata,idxdata,lang)
                        newSub.data_source = 'makemkv'
                        
                        assert(len(newSub.text)>0)
                        
                        logging.debug('Loaded caption: ' + str(newSub) + 'for index ' + str(subIndex))

                        self.subtitles[subIndex] = newSub
                        assert(self.subtitles[subIndex])

                    elif codec.lower() == 's_hdmv/pgs':
                        logging.debug('Loading PGS data for tracknum ' + str(tracknum) + ' language ' + str(lang))

                        '''sub subtract 1 from tracknumber when called mkextract'''
                        pgsdata = self.pgsDataForTrackNumber(tracknum)
                        assert(len(pgsdata)>0)

                        newSub = caption.PGSCaption(pgsdata,lang)
                        newSub.data_source = 'makemkv'
                        
                        assert(len(newSub.text)>0)
                        
                        logging.debug('Loaded caption: ' + str(newSub) + 'for index ' + str(subIndex))

                        self.subtitles[subIndex] = newSub
                        assert(self.subtitles[subIndex])

                    elif codec.lower() == 's_text/utf8':
                        logging.debug('Loading srt data for tracknum ' + str(tracknum) + ' language ' + str(lang))
                        #TODO

                    else:
                        logging.warn('Unrecognised subtitles codec: ' + codec)

                currentSubtitleIndex += 1



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

