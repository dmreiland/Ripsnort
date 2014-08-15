#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import logging


dirname = os.path.dirname(os.path.realpath( __file__ ))

sys.path.append(os.path.join(dirname,".."))
from MediaContent import *

sys.path.append(os.path.join(dirname,"..","..","dependancies"))
import imdb


class IMDb:
    def __init__(self):
        self.api = imdb.IMDb()


    def findMovie(self,movie,year=None):
        results = self._searchForTitleWithContent(movie.strip(),'movie',year)

        resultsStr = ''
        for result in results:
            resultsStr += '    - ' + str(result) + '\n'

        logging.debug('Returning movie results(' +str(len(results))+ '): ' + resultsStr)

        return results


    def findTVShow(self,tvshow,season=None,year=None):
        results = self._searchForTitleWithContent(tvshow.strip(),'tvshow',year)

        resultsStr = ''
        for result in results:
            resultsStr += '    - ' + str(result) + '\n'

        logging.debug('Returning tvshow results(' +str(len(results))+ '): ' + resultsStr)

        return results


    def findTVEpisode(self,mediaObject,seasonNumber,episodeNumber):
        episodeObject = None

        logging.debug('Fetching episodes for tv show: '  + mediaObject.title)

        self.api.update(mediaObject.scraper_data,'episodes')

        seasons = mediaObject.scraper_data['episodes']

        logging.debug('Seasons: '  + str(seasons.keys()))
        
        if seasons.has_key(seasonNumber):
            episodes = seasons[seasonNumber]

            logging.debug('Episodes: '  + str(episodes.keys()))
            
            if episodes.has_key(episodeNumber):
                episode = episodes[episodeNumber]

                imdbId = episode.movieID
                                
                episodeObject = self._imdbFindByID(imdbId)
                #TODO load these from above method
                episodeObject.episode_number = episodeNumber
                episodeObject.season_number = seasonNumber

                logging.debug('Got object: '  + str(episodeObject))
                
        return episodeObject


    def _searchForTitleWithContent(self,searchWord,contentType,year=None):
        #if searchWord starts with 'the' remove it before searching
    
        logging.info('Started search for ' + searchWord + ' year ' + str(year))
        
        filteredResults = self._imdbFindByTitle(searchWord)

        #filter by year if applicable
        if year is not None:
            filteredResults = filter(lambda x: x.production_year == year, filteredResults)
            logging.info('Candidates filtered to year: ' + str(year) + ' candidates:' + str(filteredResults))

        filteredResults = filter(lambda x: x.content_type == contentType, filteredResults)

        mediaList = []
        
        for mediaobj in filteredResults:
            hasContentType = mediaobj.content_type is not None
            hasDuration = mediaobj.durationS  > 0
            isDurationSuitableForContent = True
            
            if mediaobj.content_type == 'movie' and mediaobj.durationS < (60*60):
                isDurationSuitableForContent = False
            
            if hasContentType and hasDuration and isDurationSuitableForContent:
                mediaList.append(mediaobj)
        
        if year == None:
            #remove any candidates that have not yet been released
            from datetime import date
            currentYear = date.today().year
            
            mediaList = filter(lambda x: x.production_year <= currentYear, mediaList)
        
        #remove duplicates
        mediaList = list(set(mediaList))

        logging.info('Returning candidates: ' + str(mediaList))

        return mediaList
        
    def _imdbFindByTitle(self,title,retryCount=5):
        resultsByTitle = []
        
        from requests.exceptions import ConnectionError
        
        try:
            #Search imdb for the searchword
            for result in self.api.search_movie(title.strip()):
                mediaobj = self._imdbFindByID(result.movieID)
                if mediaobj is not None:
                    resultsByTitle.append( mediaobj )

            #Search imdb for the searchword stripped
            titleSearchStripped = title.lower().replace('-','').replace(',','').replace(':','').strip()

            if titleSearchStripped.lower().startswith('the '):
                titleSearchStripped = titleSearchStripped[len('the '):len(titleSearchStripped)].strip()

            for result in self.api.search_movie(titleSearchStripped):
                mediaobj = self._imdbFindByID(result.movieID)
                if mediaobj is not None:
                    resultsByTitle.append( mediaobj )

        except IOError as e:
            if retryCount > 0:
                logging.warn('Imdb connection error, retrying in 3 seconds')
                import time
                time.sleep(3.0)
                resultsByTitle = self._imdbFindByTitle(title,retryCount-1)
            else:
                logging.error('Failed to fetch imdb results: ' + e.strerror)
            
        return resultsByTitle
        
    def _imdbFindByID(self,uniqueId,retryCount=5):
        mediaobj = None
        
        from requests.exceptions import ConnectionError
        
        result = None
        
        try:
            result = self.api.get_movie(uniqueId)
            self.api.update(result)
            logging.debug('Result for id:' + str(uniqueId) + ', ' + str(result))
        except ConnectionError as e:
            if retryCount > 0:
                logging.warn('Imdb connection error, retrying in 3 seconds')
                import time
                time.sleep(3.0)
                result = self._imdbFindByID(uniqueId,retryCount-1)
            else:
                logging.error('Failed to fetch imdb object from id: ' + e.strerror)
        
        if result is not None:
            if result['kind'] == 'movie' or result['kind'] == 'video movie' or result['kind'] == 'tv movie':
                mediaobj = MovieMedia()

            elif result['kind'] == 'tv series':
                mediaobj = TVShowMedia()

            elif result['kind'] == 'episode':
                mediaobj = TVEpisodeMedia()
            else:
                return None

            mediaobj.scraper_source = 'IMDb'
            mediaobj.scraper_data = result

            try:
                mediaobj.title = result['canonical title'].strip()
            except:
                pass
            
            try:
                mediaobj.title = result['title'].strip()
            except:
                pass

            mediaobj.production_year = None
            try:
                mediaobj.production_year = int(result['year'])
            except:
                pass
            
            mediaobj.unique_id = result.movieID
            mediaobj.public_url = 'http://www.imdb.com/title/tt' + str(mediaobj.unique_id)
            
            print result.keys()
            
            try:
                for runtime in result['runtimes']:
                    mediaobj.durationS.append( int(runtime) * 60 )
            except:
                pass
            
            mediaobj.public_url = 'http://www.imdb.com/title/' + mediaobj.unique_id
            
            try:
                mediaobj.poster_urls.append( resDetail['full-size cover url'] )
            except:
                pass
            
            try:
                mediaobj.poster_urls.append( result['cover_url'] )
            except:
                pass
        
            try:
                mediaobj.plot_outline = result['plot outline']
            except:
                pass

            try:
                mediaobj.genres = result['genres']
            except:
                pass
        
        logging.debug('Returning result for id:' + str(uniqueId) + ', ' + str(result))
        return mediaobj


