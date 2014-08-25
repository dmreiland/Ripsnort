#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import os
import sys
import time
import shutil
import socket
import logging
import urllib2
import zipfile
import difflib
import xmlrpclib

dirname = os.path.dirname(os.path.realpath( __file__ ))


sys.path.append(os.path.join(dirname,".."))
from MediaContent import *

sys.path.append(os.path.join(dirname,"..",".."))
import caption



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
    def __init__(self,username='',password=''):
        self.serverBaseUrl = 'http://www.opensubtitles.org'
        self.server = xmlrpclib.ServerProxy('http://api.opensubtitles.org/xml-rpc')
        socket.setdefaulttimeout(10)
        self.sessionToken = self._logIn(username, password)
        logging.debug('OpenSubtitles initialized')

    def __del__(self):
        if self.sessionToken is not None:
            self._logOut(self.sessionToken)
    
    def subtitlesForMovie(self,movieObject,downloadLimit=5,language='eng'):
        captions = []
    
        imdbId = movieObject.unique_id.replace('tt','')

        logging.debug('Searching for: ' + str(imdbId) + ' language:' + language + ' max:' + str(downloadLimit))
        
        urlDownloadLinks = self._fetchZipDownloadLinks(imdbId,language)

        for downloadLink in urlDownloadLinks:
            captionObj = self._downloadZippedSrtAndLoadCaption(downloadLink,language)

            if captionObj is not None:
                captionObj.data_source = 'opensubtitles'
                captionObj.data_unique_id = 'tt' + imdbId

                captions.append(captionObj)
            else:
                logging.warn('Bad download link:' + downloadLink)

            if len(captions) > downloadLimit:
                break

        captions = self._removeSubtitleBadMatchesFromList(captions)
            
        logging.debug('Returning captions: ' + str(captions))
        return captions

    def subtitlesForTVEpisode(self,tvepisodeObject,downloadLimit=5,language='eng'):
        captions = []
    
        imdbId = tvepisodeObject.unique_id.replace('tt','')

        logging.debug('Searching for: ' + str(imdbId) + ' language:' + language + ' max:' + str(downloadLimit))
        
        urlDownloadLinks = self._fetchZipDownloadLinks(imdbId,language,tvepisodeObject.season_number,tvepisodeObject.episode_number)

        for downloadLink in urlDownloadLinks:
            captionObj = self._downloadZippedCaptionAndExtract(downloadLink,language)

            if captionObj is not None and len(captionObj.text) > 0:
                captionObj.data_source = 'opensubtitles'
                captionObj.data_unique_id = 'tt' + imdbId

                captions.append(captionObj)
            else:
                logging.warn('Bad download link:' + downloadLink)

            if len(captions) > downloadLimit:
                break

        captions = self._removeSubtitleBadMatchesFromList(captions)
            
        logging.debug('Returning captions: ' + str(captions))
        return captions
        
    def _logIn(self,username='',password='',language='eng',retryCount=3):
        sessionToken = None

        try:
            # Connection to opensubtitles.org server
            session = self.server.LogIn(username, password, language, 'OS Test User Agent')

            if session is None or session['status'] != '200 OK':
                logging.error('Failed to login to opensubtitles: ' + str(session))
            else:
                sessionToken = session['token']

        except Exception:
            time.sleep(1)

            if retryCount > 0:
                sessionToken = self._logIn(username,password,language,retryCount-1)

        return sessionToken
        
    def _logOut(self,token):
        self.server.LogOut(token)
        
    def _fetchZipDownloadLinks(self,imdbId,language=None,seasonNumber=None,episodeNumber=None,retryCount=1):
        zipDownloadLinks = []
        
        searchDict = {'imdbid':imdbId}
        
        if language is not None:
            searchDict['sublanguageid'] = language
            
#        if seasonNumber is not None:
#            searchDict['season'] = seasonNumber
#            
#        if episodeNumber is not None:
#            searchDict['episode'] = episodeNumber
        
        logging.debug('Searching Opensubtitles with token: ' + str(self.sessionToken) + ' params: ' + str(searchDict))
        
        searchList = []
        searchList.append(searchDict)
        
        results = {}
        results['data'] = []
        
        try:
            results = self.server.SearchSubtitles(self.sessionToken,searchList)
        except:
            if retryCount > 1:
                results = self._downloadZippedCaptionAndExtract(imdbId,language,seasonNumber,episodeNumber,retryCount-1)
            else:
                logging.error('Failed to search for subtitles: ' + str(searchDict))

