#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import re
import logging


from MediaContent import MediaContent

dirname = os.path.dirname(os.path.realpath( __file__ ))


sys.path.append(os.path.join(dirname,"..","utils"))
import objectcache


sys.path.append(os.path.join(dirname,"opensubtitles"))
import opensubtitles


sys.path.append(os.path.join(dirname,"..","dependancies"))
import requests


REGEX_SEASON_MATCH = r'(?i)(?:season|series|s)[_| ]?(\d{1,2})'


class MediaScraper:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MediaScraper, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        dirname = os.path.dirname(os.path.realpath( __file__ ))
        
        scraperType = 'imdb'

        if scraperType.lower() == 'imdb':
            sys.path.append(dirname + "/imdb")
            import scraper_imdb
            self.api = scraper_imdb.IMDb()
            
        logging.debug('Initialized with api: ' + str(self.api))
        
    def __repr__(self):
        return "<MediaScraper type:" +str(self.api)+ ">"

    def findMovie(self,movie,year=None):
        movie = movie.strip()
        
        if year is None:
            year = MediaScraper._extractYearFromName(movie)
            movie = MediaScraper._removeYearFromName(movie)

        results = objectcache.searchCache('MediaScraper_Movie',movie)

        if results == None:
            results = []

            for searchWord in MediaScraper._searchCandidatesFromName(movie):
                newResults = self.api.findMovie(searchWord,year)
                
                if newResults:
                    results += newResults

            objectcache.saveObject('MediaScraper_Movie',movie,results)

        if len(results) == 0:
            logging.debug('No results found for ' + movie + ', searching for acronyms')

            acronyms = MediaScraper._acronymsFromNameWithType(movie,'movie')

            logging.debug('Found acronyms: ' + str(acronyms))

            if len(acronyms) == 1:
                results = self.api.findMovie(acronyms[0],year)

        logging.debug('Returning Movies: ' + str(results))
        
        return results

    def findTVShow(self,tvshow,year=None):

        tvshow = tvshow.strip()
        
        seasonNumber = MediaScraper._extractSeasonNumberFromName(tvshow)
        
        tvshow = MediaScraper._removeSeasonFromName(tvshow)
        
        #look for a ' '/'_' followed by 'd'/'disc'/'disk' followed by a number and remove
        tvshow = re.sub(r'(?i)[_ ](d|disc|disk)[_| ]?\d{1,2}','',tvshow)
        
        tvshow = tvshow.strip()

        if tvshow[-1] == '-':
            tvshow = tvshow[0:len(tvshow)-1]
            tvshow = tvshow.strip()
        
        if year is None:
            year = MediaScraper._extractYearFromName(tvshow)
            tvshow = MediaScraper._removeYearFromName(tvshow)

        results = objectcache.searchCache('MediaScraper_TVShow',tvshow)

        if results == None:
            results = self.api.findTVShow(tvshow,seasonNumber,year)
            objectcache.saveObject('MediaScraper_TVShow',tvshow,results)

        if len(results) == 0:
            logging.info('No results found for ' + tvshow + ', searching for acronyms')

            acronyms = MediaScraper._acronymsFromNameWithType(tvshow,'tvshow')

            logging.debug('Found acronyms: ' + str(acronyms))

            if len(acronyms) == 1:
                results = self.api.findTVShow(acronyms[0],seasonNumber,year)
        
        logging.debug('Returning TV shows: ' + str(results))
        
        return results

    def findTVEpisode(self,mediaObject,seasonNumber,episodeNumber):

        searchKey = mediaObject.title + '_S' + str(seasonNumber) + '_E' + str(episodeNumber)
        
        results = objectcache.searchCache('MediaScraper_TVEpisode',searchKey)
        
        if results == None or len(results) == 0:
            results = self.api.findTVEpisode(mediaObject,seasonNumber,episodeNumber)
            objectcache.saveObject('MediaScraper_TVEpisode',searchKey,results)
        
        return results

    def findTVEpisodesForSeason(self,mediaObject,seasonNumber):

        searchKey = mediaObject.title + '_S' + str(seasonNumber)
        
        results = objectcache.searchCache('MediaScraper_TVSeason',searchKey)
        
        if results == None or len(results) == 0:
            results = self.api.findTVEpisodesForSeason(mediaObject,seasonNumber)
            objectcache.saveObject('MediaScraper_TVSeason',searchKey,results)
        
        if results:
            results.sort(key=lambda x: float(x.episode_number))

        return results

    def findTVEpisodesForShow(self,mediaObject):

        searchKey = mediaObject.unique_id
        
        results = objectcache.searchCache('MediaScraper_TVShow',searchKey)
        
        if results == None or len(results) == 0:
            results=[]
            seasonNumber=1
            keepSearching=True

            while keepSearching:
                try:
                    resultsAppend = self.api.findTVEpisodesForSeason(mediaObject,seasonNumber)
                except Exception, e:
                    logging.error('Failed to get episodes for ' + str(mediaObject) + ' season ' + str(seasonNumber) + ' error: ' + str(e))
                    resultsAppend = []

                if len(resultsAppend) == 0:
                    keepSearching = False
                else:
                    results += resultsAppend
                    seasonNumber += 1
                    
                import time
                time.sleep(5)

            if len(results) > 0:
                objectcache.saveObject('MediaScraper_TVShow',searchKey,results)
        
        if results:
            results.sort(key=lambda x: float((x.season_number*999) + x.episode_number))
        
        return results

    def findContent(self,searchword,contentType,targetDurationS=None,durationTolerance=0.3):
        contentReturn = []
        
        contentType = contentType.replace(' ','').lower().strip()
        
        if contentType == 'movie':
            contentReturn = self.findMovie(searchword)
        
        elif contentType == 'tvshow':
            contentReturn = self.findTVShow(searchword)

        elif contentType == 'tvepisode':
            contentReturn = self.findTVEpisode(searchword)

        else:
            logging.warn('Unknown content type:' + contentType + ', searching for all types')
            contentReturn = []
            
            contentMovie = self.findContent(searchword,'movie',targetDurationS,durationTolerance)
            
            if contentMovie:
                contentReturn += contentMovie

            contentTVShow = self.findContent(searchword,'tvshow',targetDurationS,durationTolerance)
            
            if contentTVShow:
                contentReturn += contentTVShow 
        
        '''If we have to filter on the duration and the results are present use the MediaContent method hasDurationBetweenMaxMin to filter'''
        if targetDurationS is not None and contentReturn is not None:
            maxTargetDurationS = targetDurationS + ( targetDurationS * durationTolerance )
            minTargetDurationS = targetDurationS - ( targetDurationS * durationTolerance )
            contentReturn = filter(lambda x: x.hasDurationBetweenMaxMin(maxTargetDurationS,minTargetDurationS), contentReturn)
        
        return contentReturn
    
    @staticmethod
    def _searchCandidatesFromName(name):
        searchCandidates = []
        searchCandidates.append(name)
        
        if '-' in name:
            newName = name.replace('-',' ')
            newName = newName.replace('\s{1,}',' ')
            
            if len(newName) != len(name):
                searchCandidates.append(newName)

            newNameTheRemoved = re.sub(r'(?i)the\ movie','',newName)
            newNameTheRemoved = re.sub(r'(?i)\ de movie','',newNameTheRemoved)
            
            if len(newNameTheRemoved) != len(name):
                searchCandidates.append(newNameTheRemoved)
            
            newNameYearRemoved = re.sub(r'(?i)\d{4}',' ',newName)
            newNameYearRemoved = re.sub(r'\s{1,}',' ',newName)
            
            if len(newNameYearRemoved) != len(name):
                searchCandidates.append(newNameYearRemoved)
            
        return searchCandidates

    @staticmethod
    def _extractYearFromName(name):
        yearReturn = None

        matchGroups = re.findall(r'(\b\d{4}\b)',name)
        
        import datetime
        currentYear = datetime.date.today().year
        
        for yearFound in matchGroups:
            if int(yearFound) > 1900 and int(yearFound) < (currentYear+1):
                if yearReturn is not None:
                    #we already have a candidate. Can't be sure about either so back out
                    yearReturn = None
                    break
                else:
                    yearReturn = int(yearFound)
                    
        return yearReturn

    @staticmethod
    def _removeYearFromName(name):
        nameReturn = name
        
        year = MediaScraper._extractYearFromName(name)
        
        if year is not None:
            nameReturn = nameReturn.replace(str(year),'')
            nameReturn = nameReturn.replace('()','')
            nameReturn = nameReturn.replace('[]','')
            nameReturn = nameReturn.strip()
        
        return nameReturn

    @staticmethod
    def _extractSeasonNumberFromName(name):
        seasonReturn = None

        matchGroups = re.findall(REGEX_SEASON_MATCH,name)
        
        if len(matchGroups) == 1:
            seasonReturn = int(matchGroups[0])

        return seasonReturn
        
    @staticmethod
    def _removeSeasonFromName(name):
        nameReturn = re.sub(REGEX_SEASON_MATCH,'',name)
        return nameReturn
        
    @staticmethod
    def _acronymsFromNameWithType(name,contentType):
        import urllib
    
        logging.info('Started search for ' + name + ' contentType ' + contentType)

        url = 'http://www.acronymfinder.com/Slang/'+ urllib.quote_plus(name) +'.html'
        
        logging.debug('Fetching url ' + url)
        
        req = requests.get(url)
        response = str( req.text.encode('ascii','replace') )
        
        logging.debug('Response:\n-----------------------\n' + response + '\n-----------------------\n')

        candidates = []

        multipleEntrySearchWord = name + ' stands for,'
        singleEntrySearchWord = name + ' stands for '

        if singleEntrySearchWord.lower() in response.lower():
            logging.debug('Single match found')

            startSearchWord = name + ' stands for '
            startSearchIdx = response.find(startSearchWord) + len(startSearchWord)
            endSearchWord = '. '
            endSearchIdx = response.find(endSearchWord) + len(endSearchWord)
            
            results = response[startSearchIdx:endSearchIdx]
            
            candidates.append( results.strip() )
        elif multipleEntrySearchWord.lower() in response.lower():
            logging.debug('Multiple matches found')

            tableStartWord = """<table class="table table-striped result-list">"""
            tableStartIdx = response.find(tableStartWord) + len(tableStartWord)
            tableEndWord = """</table>"""
            tableEndIdx = tableStartIdx + response[tableStartIdx:len(response)].find(tableEndWord)

            resultsSearch = response[tableStartIdx:tableEndIdx]    
            resultsSearch = resultsSearch.split(r'result-list__body__meaning')
        
            #remove first result
            resultsSearch = resultsSearch[1:len(resultsSearch)]

            for result in resultsSearch:
                tableClose = r'</td>'
                tableCloseIdx = result.find(tableClose)

                result = result[2:tableCloseIdx]
            
                if result.startswith('<a href'):
                    result = result[result.find('>')+1:len(result)]
            
                if result.endswith('</a>'):
                    result = result[0:result.find('</a>')]

                candidates.append( result )
        else:
            logging.debug('No matches found')

        candidatesContentTypeNotKnown = []
        
        for candidate in candidates:
             if '(' not in candidate and ')' not in candidate:
                 candidatesContentTypeNotKnown.append(candidate)

        if contentType.lower() == 'movie':
            candidatesA = filter(lambda x: 'movie' in x.lower(), candidates)
            candidatesB = filter(lambda x: 'tv movie' in x.lower(), candidates)
            candidatesC = filter(lambda x: 'feature' in x.lower(), candidates)
            
            candidates = candidatesA + candidatesB + candidatesC

        elif contentType.lower() == 'tvshow':
            candidatesA = filter(lambda x: 'tv show' in x.lower(), candidates)
            candidatesB = filter(lambda x: 'tv series' in x.lower(), candidates)
            
            candidates = candidatesA + candidatesB
        
        for i in range(0,len(candidates)):
            candidate = candidates[i]
            replacement = re.sub('\(.*\).?$','',candidate).strip()
            candidates[i] = replacement
            
        #Add the unlabelled content types too
        candidates += candidatesContentTypeNotKnown
        
        #clean values
        for i in range(0,len(candidates)):
            candidate = candidates[i]

            #If the last value ends with dot, remove it
            if candidate[-1] == '.':
                candidates[i] = candidate[0:-1]

        return candidates