def test():
    m = IMDb()

    #find movie

    assert len(m.findMovie('Dawn Of The Dead',1978)) == 1

    assert m.findMovie('The Good, the Bad, and the Ugly')[0].title == 'Il buono, il brutto, il cattivo.'
    assert m.findMovie('The Good, the Bad, and the Ugly')[0].production_year == 1966
    assert m.findMovie('Good Bad Ugly')[0].production_year == 1966

    assert len(m.findMovie('The Cloverfield')) == len(m.findMovie('Cloverfield'))
    assert m.findMovie('The Cloverfield')[0].production_year == 2008
    
    assert len(m.findMovie('The Ant Bully')) == 1
    assert len(m.findMovie('Ant Bully')) == 1

    assert m.findMovie('The Ant Bully')[0].production_year == 2006
    assert m.findMovie('Ant Bully')[0].production_year == 2006


    assert len(m.findMovie('Cloudy with a chance of meatballs 2')) == 1
    assert len(m.findMovie('Die Hard',1988)) == 1
    assert len(m.findMovie('The X-Files I Want to believe')) == 1

    assert len(m.findTVShow('The Brittas Empire')) == 1
    assert len(m.findTVShow('Brittas Empire')) == 1

    #test the episode length
    xFilesTVShow = m.findTVShow('The X-Files')[0]
    assert xFilesTVShow.durationS == 2640
    assert m.findTVShow('X-Files')[0].durationS == 2640
    
    xFilesEpisode1_4 = m.findTVEpisode(xFilesTVShow,1,4)
    
    assert xFilesEpisode1_4.title == 'The Jersey Devil'
    assert xFilesEpisode1_4.unique_id == '0751229'
    assert xFilesEpisode1_4.episode_number == 4
    assert xFilesEpisode1_4.season_number == 1

    #find tvshow
    assert m.findTVShow('The Brittas Empire')[0].production_year == 1991
    assert m.findTVShow('Brittas Empire')[0].production_year == 1991
    assert len(m.findTVShow('The X-Files')) == 1
    assert len(m.findTVShow('X-Files')) == 1
    assert len(m.findTVShow('X Files')) == 1
    assert len(m.findTVShow('X Files')) == 1
    assert len(m.findTVShow('XFiles')) == 1
    assert len(m.findTVShow('XFILES')) == 1

    assert m.findTVShow('The 24')[0].durationS == 2640
    assert m.findTVShow('24')[0].durationS == 2640

    assert m.findTVShow('The Simpsons')[0].durationS == 1320
    assert m.findTVShow('Simpsons')[0].durationS == 1320


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test()