#        logging.debug('Got response: ' + str(results))
        
        #Sometimes data is set to False.
        if results is None or results['data'] == False:
            logging.warn('Fetch failed: ' + str(results))
            results['data'] = []

        for result in results['data']:
            zipLink = result['ZipDownloadLink']
            zipDownloadLinks.append(zipLink)
        
        return zipDownloadLinks

    def _downloadZippedCaptionAndExtract(self,downloadLink,language):
        captionObj = None
        
        logging.debug('Downloading link: ' + str(downloadLink))
        
        try:
            data = urllib2.urlopen(downloadLink).read()
        except urllib.error.HTTPError as e:
            logging.error('Failed to fetch download link: ' + str(downloadLink) + ', err:' + str(e))
        
        if data is None:
            logging.error('Failed to download: ' + str(downloadLink))
            return None

        tmpZip = os.path.join('/','tmp','sub.zip')

        fTmp = open(tmpZip,'w')
        fTmp.write(data)
        fTmp.close()

        fTmp = open(tmpZip, 'r')

        zip = zipfile.ZipFile(fTmp)

        extractPath = os.path.join('/','tmp','subtemp')

        if os.path.exists(extractPath):
            shutil.rmtree(extractPath)
            
        zip.extractall(extractPath)
        
        for name in os.listdir(extractPath):
            extension = name.split('.')[-1]

            if extension == 'xml' or extension == 'html' or extension == 'txt' or extension == 'nfo':
                '''Ignore file'''
                pass
            elif extension == 'srt':
                zip.extract(name,extractPath)
                extractedFile = os.path.join(extractPath,os.listdir(extractPath)[0])
                fSrt = open(extractedFile,'r')
                srtData = fSrt.read()
                fSrt.close()
                captionObj = caption.SRTCaption(srtData,language)
                os.remove(extractedFile)

#            elif extension == 'sub':
#                zip.extract(name,extractPath)
#                extractedFile = os.path.join(extractPath,os.listdir(extractPath)[0])
#                fSub = open(extractedFile,'r')
#                subData = fSub.read()
#                fSub.close()
#                captionObj = caption.VobSubCaption(subData,None,language)
#                os.remove(extractedFile)

            else:
                logging.error('Unrecognised file:' + str(name))

        if os.path.exists(extractPath):
            shutil.rmtree(extractPath)

        fTmp.close()
        
        os.remove(tmpZip)

        return captionObj
        
    def _get3CharLanguageCodeFromWord(self,languageWord):
        retLan = None
        
        if len(languageWord) == 2:
            retLan = LANG_CODES[languageWord]
        elif len(languageWord) == 3:
            #nothing to do
            retLan = languageWord
        
        return retLan
    
    def _removeSubtitleBadMatchesFromList(self,captions):
        sortedList = []
            
        #loop through the captions and check if any stand out and remove
        for i in range(len(captions)):
            caption = captions[i]
            captionCompareTextList = []
            for caption in captions:
                captionCompareTextList.append(caption.text)
            
            compareResults = difflib.get_close_matches(caption.text,captionCompareTextList)
            
            if len(compareResults) > 0:
                sortedList.append(caption)
            
        return sortedList


def test():
    s = OpenSubtitles()
    
    tvObjEp1 = TVEpisodeMedia()
    tvObjEp1.unique_id = 'tt0751094' 
    
    subsEp1 = s.subtitlesForMovie(tvObjEp1)
    
    assert subsEp1[0].matchRatioWithCaption(subsEp1[1]) >= 0.90
    assert subsEp1[0] == subsEp1[1]
    
    s = OpenSubtitles()

    tvObjEp2 = TVEpisodeMedia()
    tvObjEp2.unique_id = 'tt0751208'
    
    subsEp2 = s.subtitlesForMovie(tvObjEp2)
    
    assert subsEp2[0].matchRatioWithCaption(subsEp2[1]) >= 0.90
    assert subsEp2[0] == subsEp2[1]

    assert subsEp1[0] != subsEp2[0]
    assert subsEp1[1] != subsEp2[1]
    assert subsEp1[1] != subsEp2[0]

    tvObjTest3 = TVEpisodeMedia()
    tvObjTest3.unique_id = '0502251'
    
    tvObjTest3subs = s.subtitlesForMovie(tvObjEp1)
    assert len(tvObjTest3subs) > 0

    movieObj = MovieMedia()
    movieObj.unique_id = 'tt0095016'
    
    movieSubs = s.subtitlesForMovie(movieObj)
    
    assert movieSubs[0] == movieSubs[1]
    
    assert movieSubs[0].matchRatioWithCaption(movieSubs[1]) >= 0.90
    
    assert movieSubs[0] != subsEp1[0]
    assert movieSubs[0] != subsEp1[1]

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    test()


