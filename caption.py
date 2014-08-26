#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import os
import sys
import logging
import subprocess


import apppath

dirname = os.path.dirname(os.path.realpath( __file__ ))

sys.path.append( os.path.join(dirname,"utils") )
import levenshtein_distance


COMPARE_MATCH_MIN_RATIO = 0.90


class Caption:
    def __init__(self,text,language):
        self.data_source = None
        self.data_unique_id = None
        self.text = text
        self.language = language
        '''Cached copy of text comparison'''
        self.textCompare = None
        logging.debug('Caption initialized with lang:' + language + ' text:\n' + str(text))
    
    def matchRatioWithCaption(self,caption):
        
        if self.textCompare == None:
            self.textCompare = Caption._textForComparison(self.text)
        
        textA = self.textCompare
        
        if caption.textCompare == None:
            caption.textCompare = Caption._textForComparison(caption.text)
            
        textB = caption.textCompare
        
        distance = abs( float( levenshtein_distance.distanceBetweenStrings(textA,textB) ) )

        textALen = len(textA)
        matchRatio = (textALen-distance) / textALen
        matchRatio = abs(matchRatio)

        logging.debug('Match ratio: ' + str(matchRatio))
        
        return matchRatio
    
    @staticmethod
    def _textForComparison(textReplace):
        textA = textReplace.lower()
        
        #remove additional text not part of the subtitles
        textA = textA.replace('best watched using open subtitles mkv player','')
        textA = textA.replace('subtitles downloaded from www.opensubtitles.org','')
        textA = re.sub(r'synchro\:.*\n','',textA)
        textA = re.sub(r'transcript\:.*\n','',textA)
        textA = re.sub(r'rearranged\ by\ .*\n','',textA)
        textA = re.sub(r'visiontext\ subtitles\:\ .*\n','',textA)
        textA = re.sub(r'visiontext\ subtitles\ by.*\n','',textA)
        textA = re.sub(r'english\ sdh\n','',textA)
        textA = re.sub(r'english\n','',textA)
        textA = re.sub(r'shared\ by.*\n','',textA)
        textA = re.sub(r'\n.*corrected\ by.*\n','',textA)
        textA = re.sub(r'\n.*all subtit?les are (?:4|for) evalution use only.*\n','',textA)
        
        #remove html
        textA = re.sub(r'<[^>]*>','',textA)
        
        #remove anything in round brackets
        textA = re.sub('\(.*\)',' ',textA)

        #remove anything in square brackets
        textA = re.sub('\[.*\]',' ',textA)
        
        #remove '
        textA = textA.replace('\'','')
        
        #remove any special characters
        textA = re.sub('\W',' ',textA)
        
        #remove any double/triple whitespace
        textA = re.sub('\s+', textA, ' ')
        
        textA = textA.replace(' a ',' ')
        textA = textA.replace(' at ',' ')
        textA = textA.replace(' an ',' ')
        textA = textA.replace(' by ',' ')
        textA = textA.replace(' of ',' ')
        textA = textA.replace(' or ',' ')
        textA = textA.replace(' in ',' ')
        textA = textA.replace(' is ',' ')
        textA = textA.replace(' it ',' ')
        textA = textA.replace(' for ',' ')
        textA = textA.replace(' the ',' ')
        textA = textA.replace(' this ',' ')

        textA = re.sub('\W',' ',textA)
        
        #remove any double/triple whitespace
        textA = re.sub('\s{2,}',' ',textA)

        return textA.strip()
        
    def __repr__(self):
        textPrint = ''
        if self.text is not None:
            if len(self.text) > 30:
                textPrint = self.text[0:30]
            else:
                textPrint = self.text

        return '<Caption lan:' +str(self.language)+ ' data source:' +str(self.data_source)+ ' uniqueid:' +str(self.data_unique_id)+ ' \'' +textPrint+ '\'>'
    
    def findClosestMatchFromCaptions(self,captionsList):
        closestMatch = None
        closestRatio = 0.0
        
        for captionCmp in captionsList:
            ratioCmp = self.matchRatioWithCaption(captionCmp)
            
            if ratioCmp > closestRatio:
                closestMatch = captionCmp
                closestRatio = ratioCmp
                
        logging.debug('Closest match to: ' +str(self)+ ' -> ' + str(closestMatch))

        return closestMatch

    def __eq__(self,cmp):
        if isinstance(cmp, Caption):
            ratio = self.matchRatioWithCaption(cmp)
            isMatch = ratio > COMPARE_MATCH_MIN_RATIO
            print isMatch
            return isMatch

        return NotImplemented
        
    def __ne__(self,cmp):
        return not self.__eq__(cmp)


