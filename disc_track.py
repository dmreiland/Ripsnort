#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json


class disc_track:

    def __init__(self,dictLoad=None):
        self.disc_name=''
        self.bytes=0
        self.megabytes=0.0
        self.gigabytes=0.0
        self.chapters=0.0
        self.durationS=0.0
        self.segmentsMap=[]
        self.titleID=0
        self.trackNumber=0
        self.outputFileName=''
        
        if ( dictLoad is not None ) and ( type(dictNone) == dict ):
            self.disc_name = dictLoad['discname']
            self.bytes = dictLoad['bytes']
            self.megabytes = self.bytes / 1024 / 1024
            self.gigabytes = self.bytes / 1024 / 1024 / 1024
            self.chapters = dictLoad['chapters']
            self.durationS = dictLoad['duration']
            self.segmentsMap = dictLoad['segmentsmap']
            self.titleID = dictLoad['titleid']
            self.trackNumber = dictLoad['tracknumber']
            self.outputFileName = dictLoad['filename']

    def serialize(self):
        retDict = {}
        
        retDict['discname'] = self.disc_name
        retDict['bytes'] = self.bytes
        retDict['chapters'] = self.chapters
        retDict['duration'] = self.durationS
        retDict['segmentsmap'] = self.segmentsMap
        retDict['titleid'] = self.titleID
        retDict['tracknumber'] = self.trackNumber
        retDict['filename'] = self.outputFileName
        
        return json.dumps(retDict)
        
    def __repr__(self):
        retStr = '<disc_track '
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
    
    def containsAllSegmentMapsFromDiscTrack(self,diskTrackCmp):
        isMatch = True
        
        for i in range(len(diskTrackCmp.segmentsMap)):
            segMapCmp = diskTrackCmp.segmentsMap[i]
            
            foundMatch = False
            
            for k in range(len(self.segmentsMap)):
                segMapSelf = diskTrackCmp.segmentsMap[i]
                
                if segMapSelf == segMapCmp:
                    foundMatch = True
                    break
            
            if not foundMatch:
                isMatch = False
                break

        return isMatch
    
    
if __name__ == "__main__":
    dictLoad = {}

    dictLoad['discname'] = 'disc'
    dictLoad['bytes'] = 999
    dictLoad['chapters'] = 10
    dictLoad['duration'] = 300
    dictLoad['segmentsmap'] = [[0,1],[2,3]]
    dictLoad['titleid'] = 1
    dictLoad['filename'] = 'file1'

    track = disc_track(dictLoad)

    assert track.disc_name == 'disc'
    assert track.bytes == 999
    assert track.chapters == 10
    assert track.durationS == 300
    assert track.segmentsMap == [[0,1],[2,3]]
    assert track.titleID == 1
    assert track.outputFileName == 'file1'
