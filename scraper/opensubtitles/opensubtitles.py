#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import os
import sys
import time
import shutil
import socket
import logging
import urllib
import urllib2
import zipfile
import difflib
import xmlrpclib

dirname = os.path.dirname(os.path.realpath( __file__ ))


sys.path.append(os.path.join(dirname,".."))
from MediaContent import *

sys.path.append(os.path.join(dirname,"..",".."))
import caption
import apppath



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
            "el":"gre",
            "el":"grc",
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
        logging.debug('OpenSubtitles initialized: ' + str(self.sessionToken) + ', ' + str(username) + ':' + str(password))

    def __del__(self):
        if self.sessionToken is not None:
            self._logOut(self.sessionToken)
    
    def subtitlesForMovie(self,movieObject,downloadLimit=3,language='eng'):
        captions = []
        
        language = self._get3CharLanguageCodeFromWord(language)
    
        imdbId = movieObject.unique_id.replace('tt','')

        logging.debug('Searching for: ' + str(imdbId) + ' language:' + language + ' max:' + str(downloadLimit))
        
        urlDownloadLinks = self._fetchZipDownloadLinks(imdbId,language)

        logging.debug('Got download links: ' + str(urlDownloadLinks))

        for downloadLink in urlDownloadLinks:
            captionObj = self._downloadZippedCaptionAndExtract(downloadLink,language)
            logging.debug('Got caption ' + str(captionObj))

            if captionObj:
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

    def subtitlesForTVEpisode(self,tvepisodeObject,downloadLimit=3,language='eng'):
        captions = []
        
        language = self._get3CharLanguageCodeFromWord(language)
    
        imdbId = tvepisodeObject.unique_id.replace('tt','')

        logging.debug('Searching for: ' + str(imdbId) + ' language:' + language + ' max:' + str(downloadLimit))
        
        urlDownloadLinks = self._fetchZipDownloadLinks(imdbId,language,tvepisodeObject.season_number,tvepisodeObject.episode_number)

        logging.debug('Got download links: ' + str(urlDownloadLinks))

        for downloadLink in urlDownloadLinks:
            captionObj = self._downloadZippedCaptionAndExtract(downloadLink,language)
            logging.debug('Got caption ' + str(captionObj))

            if captionObj is not None and len(captionObj.text) > 0:
                captionObj.data_source = 'opensubtitles'
                captionObj.data_unique_id = 'tt' + imdbId

                captions.append(captionObj)
            else:
                logging.warn('Bad download link:' + downloadLink)

            if len(captions) > downloadLimit:
                break

        captions = self._removeSubtitleBadMatchesFromList(captions)
        
        #remove duplicates
        if captions:
            captions = list(set(captions))

        logging.debug('Returning captions: ' + str(captions))
        return captions
        
    def _logIn(self,username='',password='',language='eng',retryCount=3):
        sessionToken = None

        try:
            # Connection to opensubtitles.org server
            session = self.server.LogIn(username, password, language, 'ripsnort')

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

            logging.debug('Got subtitle response: ' + str(results))
        
            #Sometimes data is set to False.
            if results is None or results['data'] == False:
                logging.warn('Fetch failed: ' + str(results))
                results['data'] = []

            for result in results['data']:
                zipLink = result['ZipDownloadLink']
                zipDownloadLinks.append(zipLink)
        except:
            if retryCount > 1:
                results = self._fetchZipDownloadLinks(imdbId,language,seasonNumber,episodeNumber,retryCount-1)
            else:
                logging.error('Failed to search for subtitles: ' + str(searchDict))
        
        logging.debug('Returning zip links' + str(zipDownloadLinks))
        return zipDownloadLinks

    def _downloadZippedCaptionAndExtract(self,downloadLink,language):
        captionObj = None
        
        logging.debug('Downloading link: ' + str(downloadLink))
        
        try:
            data = urllib2.urlopen(downloadLink).read()
        except Exception as e:
            logging.error('Failed to fetch download link: ' + str(downloadLink) + ', err:' + str(e))
            data = None
        
        if data is None:
            logging.error('Failed to download: ' + str(downloadLink))
            return None
        
        tmpZip = os.path.join(apppath.pathTemporary('opensubtitles'),'sub.zip')

        fTmp = open(tmpZip,'w')
        fTmp.write(data)
        fTmp.close()

        fTmp = open(tmpZip, 'r')

        extractPath = os.path.join(apppath.pathTemporary('opensubtitles'),'subtemp')

        if os.path.exists(extractPath):
            shutil.rmtree(extractPath)
            
        os.makedirs(extractPath)
            
        try:
            zip = zipfile.ZipFile(fTmp)
            zip.extractall(extractPath)
        except Exception as e:
            logging.error('Failed to extract zip: ' + str(e))
            return None

        for name in os.listdir(extractPath):
            extension = name.split('.')[-1]

            if extension == 'xml' or extension == 'html' or extension == 'txt' or extension == 'nfo':
                logging.info('Ignoring file ' + name)

            elif extension == 'srt':
                zip.extract(name,extractPath)
                extractedFile = os.path.join(extractPath,name)
                fSrt = open(extractedFile,'r')
                srtData = fSrt.read()
                #tmp
                open('/tmp/srttext.a','w').write(srtData)
                assert(len(srtData)>0)
                fSrt.close()
                
                try:
                    captionObj = caption.SRTCaption(srtData,language)
                except Exception as e:
                    logging.error('Failed to extract srt from file ' + extractedFile + ', ' + downloadLink + ', ' + str(e)) 
                    pass

                os.remove(extractedFile)
                logging.debug('Got SRT caption: ' + str(captionObj))
                break

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
        #Order captions by Caption.textSignature()
        captions.sort()
        sortedList = captions
        
        arrayValsSorted = False
        
        #keep removing edge captions idx(0,-1) that are greater than 10% away from the middle until. This should remove any odd looking subtitles from the 'norm'
        while not arrayValsSorted:
            didSort = False
            if len(sortedList) >= 2:
                captIntA = float( sortedList[0].textSignature() )
                captIntB = float( sortedList[1].textSignature() )
                delta = abs(captIntB/captIntA) % 1.0
                
                if delta > 0.1:
                    sortedList.remove(sortedList[0])
                    didSort = True

            if len(sortedList) >= 2:
                captIntA = float( sortedList[-1].textSignature() )
                captIntB = float( sortedList[-2].textSignature() )
                delta = abs(captIntB/captIntA) % 1.0
                
                if delta > 0.1:
                    del sortedList[-1]
                    didSort = True
                    
            if not didSort:
                arrayValsSorted = True
            
        return sortedList