class SRTCaption(Caption):
    def __init__(self,srtRaw,language):
        self.srt = srtRaw
        self.text = SRTCaption._extractTextFromSRT(srtRaw)
        self.language = language
        
        Caption.__init__(self,self.text,language)
        
    def __repr__(self):
        textPrint = ''
        if self.text is not None:
            if len(self.text) > 30:
                textPrint = self.text[0:30]
            else:
                textPrint = self.text

        return '<SRTCaption lan:' +str(self.language)+ ' data source:' +str(self.data_source)+ ' uniqueid:' +str(self.data_unique_id)+ ' \'' +textPrint+ '\'>'

    @staticmethod
    def _extractTextFromSRT(srtText):
        splits = [s.strip() for s in re.split(r'\n\s*\n', srtText) if s.strip()]
        regex = re.compile(r'''(?P<index>\d+).*?(?P<start>\d{2}:\d{2}:\d{2},\d{3}) --> (?P<end>\d{2}:\d{2}:\d{2},\d{3})\s*.*?\s*(?P<text>.*)''', re.DOTALL)

        textReturn = ''

        try:
            for s in splits:
                r = regex.search(s)
                text = r.groups()[3]
                #Remove any '<>' from text i.e. italics
                text = re.sub(r'\<.*?\>','',text)
                textReturn += text + '\n'
        except:
            logging.error('Failed to extract srt:\n' + srtText)

        return textReturn


class VobSubCaption(Caption):
    def __init__(self,subRaw,idxRaw,lan):
        self.sub = subRaw
        self.idx = idxRaw
        
        self.language = lan
        
        srtData = VobSubCaption._convertVobSubToSRT(subRaw,idxRaw)
        self.text = SRTCaption(srtData,lan).text
        
        Caption.__init__(self,self.text,lan)
        
    def __repr__(self):
        textPrint = ''
        if self.text is not None:
            if len(self.text) > 30:
                textPrint = self.text[0:30]
            else:
                textPrint = self.text

        return '<VobSubCaption lan:' +str(self.language)+ ' data source:' +str(self.data_source)+ ' uniqueid:' +str(self.data_unique_id)+ ' \'' +textPrint+ '\'>'

    @staticmethod
    def _convertVobSubToSRT(vobsubData,idxData):
        vobsubPath = apppath.vobsub2srt()
        
        if vobsubPath is None:
            return None
            
        tmpSubFile = os.path.join('/','tmp','subtitle.sub')
        tmpIdxFile = os.path.join('/','tmp','subtitle.idx')
        tmpSrtFile = os.path.join('/','tmp','subtitle.srt')
        
        if os.path.exists(tmpSubFile):
            os.remove(tmpSubFile)
        
        if os.path.exists(tmpIdxFile):
            os.remove(tmpIdxFile)
        
        if os.path.exists(tmpSrtFile):
            os.remove(tmpSrtFile)
        
        fSub = open(tmpSubFile,'w')
        fSub.write(vobsubData)
        fSub.close()
        
        if idxData is not None:
            fIdx = open(tmpIdxFile,'w')
            fIdx.write(idxData)
            fIdx.close()
        
        cmdargs = [vobsubPath,tmpSubFile.split('.')[0]]
        
        logging.debug('Running command: ' + ' '.join(cmdargs))

        cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd.wait()
        response = cmd.communicate()

        srtData = None
        
        if os.path.exists(tmpSrtFile):
            logging.debug('Succesfully converted to srt file: ' + tmpSrtFile)
            fSrt = open(tmpSrtFile)
            srtData = fSrt.read()
            fSrt.close()
            os.remove(tmpSrtFile)

        os.remove(tmpSubFile)
        
        if os.path.exists(tmpIdxFile):
            os.remove(tmpIdxFile)

        return srtData


def test():
    textA = '1234567890'
    textB = '0234567890'
    textC = '0034567890'
    textD = '-234567890'
    textE = '0000000000'
    textF = 'ABCDEFGHIJ'
    
    cA = Caption(textA,'en')
    cB = Caption(textB,'en')
    cC = Caption(textC,'en')
    cD = Caption(textD,'en')
    cE = Caption(textE,'en')
    cF = Caption(textF,'en')

    assert cA.matchRatioWithCaption(cA.text) == 1.0
    assert cA.matchRatioWithCaption(cB.text) == 0.9
    assert cA.matchRatioWithCaption(cC.text) == 0.8
    assert cA.matchRatioWithCaption(cD.text) == 0.9
    assert cA.matchRatioWithCaption(cE.text) == 0.1
    assert cA.matchRatioWithCaption(cF.text) == 0.0

    assert cA == cA
    assert cA != cB
    assert cA != cC

    assert cA.findClosestMatchFromCaptions([cE,cF]) == cE
    assert cA.findClosestMatchFromCaptions([cF,cE]) == cE
    assert cA.findClosestMatchFromCaptions([cD,cE,cF]) == cD
    assert cA.findClosestMatchFromCaptions([cF,cE,cD]) == cD
    assert cA.findClosestMatchFromCaptions([cF,cD,cE]) == cD
    assert cA.findClosestMatchFromCaptions([cD,cE,cD]) == cD
    assert cA.findClosestMatchFromCaptions([cD,cD,cD]) == cD

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test()

