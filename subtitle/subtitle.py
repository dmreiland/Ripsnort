#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import os
import sys
import logging
import subprocess


from caption import SRTCaption
from caption import VobSubCaption


class Subtitle:
    @staticmethod
    def extractSubtitlesFromVideoFile(videoFile):
        fileBaseName = os.path.basename(videoFile)
        fileExt = None
        
        if '.' in fileBaseName:
            fileExt = fileBaseName.split('.')[-1]
            fileBaseName = fileBaseName[0:-(len(fileExt))-1]

        subtitleTrackNumbers = Subtitle.subtitleTrackNumbersFromVideoFile(videoFile)
        
        subtitleFiles = []
        
        for track in subtitleTrackNumbers:
            ext = Subtitle.subtitleTypeForTrackNumber(videoFile,track).lower()
            subfilename = fileBaseName + '_' + str(track) + '.' + ext
            path = os.path.join(Subtitle.temporaryDirectory(),subfilename)
            
            if Subtitle.extractSubtitlesFromTrackNumber(videoFile,track,path):
                subtitleFiles.append( path )
        
        #Now convert filedata to Caption objects and delete temporary files
        for i in range(len(subtitleFiles)):
            subFile = subtitleFiles[i]
            ext = subFile.split('.')[-1]
            
            if ext.lower() == 'vobsub':
                idxFile = subFile.replace('.sub','.idx')
                subData = open(subFile,'r').read()
                idxData = open(idxFile,'r').read()

                sub = VobSubCaption(subData,idxData)
                subtitleFiles[i] = sub
                
                os.remove(subFile)
                os.remove(idxFile)
                
            elif ext.lower() == 'srt':
                srtData = open(subFile,'r').read()

                sub = SRTCaption(srtData)
                subtitleFiles[i] = sub
                
                os.remove(subFile)

            else:
                logging.error('Unknown subtitle: ' + ext)
                sys.exit(1)
        
        print subtitleFiles
    
    @staticmethod
    def mkvExtractPath():
        mkvextractPath = None

        import platform
        platformName = platform.system().lower().strip()

        if platformName == 'darwin':
            path = '/Applications/Mkvtoolnix.app/Contents/MacOS/mkvextract'
            
            if os.path.isfile(path):
                mkvextractPath = path

        elif platformName == 'windows':
            logging.error( 'No windows support yet' )
            sys.exit(1)

        elif platformName == 'linux':
            try:
                cmdargs = ['which','mkvextract']
                logging.info('Running command: ' + ' '.join(cmdargs))
                cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cmd.wait()
                response = cmd.communicate()
                mkvextractPath = response[0].strip()
            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to call makemkv: ' + str(e.output) )
                sys.exit(1)

        return mkvextractPath
        
    @staticmethod
    def mkvMergePath():
        mkvmergePath = None

        import platform
        platformName = platform.system().lower().strip()

        if platformName == 'darwin':
            path = '/Applications/Mkvtoolnix.app/Contents/MacOS/mkvmerge'
            
            if os.path.isfile(path):
                mkvmergePath = path

        elif platformName == 'windows':
            logging.error( 'No windows support yet' )
            sys.exit(1)

        elif platformName == 'linux':
            try:
                cmdargs = ['which','mkvmerge']
                logging.info('Running command: ' + ' '.join(cmdargs))
                cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cmd.wait()
                response = cmd.communicate()
                mkvmergePath = response[0].strip()
            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to call makemkv: ' + str(e.output) )
                sys.exit(1)

        return mkvmergePath

    @staticmethod
    def vobsub2srtPath():
        vobsrtPath = None

        import platform
        platformName = platform.system().lower().strip()

        if platformName == 'darwin':
            logging.error( 'No mac support yet' )
            sys.exit(1)

        elif platformName == 'windows':
            logging.error( 'No windows support yet' )
            sys.exit(1)

        elif platformName == 'linux':
            try:
                cmdargs = ['which','vobsub2srt']
                logging.info('Running command: ' + ' '.join(cmdargs))
                cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cmd.wait()
                response = cmd.communicate()
                vobsrtPath = response[0].strip()
            except subprocess.CalledProcessError as e:
                logging.error( 'Failed to call makemkv: ' + str(e.output) )
                sys.exit(1)

        return vobsrtPath
    
    @staticmethod
    def temporaryDirectory():
        tmpDir = '/tmp/ripsnort/subtitles'
            
        if not os.path.isdir(tmpDir):
            os.makedirs(tmpDir)

        if not os.path.isdir(tmpDir):
            #Failed to create dir
            tmpDir = None

        return tmpDir
        
    @staticmethod
    def subtitleTrackNumbersFromVideoFile(videoFile):
        mkvmergeBin = Subtitle.mkvMergePath()

        cmdargs = [mkvmergeBin,'-i',videoFile]
        logging.info('Running command: ' + ' '.join(cmdargs))
        cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd.wait()
        response = cmd.communicate()
        
        tracks = []
        
        for line in response[0].split('\n'):
            if ': subtitles ' in line:
                line = re.sub('Track ID','',line)
                line = re.sub(r'\:.*','',line)
                line = line.strip()
                tracks.append( int(line) )
        
        return tracks
        
    @staticmethod
    def subtitleTypeForTrackNumber(videoFile,trackNumber):
        mkvmergeBin = Subtitle.mkvMergePath()

        cmdargs = [mkvmergeBin,'-i',videoFile]
        logging.info('Running command: ' + ' '.join(cmdargs))
        cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd.wait()
        response = cmd.communicate()
        
        subtitleType = None
        
        for line in response[0].split('\n'):
            strSearch = str(trackNumber) + ': subtitles '
            if strSearch in line:
                #find the last bracketed word on this line
                result = re.search(r'\(.*?\)$',line).group()
                #remove '(' and ')'
                subtitleType = result[1:-1]
        
        return subtitleType

    @staticmethod
    def extractSubtitlesFromTrackNumber(videoFile,subtitleTrackNumber,subtitleFile):
        if os.path.isfile(subtitleFile):
            #TODO remove file
            pass
    
        didSave = False
    
        mkvextractBin = Subtitle.mkvExtractPath()

        cmdargs = [mkvextractBin,'tracks',videoFile,str(subtitleTrackNumber)+':'+subtitleFile]
        logging.info('Running command: ' + ' '.join(cmdargs))
        cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd.wait()
        response = cmd.communicate()
        
        if os.path.isfile(subtitleFile):
            return didSave
        
        return didSave

        
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

#     assert Subtitle.mkvExtractPath() != None
#     assert Subtitle.mkvMergePath() != None
#     assert Subtitle.vobsub2srtPath() == None
    
#     subs = Subtitle.subtitleTrackNumbersFromVideoFile('/Users/ryan/Movies/Bones - S01E05 - A Boy in a Bush.mkv')
    Subtitle.extractSubtitlesFromVideoFile('/Users/ryan/Movies/Bones - S01E05 - A Boy in a Bush.mkv')


