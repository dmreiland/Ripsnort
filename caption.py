#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import os
import sys
import difflib
import logging
import subprocess


import apppath

dirname = os.path.dirname(os.path.realpath( __file__ ))

sys.path.append( os.path.join(dirname,"utils") )
import string_match


COMPARE_MATCH_MIN_RATIO = 0.90


LANG_CODES ={ "en": "eng", 
            "fr" : "fre", 
            "hu": "hun", 
            "cs": "cze", 
            "pl" : "pol", 
            "sk" : "slo", 
            "pt" : "por", 
            "pt-br" : "pob", 
            "es" : "spa", 
            "el" : "ell", 
            "ar":"ara",
            'sq':'alb',
            "hy":"arm",
            "ay":"ass",
            "bs":"bos",
            "bg":"bul",
            "ca":"cat",
            "zh":"chi",
            "hr":"hrv",
            "da":"dan",
            "nl":"dut",
            "eo":"epo",
            "et":"est",
            "fi":"fin",
            "gl":"glg",
            "ka":"geo",
            "de":"ger",
            "he":"heb",
            "hi":"hin",
            "is":"ice",
            "id":"ind",
            "it":"ita",
            "ja":"jpn",
            "kk":"kaz",
            "ko":"kor",
            "lv":"lav",
            "lt":"lit",
            "lb":"ltz",
            "mk":"mac",
            "ms":"may",
            "no":"nor",
            "oc":"oci",
            "fa":"per",
            "ro":"rum",
            "ru":"rus",
            "sr":"scc",
            "sl":"slv",
            "sv":"swe",
            "th":"tha",
            "tr":"tur",
            "uk":"ukr",
            "vi":"vie"}


def convert2to3CharCode(lang):
    retLan = LANG_CODES[lang]
    return retLan


def convert3to2CharCode(lang):
    retLan = None
    for langCode in LANG_CODES.keys():
        if LANG_CODES[langCode] == lang:
            retLan = langCode
    return retLan

def convertSup2SubIdx(pgsData):
    if pgsData is None:
        logging.error('No PGS data given')
        return None
        
    pgsPath = apppath.BDSup2Sub()
    assert(pgsPath)
            
    tmpSupFile = os.path.join(apppath.pathTemporary('caption'),'subtitle.sup')
    tmpSubFile = os.path.join(apppath.pathTemporary('caption'),'subtitle.sub')
    tmpIdxFile = os.path.join(apppath.pathTemporary('caption'),'subtitle.idx')
        
    if os.path.exists(tmpSupFile):
        os.remove(tmpSupFile)
        
    fSup = open(tmpSupFile,'w')
    fSup.write(pgsData)
    fSup.close()
            
    if os.path.exists(tmpSubFile):
        os.remove(tmpSubFile)
            
    if os.path.exists(tmpIdxFile):
        os.remove(tmpIdxFile)
        
    cmdargs = [pgsPath,'-o',tmpSubFile,tmpSupFile]
        
    logging.debug('Running command: ' + ' '.join(cmdargs))

    cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    response = cmd.communicate()

    subData = None
    idxData = None
        
    if os.path.exists(tmpSubFile):
        logging.debug('Succesfully converted to sub file: ' + tmpSubFile)
        fSub = open(tmpSubFile)
        subData = fSub.read()
        fSub.close()
        os.remove(tmpSubFile)
        
    if os.path.exists(tmpIdxFile):
        logging.debug('Succesfully converted to idx file: ' + tmpIdxFile)
        fIdx = open(tmpIdxFile)
        idxData = fIdx.read()
        fIdx.close()
        os.remove(tmpIdxFile)
        
    if os.path.exists(tmpSupFile):
        os.remove(tmpSupFile)

    return [subData,idxData]


