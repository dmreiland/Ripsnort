#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys


dirname = os.path.dirname(os.path.realpath( __file__ ))

sys.path.append(dirname + "/../")
from MediaContent import MediaContent

sys.path.append(dirname + "/../../dependancies/")
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
    
        resultsByTitle = self.api.find_by_title(searchWord)
        
        filteredByTitle = []
        
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
                
            cmp = searchWord.lower().replace('-','').replace(',','').replace(':','').replace(' ','')
            
            if cmp.startswith('the'):
                cmp = cmp[len('the'):len(cmp)]
            
            if title == cmp:
                filteredByTitle.append(result)
        
        #filter by year if applicable
        if year is not None:
            filteredByTitle = filter(lambda x: int(x['year']) == year, resultsByTitle)
        
        mediaList = []
        
        for result in filteredByTitle:
            mediaobj = MediaContent()
            mediaobj.title = result['title'].strip()
            mediaobj.production_year = int(result['year'])
            mediaobj.unique_id = result['imdb_id'].strip()
            mediaobj.scrape_source = 'IMDb'
            
            #fetch detailed response and populate other fields
            resDetail = self.api.find_movie_by_id(mediaobj.unique_id)
            
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
            elif resDetail.type == 'feature':
                mediaobj.content_type = 'movie'
            
            if mediaobj.content_type is not None:
                mediaList.append(mediaobj)
        
        return mediaList

if __name__ == "__main__":
    m = IMDb()
    #find movie
    
    assert len(m.findMovie('The Ant Bully')) == 1
    assert len(m.findMovie('Ant Bully')) == 1

    assert m.findMovie('The Ant Bully')[0].production_year == 2006
    assert m.findMovie('Ant Bully')[0].production_year == 2006

    assert len(m.findMovie('The Toy Story 3')) == 1
    assert len(m.findMovie('Toy Story 3')) == 1

    assert m.findMovie('Toy Story 3')[0].production_year == 2010
    assert len(m.findMovie('Die Hard',1988)) == 1
    assert len(m.findTVShow('The Brittas Empire')) == 1
    assert len(m.findTVShow('Brittas Empire')) == 1

    assert len(m.findMovie('The X-Files')) == 1
    assert len(m.findMovie('X-Files')) == 1

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
