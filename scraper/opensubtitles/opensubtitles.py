#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import os
import sys
import logging
import urllib2
import zipfile

dirname = os.path.dirname(os.path.realpath( __file__ ))


sys.path.append(os.path.join(dirname,".."))
from MediaContent import *

sys.path.append(os.path.join(dirname,"..",".."))
import caption

sys.path.append(os.path.join(dirname,"..","..","dependancies"))
import bs4


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


class OpenSubtitles:
    def __init__(self):
        logging.debug('OpenSubtitles initialized')
        self.serverBaseUrl = 'http://www.opensubtitles.org'

    def subtitlesForMovie(self,movieObject):
        return None
    
    def subtitlesForTVShow(self,tvshowObject):
        return None
    
    def subtitlesForTVEpisode(self,tvepisodeObject):
        imdbId = tvepisodeObject.unique_id
        
        urlSubListings = self._serverUrlWithImdbIdAndLanguage(imdbId,'en')
        
        htmlSubListings = urllib2.urlopen(urlSubListings).read()
        
        soupSubListings = bs4.BeautifulSoup(htmlSubListings)
        
        urlSubLinks = []
        
        for obj in soupSubListings.findAll('a',{'class':'bnone'}):
            jsLink = obj.__dict__['attrs']['onclick']
            jsLink = jsLink.replace('reLink(event,\'','')
            jsLink = jsLink[0:-3]
            
            fullLink = self.serverBaseUrl + jsLink
            
            urlSubLinks.append(fullLink)
        
        urlDownloadLinks = []
        
        for subPageLink in urlSubLinks:
            subPageHtml = urllib2.urlopen(subPageLink).read()
            
            urlDownloadLinks.append( self._getDownloadLinkFromSubtitlePage(subPageHtml) )
            
        subSrtData = []

        for downloadLink in urlDownloadLinks:
            data = urllib2.urlopen(urlDownloadLinks[0]).read()
            
            fTmp = open('/tmp/sub.zip','w')
            fTmp.write(data)
            fTmp.close()
            fTmp = open('/tmp/sub.zip', 'r')
            zip = zipfile.ZipFile(fTmp)
            
            for name in zip.namelist():
                if name.split('.')[-1] == 'srt':
                    zip.extract(name,'/tmp/sub_srt')
                    srtFile = '/tmp/sub_srt/' + os.listdir('/tmp/sub_srt')[0]
                    fSrt = open(srtFile,'r')
                    srtData = fSrt.read()
                    fSrt.close()
                    subSrtData.append(srtData)
                    
        captions = []
        
        for srtData in subSrtData:
            captionObj = caption.SRTCaption(srtData,'en')
            captions.append(captionObj)
        
        return captions
        
        
    def _serverUrlWithImdbIdAndLanguage(self,imdbId,language):
        #remove tt prefix
        if imdbId[0:2] == 'tt':
            imdbId = imdbId[2:len(imdbId)]
            
        language = self._get3CharLanguageCodeFromWord(language)

        serverUrlTemplate = 'http://www.opensubtitles.org/en/search/sublanguageid-$LANGUAGE/imdbid-$IMDBID'
        
        serverUrl = serverUrlTemplate
        
        serverUrl = serverUrl.replace('$IMDBID',imdbId)
        serverUrl = serverUrl.replace('$LANGUAGE',language)

        return serverUrl
        
    def _get3CharLanguageCodeFromWord(self,languageWord):
        retLan = None
        
        if len(languageWord) == 2:
            retLan = LANG_CODES[languageWord]
        elif len(languageWord) == 3:
            #nothing to do
            retLan = languageWord
        
        return retLan
        
    def _getDownloadLinkFromSubtitlePage(self,subPage):
        match = re.findall(r'if\(window\.chrome\)\s\{\n\s+directUrl\=\'.*?\'\;',subPage)[0]

        match = match[match.find('directUrl=\'')+len('directUrl=\''):len(match)]

        match = match[0:-2]

        return match


def test():
    s = OpenSubtitles()
    
    tvObj = TVEpisodeMedia()
    tvObj.unique_id = 'tt0751229' 
    
    subs = s.subtitlesForTVEpisode(tvObj)
    
    assert subs[0] == subs[1]
    assert subs[0].compareText(subs[1].text) >= 0.95
    
    dl_link = """asdf asdf asdf asdf asdf if(window.chrome) {
					   					directUrl='http://dl.opensubtitles.org/en/download/sub/5704576'; asdf asdf asdf asdf """
					   					
    assert s._getDownloadLinkFromSubtitlePage(dl_link) == 'http://dl.opensubtitles.org/en/download/sub/5704576'

    assert s._serverUrlWithImdbIdAndLanguage('tt123456','eng') == 'http://www.opensubtitles.org/en/search/sublanguageid-eng/imdbid-123456'
    assert s._serverUrlWithImdbIdAndLanguage('tt123456','en') == 'http://www.opensubtitles.org/en/search/sublanguageid-eng/imdbid-123456'


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    test()