def convertSubIdxToSrt(vobsubData,idxData,language='en'):
    vobsubPath = apppath.vobsub2srt()
        
    if vobsubPath is None:
        return None
            
    tmpSubFile = os.path.join(apppath.pathTemporary('caption'),'subtitle.sub')
    tmpIdxFile = os.path.join(apppath.pathTemporary('caption'),'subtitle.idx')
    tmpSrtFile = os.path.join(apppath.pathTemporary('caption'),'subtitle.srt')
        
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
    
    #TODO vobsub2srt complains about language codes
    language = 'en'
    
    cmdargs = [vobsubPath,'--lang',language,tmpSubFile.split('.')[0]]

    logging.debug('Running command: ' + ' '.join(cmdargs))

    cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd.wait()
    response = cmd.communicate()

    srtData = None
    
    if os.path.exists(tmpSrtFile):
        fSrt = open(tmpSrtFile)
        srtData = fSrt.read()
        fSrt.close()
        logging.debug('Succesfully converted to srt file: ' + str(tmpSrtFile) + ', size(' + str(len(srtData)) +')')
        os.remove(tmpSrtFile)
    else:
        logging.warn('Failed to convert sub file to srt file: ' + str(response))

    if os.path.exists(tmpSubFile):
        os.remove(tmpSubFile)
        
    if os.path.exists(tmpIdxFile):
        os.remove(tmpIdxFile)

    return srtData


class Caption:
    def __init__(self,text,language):
        self.data_source = None
        self.data_unique_id = None
        self.text = text
        
        if len(language) == 2:
            self.languageCode2 = language
            self.languageCode3 = convert2to3CharCode(language)
            
        elif len(language) == 3:
            self.languageCode2 = convert3to2CharCode(language)
            self.languageCode3 = language

        self.language = self.languageCode3

        self.textCompare = Caption._textForComparison(self.text)
        
        textPrint = text
        if text is not None and len(text) > 200:
            textPrint = text[0:200]

        logging.debug('Caption initialized with lang:' + language + ' text:\n' + str(textPrint))
    
    def matchRatioWithCaption(self,caption,quickMatch=False):
        
        assert(caption)
        
        matchRatio = 0.0
        
        try:
            if self.textCompare == None:
                self.textCompare = Caption._textForComparison(self.text)
        
            textA = self.textCompare
        
            if caption.textCompare == None:
                caption.textCompare = Caption._textForComparison(caption.text)
            
            textB = caption.textCompare

            assert(len(textA)>0)
            assert(len(textB)>0)
        
            matchRatio = string_match.matchRatio(self.textCompare,caption.textCompare)
        except:
            pass

        logging.debug('Match ratio: ' + str(matchRatio))
        
        return matchRatio
    
    @staticmethod
    def _textForComparison(textReplace):
        textA = textReplace.lower()
        
        #remove any http links
        textA = re.sub(r'(https?:\/\/)?([\da-z\.-]+)\.([a-zA-Z\.]{2,32}).*\ ',' ',textA)
        textA = re.sub(r'(?:)opensubtitles[\.| ]org',' ',textA)
        textA = re.sub(r'\s{2,}',' ',textA)
        
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
        textA = re.sub(r'(?i)subtitles','',textA)
        textA = re.sub(r'(?i)media\ group','',textA)
        textA = re.sub(r'(?i)sdi','',textA)
        
        textA = re.sub(r'(?i)advertise your product or brand here.{1,3}contact today','',textA)
        
        textA = re.sub(r'(?i)Bio Cleanse Organic Detox','',textA)
        textA = re.sub(r'(?i)Support us and become VIP member.*to remove all ads from','',textA)
        
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
            if len(self.text) > 50:
                textPrint = self.text[0:50]
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

    def textSignature(self):
        textIntVal = 0
        for textChar in self.textCompare.strip().replace(' ',''):
            textIntVal += ord(textChar)

        return textIntVal

    def __eq__(self,cmp):
        if isinstance(cmp, Caption):
            return self.textSignature() == cmp.textSignature()
        else:
            return NotImplemented

    def __ne__(self,cmp):
        return not self.__eq__(cmp)
    
    def __lt__(self,cmp):
        if isinstance(cmp, Caption):
            return self.textSignature() < cmp.textSignature()
        else:
            return NotImplemented
    
    def __gt__(self,cmp):
        if isinstance(cmp, Caption):
            return self.textSignature() > cmp.textSignature()
        else:
            return NotImplemented
    
    def __le__(self,cmp):
        if isinstance(cmp, Caption):
            return self.textSignature() <= cmp.textSignature()
        else:
            return NotImplemented
    
    def __ge__(self,cmp):
        if isinstance(cmp, Caption):
            return self.textSignature() >= cmp.textSignature()
        else:
            return NotImplemented

    def  __hash__(self):
        hashVal = 0
        
        try:
            hashVal += self.textCompare.__hash__()
        except:
            pass
        
        try:
            hashVal += self.language.__hash__()
        except:
            pass
        
        try:
            hashVal += self.data_source.__hash__()
        except:
            pass
        
        try:
            hashVal += self.data_unique_id.__hash__()
        except:
            pass
        
        return hashVal

