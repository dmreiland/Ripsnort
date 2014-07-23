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

    def findTVShow(self,tvshow,year=None):
        results = self._findMovieAndTV(tvshow.strip(),year)
        results = filter(lambda x: x.content_type == 'tvshow', results)
        return results
        
    def _findMovieAndTV(self,searchWord,year=None):
        resultsByTitle = self.api.find_by_title(searchWord)
        
        resultsByTitle = filter(lambda x: x['title'].lower().strip() == searchWord.lower(), resultsByTitle)
        
        if year is not None:
            resultsByTitle = filter(lambda x: int(x['year']) == year, resultsByTitle)
        
        mediaList = []
        
        for result in resultsByTitle:
            mediaobj = MediaContent()
            mediaobj.title = result['title'].strip()
            mediaobj.production_year = int(result['year'])
            mediaobj.unique_id = result['imdb_id'].strip()
            mediaobj.scrape_source = 'IMDb'
            
            #fetch detailed response and populate other fields
            resDetail = self.api.find_movie_by_id(mediaobj.unique_id)

            mediaobj.durationS = resDetail.runtime * 60
            
            if resDetail.type == 'tv_series':
                mediaobj.content_type = 'tvshow'
            elif resDetail.type == 'feature':
                mediaobj.content_type = 'movie'
            
            mediaList.append(mediaobj)
        
        return mediaList

if __name__ == "__main__":
    m = IMDb()
    assert len(m.findMovie('The Ant Bully')) == 1
    assert m.findMovie('The Ant Bully')[0].production_year == 2006
    assert len(m.findMovie('Toy Story 3')) == 1
    assert m.findMovie('Toy Story 3')[0].production_year == 2010
    assert len(m.findMovie('Die Hard',1988)) == 1
    assert len(m.findTVShow('The Brittas Empire')) == 1
    assert m.findTVShow('The Brittas Empire')[0].production_year == 1991
    assert len(m.findTVShow('The X-Files')) == 1
    assert len(m.findMovie('The X-Files')) == 0
