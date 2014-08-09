#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import os
import sys
import logging


import apppath


COMPARE_MATCH_MIN_RATIO = 0.8


class Caption:
    def __init__(self,text,language):
        self.text = text
        self.language = language
        logging.info('Initialized with text ' + str(text) + ', lang:' + language)
        
    def compareText(self,compareCaption):
        import difflib
        logging.debug('Comparing self.text: \'' + self.text + '\' to \'' + compareCaption + '\'')
        
        textCheckSelf = re.sub(r'\W+','',self.text)
        textCheckCompare = re.sub(r'\W+','',compareCaption)
        
        matchRatio = difflib.SequenceMatcher(None,textCheckSelf,compareCaption).ratio()
        logging.debug('Match ratio: ' + str(matchRatio))
        return matchRatio
        
    def __repr__(self):
        return '<Caption lan:' +self.language+ ' \'' + str(self.text) + '\'>'

    def __eq__(self,cmp):
        if isinstance(cmp, Caption):
            ratio = self.compareText(cmp.text)
            isMatch = ratio > COMPARE_MATCH_MIN_RATIO
            print isMatch
            return isMatch

        return NotImplemented
        
    def __ne__(self,cmp):
        return not self.__eq__(cmp)


class SRTCaption(Caption):
    def __init__(self,srtRaw):
        self.srt = srtRaw
        self.text = SRTCaption._extractTextFromSRT(srtRaw)
        
        Caption.__init__(self,self.text)
        
    def __repr__(self):
        return '<SRTCaption lan:' +self.language+ ' \'' + self.text + '\'>'

    @staticmethod
    def _extractTextFromSRT(srtText):
        splits = [s.strip() for s in re.split(r'\n\s*\n', srtText) if s.strip()]
        regex = re.compile(r'''(?P<index>\d+).*?(?P<start>\d{2}:\d{2}:\d{2},\d{3}) --> (?P<end>\d{2}:\d{2}:\d{2},\d{3})\s*.*?\s*(?P<text>.*)''', re.DOTALL)

        textReturn = ''

        for s in splits:
            r = regex.search(s)
            text = r.groups()[3]
            #Remove any '<>' from text i.e. italics
            text = re.sub(r'\<.*?\>','',text)
            textReturn += text + '\n'
            
        return textReturn


class VobSubCaption(Caption):
    def __init__(self,subRaw,idxRaw,lan):
        self.sub = subRaw
        self.idx = idxRaw
        
        self.language = lan
        
        srtData = VobSubCaption._convertVobSubToSRT(subRaw,idxRaw)
        self.text = SRTCaption(srtData).text
        
        Caption.__init__(self,self.text,lan)
        
    def __repr__(self):
        return '<VobSubCaption lan:' +self.language+ ' \'' + str(self.text) + '\'>'

    @staticmethod
    def _convertVobSubToSRT(vobsubData,idxData):
        vobsubPath = apppath.vobsub2srt()
        
        if vobsubPath is None:
            return None
            
        tmpPath = '/tmp/'
        tmpSubFile = os.path.join(tmpPath,'subtitle.sub')
        tmpIdxFile = os.path.join(tmpPath,'subtitle.idx')
        tmpSrtFile = os.path.join(tmpPath,'subtitle.srt')
        
        fSub = open(tmpSubFile,'w')
        fSub.write(vobsubData)
        fSub.close()
        
        fIdx = open(tmpIdxFile,'w')
        fIdx.write(vobsubData)
        fIdx.close()
        
        cmdargs = [vobsubPath,tmpSubFile.split('.')[0]]

        cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd.wait()
        response = cmd.communicate()

        srtData = None
        
        if os.path.exists(tmpSrtFile):
            fSrt = open(tmpSrtFile)
            srtData = fSrt.read()
            fSrt.close()

        os.remove(tmpSubFile)
        os.remove(tmpIdxFile)
        os.remove(tmpSrtFile)
        
        return srtData


def test():
    textA = '1234567890'
    textB = '0234567890'
    textC = '0034567890'
    textD = '-234567890'
    
    cA = Caption(textA)
    cB = Caption(textB)
    cC = Caption(textC)
    cD = Caption(textD)

    assert cA.compareText(cA.text) == 1.0
    assert cA.compareText(cB.text) == 0.9
    assert cA.compareText(cC.text) == 0.8
    assert cA.compareText(cD.text) == 0.9

    assert cA == cA
    assert cA == cB
    assert cA != cC


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test()