class SubtitleScraper:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SubtitleScraper, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        self.scraper = opensubtitles.OpenSubtitles()
        logging.debug('Initialized SubtitleScraper scraper')
        
    def __repr__(self):
        return "<SubtitleScraper type:" +str(self.api)+ ">"
    
    def subtitlesForMovie(self,movieObject,language='eng'):
        key = str(movieObject.unique_id) + '_' + language + '_' + str(movieObject.scraper_source)

        results = objectcache.searchCache('SubtitleScraper_Movie',key)

        if results == None or len(results) == 0:
            results = self._api().subtitlesForMovie(movieObject,3,language)
            objectcache.saveObject('MediaScraper_Movie',key,results)

        return results

    def subtitlesForTVShow(self,tvshowObject,language='eng'):
        '''Currently no support'''
        return None
        #return self.scraper.subtitlesForTVShow(movieObject)

    def subtitlesForTVEpisode(self,episodeObject,language='eng'):
        key = str(episodeObject.unique_id) + '_' + language + '_' + str(episodeObject.scraper_source)
        
        results = objectcache.searchCache('SubtitleScraper_TVEpisode',key)
        
        if results == None or len(results) == 0:
            results = self._api().subtitlesForMovie(episodeObject,5,language)
            objectcache.saveObject('SubtitleScraper_TVEpisode',key,results)

        return results
        
    def subtitlesForMediaContent(self,mediaObject,language='eng'):
        subs = []
        
        logging.debug('Looking for subtitles language(' + str(language) + ')  for media object: ' + str(mediaObject))

        if mediaObject.content_type == 'movie':
            subs = self.subtitlesForMovie(mediaObject,language)

        elif mediaObject.content_type == 'tvshow':
            logging.error('Unable to download subtitles for tvshow. Must be a single entity')

        elif mediaObject.content_type == 'tvepisode':
            subs = self.subtitlesForTVEpisode(mediaObject,language)

        else:
            logging.error('Unable content type for object: ' + str(mediaObject))
        
        logging.debug('Returning subtitles language(' + str(language) + ') subtitles: ' + str(subs))
        
        return subs
    
    def _api(self):
        return opensubtitles.OpenSubtitles()