def test():
    s = OpenSubtitles()
    
    tvObjEp1 = TVEpisodeMedia()
    tvObjEp1.unique_id = 'tt0751094' 
    
    subsEp1 = s.subtitlesForMovie(tvObjEp1)
    
    assert(len(subsEp1)>=1)
    
    assert subsEp1[0].matchRatioWithCaption(subsEp1[0]) >= 0.90
    assert subsEp1[0] == subsEp1[0]
    
    s = OpenSubtitles()

    tvObjEp2 = TVEpisodeMedia()
    tvObjEp2.unique_id = 'tt0751208'
    
    subsEp2 = s.subtitlesForMovie(tvObjEp2)
    
    assert subsEp2[0].matchRatioWithCaption(subsEp2[0]) >= 0.90
    assert subsEp2[0] == subsEp2[0]

    assert subsEp1[0] != subsEp2[0]

    tvObjTest3 = TVEpisodeMedia()
    tvObjTest3.unique_id = '0502251'
    
    tvObjTest3subs = s.subtitlesForMovie(tvObjEp1)
    assert len(tvObjTest3subs) > 0

    movieObj = MovieMedia()
    movieObj.unique_id = 'tt0095016'
    
    movieSubs = s.subtitlesForMovie(movieObj)
    
    assert movieSubs[0] == movieSubs[0]
    
    assert movieSubs[0].matchRatioWithCaption(movieSubs[0]) >= 0.90
    
    assert movieSubs[0] != subsEp1[0]

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    test()


