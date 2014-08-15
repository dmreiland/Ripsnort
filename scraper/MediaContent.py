#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging


class MediaContent(object):
    def __init__(self):
        self.content_type = ''
        self.production_year = -1
        self.title = ''
        self.durationS = []
        self.scraper_source = ''
        self.scraper_data = None
        self.unique_id = None
        self.photos_urls = []
        self.poster_urls = []
        self.plot_outline = ''
        self.genres = []
        self.public_url = ''

    def __repr__(self):
        retStr = "<MediaContent "
        retStr += "content: " + self.content_type + ", "
        retStr += "year: " + str(self.production_year) + ", "
        retStr += "title: " + self.title.encode('ascii','replace')
        retStr += ">"

    def __eq__(self,cmp):
        titleMatch = self.title == cmp.title
        yearMatch = self.production_year == cmp.production_year
        return titleMatch and yearMatch
        
    def __ne__(self,cmp):
        return not self.__eq__(cmp)        
    
        
        return retStr


class MovieMedia(MediaContent):
    def __init__(self):
        super(MovieMedia,self).__init__()
        self.content_type = 'movie'

    def __repr__(self):
        retStr = "<MovieMedia "
        retStr += "year: " + str(self.production_year) + ", "
        retStr += "title: " + self.title.encode('ascii','replace')
        retStr += ">"
        
        return retStr


class TVShowMedia(MediaContent):    
    def __init__(self):
        super(TVShowMedia,self).__init__()
        self.content_type = 'tvshow'
        self.number_of_episodes = 0
        self.number_of_seasons = 0

    def __repr__(self):
        retStr = "<TVShowMedia "
        retStr += "number_episodes: " + str(self.number_of_episodes) + ", "
        retStr += "number_seasons" + str(self.number_of_seasons) + ", "
        retStr += "title: " + self.title.encode('ascii','replace')
        retStr += ">"
        
        return retStr


class TVEpisodeMedia(MediaContent):    
    def __init__(self):
        super(TVEpisodeMedia,self).__init__()
        self.content_type = 'tvepisode'
        self.episode_number = None
        self.episode_title = None
        self.season_number = None

    def __repr__(self):
        retStr = "<TVEpisodeMedia "
        retStr += "episode: " + self.content_type + "(" + str(self.episode_number) + "),"
        retStr += "season: " + str(self.season_number) + "),"
        retStr += "year: " + str(self.production_year) + ", "
        retStr += "title: " + self.title.encode('ascii','replace')
        retStr += ">"
        
        return retStr


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    movie = MovieMedia()
    tvshow = TVEpisodeMedia()
    tvep = TVEpisodeMedia()
