#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import logging


dirname = os.path.dirname(os.path.realpath( __file__ ))

sys.path.append(os.path.join(dirname,".."))
from MediaContent import MediaContent

sys.path.append(os.path.join(dirname,"..","..","dependancies"))
import imdbpie


class IMDb:
    def __init__(self):
        self.api = imdbpie.Imdb()

    def findMovie(self,movie,year=None):
        results = self._findMovieAndTV(movie.strip(),year)
        results = filter(lambda x: x.content_type == 'movie', results)
        return results

    def findTVShow(self,tvshow,season=None,year=None):
        results = self._findMovieAndTV(tvshow.strip(),year)
        results = filter(lambda x: x.content_type == 'tvshow', results)
        return results
        
    def _findMovieAndTV(self,searchWord,year=None):
        #if searchWord starts with 'the' remove it before searching
        if searchWord.lower().startswith('the'):
            searchWord = searchWord[len('the'):len(searchWord)].strip()
    
        logging.info('Started search for ' + searchWord + ' year ' + str(year))
        
        resultsByTitle = self._imdbFindByTitle(searchWord)
        
        filteredByTitle = []
                        
        searchCmp = searchWord.lower()
        searchCmp = searchCmp.replace('-','')
        searchCmp = searchCmp.replace(',','')
        searchCmp = searchCmp.replace(':','')
        searchCmp = searchCmp.replace(' ','')
            
        if searchCmp.startswith('the'):
            searchCmp = searchCmp[len('the'):len(searchCmp)]
            
        logging.debug('Comparing to search word ' + str(searchCmp))

        for result in resultsByTitle:
            title = result['title']
            title = title.lower()
            title = title.replace('-','')
            title = title.replace(':','')
            title = title.replace(',','')
            title = title.replace(' ','')
            
            #remove 'the' prefix
            if title.startswith('the'):
                title = title[len('the'):len(title)]
            
            if title == searchCmp or title.startswith(searchCmp):
                logging.debug('Matched ' + title)
                filteredByTitle.append(result)
                
        logging.info('Candidates matching title: ' + searchWord + ' candidates(' +str(len(filteredByTitle))+ '):' + str(filteredByTitle))
        
        #filter by year if applicable
        if year is not None:
            filteredByTitle = filter(lambda x: int(x['year']) == year, filteredByTitle)

        logging.info('Candidates filtered to year: ' + str(year) + ' candidates(' +str(len(filteredByTitle))+ '):' + str(filteredByTitle))
        
        mediaList = []
        
        for result in filteredByTitle:
            mediaobj = MediaContent()
            mediaobj.title = result['title'].strip()
            mediaobj.production_year = int(result['year'])
            mediaobj.unique_id = result['imdb_id'].strip()
            mediaobj.scrape_source = 'IMDb'
            
            #fetch detailed response and populate other fields
            resDetail = self._imdbFindByID(mediaobj.unique_id)
            
            mediaobj.public_url = 'http://www.imdb.com/title/' + mediaobj.unique_id
            
            if resDetail.runtime is not None:
                mediaobj.durationS = int(resDetail.runtime) * 60

            try:
                for photo in resDetail.__dict__['data']['photos']:
                    mediaobj.photos_urls.append( photo['image']['url'] )
            except:
                pass
            
            try:
                for photo in resDetail.__dict__['data']['photos']:
                    mediaobj.photos_urls.append( photo['image']['url'] )
            except:
                pass
            
            try:
                mediaobj.poster_urls.append( resDetail['trailer_img_url'] )
            except:
                pass
            
            try:
                mediaobj.poster_urls.append( resDetail['poster_url'] )
            except:
                pass
            
            try:
                mediaobj.poster_urls.append( resDetail['cover_url'] )
            except:
                pass

            try:
                mediaobj.poster_urls.append( resDetail.__dict__['data']['image']['url'] )
            except:
                pass
        
            try:
                mediaobj.plot_outline = resDetail.plot_outline
            except:
                pass
                
            try:
                mediaobj.genres = resDetail.__dict__['data']['genres']
            except:
                pass

            if resDetail.type == 'tv_series':
                mediaobj.content_type = 'tvshow'
            elif resDetail.type == 'feature' or resDetail.type == 'video':
                mediaobj.content_type = 'movie'
            
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
        
        logging.info('Returning candidates: ' + str(mediaList))

        return mediaList
        
    def _imdbFindByTitle(self,title,retryCount=5):
        resultsByTitle = []
        
        from requests.exceptions import ConnectionError
        
        try:
            resultsByTitle = self.api.find_by_title(title)
        except ConnectionError as e:
            if retryCount > 0:
                logging.warn('Imdb connection error, retrying in 3 seconds')
                import time
                time.sleep(3.0)
                resultsByTitle = self._imdbFindByTitle(title,retryCount-1)
            else:
                logging.error('Failed to fetch imdb results: ' + e.strerror)
            
        return resultsByTitle
        
    def _imdbFindByID(self,uniqueId,retryCount=5):
        result = None
        
        from requests.exceptions import ConnectionError
        
        try:
            result = self.api.find_movie_by_id(uniqueId)
        except ConnectionError as e:
            if retryCount > 0:
                logging.warn('Imdb connection error, retrying in 3 seconds')
                import time
                time.sleep(3.0)
                result = self._imdbFindByID(uniqueId,retryCount-1)
            else:
                logging.error('Failed to fetch imdb object from id: ' + e.strerror)
            
        return result


def test():
    m = IMDb()
    #find movie
    
    assert len(m.findMovie('The Ant Bully')) == 1
    assert len(m.findMovie('Ant Bully')) == 1

    assert m.findMovie('The Ant Bully')[0].production_year == 2006
    assert m.findMovie('Ant Bully')[0].production_year == 2006

    assert len(m.findMovie('Cloverfield')) == 1
    assert len(m.findMovie('The Cloverfield')) == 1
    assert m.findMovie('The Cloverfield')[0].production_year == 2008

    assert len(m.findMovie('Cloudy with a chance of meatballs 2')) == 1
    assert len(m.findMovie('Die Hard',1988)) == 1
    assert len(m.findMovie('The X-Files I Want to believe')) == 1

    assert len(m.findTVShow('The Brittas Empire')) == 1
    assert len(m.findTVShow('Brittas Empire')) == 1


    #find tvshow
    assert m.findTVShow('The Brittas Empire')[0].production_year == 1991
    assert m.findTVShow('Brittas Empire')[0].production_year == 1991
    assert len(m.findTVShow('The X-Files')) == 1
    assert len(m.findTVShow('X-Files')) == 1
    assert len(m.findTVShow('X Files')) == 1
    assert len(m.findTVShow('X Files')) == 1
    assert len(m.findTVShow('XFiles')) == 1
    assert len(m.findTVShow('XFILES')) == 1

    #test the episode length
    assert m.findTVShow('The X-Files')[0].durationS == 2640
    assert m.findTVShow('X-Files')[0].durationS == 2640

    assert m.findTVShow('The 24')[0].durationS == 2640
    assert m.findTVShow('24')[0].durationS == 2640

    assert m.findTVShow('The Simpsons')[0].durationS == 1320
    assert m.findTVShow('Simpsons')[0].durationS == 1320


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test()