def test():
    logging.basicConfig(level=logging.DEBUG)
    
    s = SubtitleScraper()

    m = MediaScraper()
    
    assert m.findMovie('Thunderbirds - De Movie 2004')[0].production_year == 2004
    assert m.findMovie('Thunderbirds 2004')[0].production_year == 2004
    
    tvShow = m.findTVShow('The Brittas Empire')[0]

    assert tvShow.number_of_seasons == 7
    assert tvShow.number_of_episodes == 51
    
    tvEpisodes = m.findTVEpisodesForSeason(tvShow,1)
    
    assert len(tvEpisodes) == 6
    assert tvEpisodes[0].episode_title == 'Laying the Foundations'
    assert tvEpisodes[0].episode_number == 1
    assert tvEpisodes[0].season_number == 1

    #Acronym checker
    assert len(MediaScraper._acronymsFromNameWithType('Snow White And The Huntsman','movie')) == 0
    assert len(MediaScraper._acronymsFromNameWithType('Snow White And The Huntsman Tafe','movie')) == 0

    assert MediaScraper._acronymsFromNameWithType('koth','tvshow')[0] == 'King of the Hill'
    assert MediaScraper._acronymsFromNameWithType('HIMYM','tvshow')[0] == 'How I Met Your Mother'
    assert MediaScraper._acronymsFromNameWithType('baps','movie')[0] == 'Black American Princesses'
    assert MediaScraper._acronymsFromNameWithType('OFOTCN','movie')[0] == 'One Flew Over the Cuckoo\'s Nest'
    assert MediaScraper._acronymsFromNameWithType('WWATCF','movie')[0] == 'Willy Wonka and the Chocolate Factory'
    assert MediaScraper._acronymsFromNameWithType('TGTBATU','movie')[0] == 'The Good, the Bad, and the Ugly'
    assert MediaScraper._acronymsFromNameWithType('AQOTWF','movie')[0] == 'All Quiet on the Western Front'
    assert MediaScraper._acronymsFromNameWithType('MPatHG','movie')[0] == 'Monty Python and the Holy Grail'
    assert MediaScraper._acronymsFromNameWithType('IJATTOD','movie')[0] == 'Indiana Jones and the Temple of Doom'
    assert MediaScraper._acronymsFromNameWithType('HPATSS','movie')[0] == 'Harry Potter and the Sorcerer\'s Stone'
    assert MediaScraper._acronymsFromNameWithType('HJNTIY','movie')[0] == 'He\'s Just Not That Into You'
    assert MediaScraper._acronymsFromNameWithType('THGTTG','movie')[0] == 'The Hitchhiker\'s Guide to the Galaxy'



    assert m.findMovie('The Good, the Bad, and the Ugly')[0].production_year == 1966
    assert m.findMovie('TGTBATU')[0].production_year == 1966

    assert m.findMovie('The Ant Bully')[0].production_year == 2006
    assert MediaScraper._extractYearFromName('Toy Story 3 2017') == None
    assert MediaScraper._extractYearFromName('Toy Story 3') == None
    assert MediaScraper._extractYearFromName('Toy Story 3 1899') == None
    assert MediaScraper._extractYearFromName('Toy Story 3 2010') == 2010
    assert MediaScraper._extractYearFromName('Toy Story 3 2010 2013') == None
    assert MediaScraper._extractYearFromName('Toy Story 3 2010 12') == 2010
    assert MediaScraper._extractYearFromName('Toy Story 3 2010 123') == 2010
    assert MediaScraper._extractYearFromName('Toy Story 3 (2010) 123') == 2010
    assert MediaScraper._removeYearFromName('Toy Story 3') == 'Toy Story 3'
    assert MediaScraper._removeYearFromName('Toy Story 3 (2010)') == 'Toy Story 3'
    assert MediaScraper._removeYearFromName('Toy Story 3 [2010]') == 'Toy Story 3'


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test()

