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

        '''Remove duplicates'''
        if results is not None:
            results = list(set(results))

        logging.debug('Returning movie results(' +str(len(results))+ '): ' + resultsStr)

        return results


    def findTVShow(self,tvshow,season=None,year=None):
        results = self._searchForTitleWithContent(tvshow.strip(),'tvshow',year)

        resultsStr = ''
        for result in results:
            resultsStr += '    - ' + str(result) + '\n'

        '''Remove duplicates'''
        if results is not None:
            results = list(set(results))

        logging.debug('Returning tvshow results(' +str(len(results))+ '): ' + resultsStr)

        return results
    
    def findTVEpisodesForSeason(self,mediaObject,seasonNumber):
        episodes = []
        
        pilotEpisode = self.findTVEpisode(mediaObject,seasonNumber,0)
        
        if pilotEpisode is not None:
            episodes.append(pilotEpisode)

        didFind = True
        episodeNumber = 1
        
        while didFind:
            newEpisode = self.findTVEpisode(mediaObject,seasonNumber,episodeNumber)
            
            if newEpisode is not None:
                episodes.append(newEpisode)
                episodeNumber += 1
            else:
                logging.debug('Searching tv show: ' + str(mediaObject) + ' finished on season: ' + str(seasonNumber) + ' at episode: ' + str(episodeNumber))
                break

        '''Remove duplicates'''
        if episodes is not None:
            episodes = list(set(episodes))

        return episodes

    def findTVEpisode(self,mediaObject,seasonNumber,episodeNumber):
        episodeObject = None

        logging.debug('Fetching episodes for tv show: '  + mediaObject.title)

        self.api.update(mediaObject.scraper_data,'episodes')
        
        if not mediaObject.scraper_data.has_key('episodes'):
            self.api.update(mediaObject.scraper_data,'episodes')

        if not mediaObject.scraper_data.has_key('episodes'):
            logging.error('Repeatedly failed to get episode:' + str(mediaObject) + ' season:' + str(seasonNumber) + ' episode:' + str(episodeNumber))
            return None

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
    
        logging.debug('Started search for ' + searchWord + ' year ' + str(year))
        
        filteredResults = self._imdbFindByTitle(searchWord)

        #filter by year if applicable
        if year is not None:
            filteredResults = filter(lambda x: x.production_year == year, filteredResults)
            logging.debug('Candidates filtered to year: ' + str(year) + ' candidates:' + str(filteredResults))

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

        logging.debug('Returning candidates: ' + str(mediaList))

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
        except Exception as e:
            if retryCount > 0:
                logging.warn('Imdb connection error, retrying in 3 seconds')
                import time
                time.sleep(3.0)
                result = self._imdbFindByID(uniqueId,retryCount-1)
            else:
                logging.error('Failed to fetch imdb object from id: ' + e.strerror)
        
        if result is not None and result.has_key('kind'):
            kind = result['kind'].encode('ascii','replace').replace(' ','').strip()

            if kind == 'movie' or kind == 'videomovie' or kind == 'tvmovie':
                mediaobj = MovieMedia()

            elif kind == 'tvseries':
                self.api.update(result,'episodes')
                mediaobj = TVShowMedia()

            elif kind == 'episode':
                mediaobj = TVEpisodeMedia()

            else:
                logging.debug('Error searching for IMDBId: ' + str(uniqueId) + ' returned bad result: ' + str(result))
                return None
                
            logging.debug('Loaded IMDBId: ' + str(uniqueId) + ' Kind: ' + kind)# + ' Data: ' + str(result.__dict__))

            mediaobj.scraper_source = 'IMDb'
            mediaobj.scraper_data = result

            try:
                mediaobj.title = result['canonical title'].strip()
            except:
                pass
            
            try:
                mediaobj.title = result['title'].strip().encode('ascii','replace')
            except:
                pass

            mediaobj.production_year = None
            try:
                mediaobj.production_year = int(result['year'])
            except:
                pass
            
            mediaobj.unique_id = result.movieID
            mediaobj.public_url = 'http://www.imdb.com/title/tt' + str(mediaobj.unique_id)
            
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
            
            try:
                mediaobj.popularity = result['votes']
            except:
                pass
                
            try:
                seasons = mediaobj.scraper_data['episodes']
                mediaobj.number_of_seasons = len( seasons.keys() )
                logging.debug('Season count ' + str(mediaobj.number_seasons) + ' data:' + str(seasons))
            except:
                pass
                
            try:
                number_of_episodes = 0
                
                seasons = mediaobj.scraper_data['episodes']

                for season in seasons:
                    episodesDict = seasons[season]
                    logging.debug('Episode keys: ' + str(episodesDict.keys()))
                    number_of_episodes += len(episodesDict.keys())

                mediaobj.number_of_episodes = number_of_episodes
            except:
                pass
            
            try:
                mediaobj.season_number = result['season']
            except:
                pass

            try:
                mediaobj.episode_number = result['episode']
            except:
                pass

            try:
                mediaobj.title = result['episode of']['title'].encode('ascii','replace')
                mediaobj.episode_title = result['title'].encode('ascii','replace')
            except:
                pass

        logging.debug('Returning result for id:' + str(uniqueId) + ', ' + str(mediaobj))
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

    tvShow = m.findTVShow('Brittas Empire')[0]
    logging.debug('Testing tv show: ' + str(tvShow))

    assert tvShow.number_of_seasons == 7
    assert tvShow.number_of_episodes == 51
    
    tvEpisodes = m.findTVEpisodesForSeason(tvShow,1)
    
    assert len(tvEpisodes) == 6
    print('Testing episode: ' + str(tvEpisodes[0]))
    
    print('Testing episode: ' + str(tvEpisodes[0].title))
    assert tvEpisodes[0].unique_id == '0532366'
    assert tvEpisodes[0].title == 'The Brittas Empire'
    assert tvEpisodes[0].episode_title == 'Laying the Foundations'
    assert tvEpisodes[0].episode_number == 1
    assert tvEpisodes[0].season_number == 1

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
    logging.basicConfig(level=logging.INFO)
    test()

