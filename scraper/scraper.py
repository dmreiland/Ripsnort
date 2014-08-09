#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import re
import logging


from MediaContent import MediaContent


dirname = os.path.dirname(os.path.realpath( __file__ ))


sys.path.append(os.path.join(dirname,"..","dependancies"))
import requests


REGEX_SEASON_MATCH = r'(?i)(?:season|series|s)[_| ]?(\d{1,2})'


class MediaScraper:

    def __init__(self,params):
        dirname = os.path.dirname(os.path.realpath( __file__ ))
        
        scraperType = params['type']

        if scraperType.lower() == 'imdb':
            sys.path.append(dirname + "/imdb")
            import imdb
            self.api = imdb.IMDb()
            
        logging.info('Initialized with api: ' + str(self.api))
        
    def __repr__(self):
        return "<Scraper>"

    def findMovie(self,movie,year=None):
        movie = movie.strip()
        
        if year is None:
            year = MediaScraper._extractYearFromName(movie)
            movie = MediaScraper._removeYearFromName(movie)
            
        results = self.api.findMovie(movie,year)
        
        if len(results) == 0:
            logging.info('No results found for ' + movie + ', searching for acronyms')

            acronyms = MediaScraper._acronymsFromNameWithType(movie,'movie')

            logging.info('Found acronyms: ' + str(acronyms))

            if len(acronyms) == 1:
                results = self.api.findMovie(acronyms[0],year)

        logging.info('Returning Movies: ' + str(results))
        
        return results

    def findTVShow(self,tvshow,year=None):
    
        tvshow = tvshow.strip()
        
        seasonNumber=MediaScraper._extractSeasonNumberFromName(tvshow)
        
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

        results = self.api.findTVShow(tvshow,seasonNumber,year)

        if len(results) == 0:
            logging.info('No results found for ' + tvshow + ', searching for acronyms')

            acronyms = MediaScraper._acronymsFromNameWithType(tvshow,'tvshow')

            logging.info('Found acronyms: ' + str(acronyms))

            if len(acronyms) == 1:
                results = self.api.findTVShow(acronyms[0],seasonNumber,year)
        
        logging.info('Returning TV shows: ' + str(results))
        
        return results
            
        
    def findContent(self,contentType,searchword):
        if contentType.lower().strip() == 'movie':
            return self.findMovie(searchword)
        elif contentType.lower().strip() == 'tvshow':
            return self.findTVShow(searchword)
        else:
            return None
    

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


def test():
    logging.basicConfig(level=logging.DEBUG)

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

    m = MediaScraper({'type':'imdb'})

    assert m.findMovie('TGTBATU')[0].production_year == 1966
    assert m.findMovie('The Good, the Bad, and the Ugly')[0].production_year == 1966

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