class SRTCaption(Caption):
    def __init__(self,srtRaw,language):
        assert(len(srtRaw)>0)

        srtText = SRTCaption._extractTextFromSRT(srtRaw)
        assert(len(srtText)>0)
        
        Caption.__init__(self,srtText,language)
        assert(len(self.language)>0)
        assert(len(self.text)>0)

        self.srt = srtRaw
        
        
    def __repr__(self):
        textPrint = ''
        if self.text is not None:
            if len(self.text) > 200:
                textPrint = self.text[0:200]
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
                
                if r is not None:
                    text = r.groups()[3]
                    #Remove any '<>' from text i.e. italics
                    text = re.sub(r'<[^>]*>','',text)
                    textReturn += text + '\n'
        except Exception as e:
            logging.error('Failed to extract srt:\n' + str(e))

        return textReturn


class VobSubCaption(Caption):
    def __init__(self,subRaw,idxRaw,lan):
        assert(len(subRaw)>0)
        assert(len(idxRaw)>0)
        
        langCode = None
        
        if len(lan) == 2:
            langCode = lan
        elif len(lan) == 3:
            langCode = convert3to2CharCode(lan)
        
        srtText = convertSubIdxToSrt(subRaw,idxRaw,langCode)
        
        logging.debug('Initialzing with text ' + str(len(srtText)) + ', ' + srtText[0:100])

        Caption.__init__(self,srtText,langCode)
        
        self.sub = subRaw
        self.idx = idxRaw
        
    def __repr__(self):
        textPrint = ''
        if self.text is not None:
            if len(self.text) > 50:
                textPrint = self.text[0:50]
            else:
                textPrint = self.text

        return '<VobSubCaption lan:' +str(self.language)+ ' data source:' +str(self.data_source)+ ' uniqueid:' +str(self.data_unique_id)+ ' \'' +textPrint+ '\'>'


class PGSCaption(Caption):
    def __init__(self,pgsRaw,lan):
        assert(len(pgsRaw)>0)

        subData, idxData = convertSup2SubIdx(pgsRaw)
        assert(len(subData)>0)
        assert(len(idxData)>0)
        
        srtData = convertSubIdxToSrt(subData,idxData)
        assert(len(srtData)>0)
        
        srtObj = SRTCaption(srtData,lan)
        
        Caption.__init__(self,srtObj.text,lan)

        self.pgs = pgsRaw
        
    def __repr__(self):
        textPrint = ''
        if self.text is not None:
            if len(self.text) > 200:
                textPrint = self.text[0:200]
            else:
                textPrint = self.text

        return '<VobSubCaption lan:' +str(self.language)+ ' data source:' +str(self.data_source)+ ' uniqueid:' +str(self.data_unique_id)+ ' \'' +textPrint+ '\'>'


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

