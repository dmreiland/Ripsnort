#!/usr/bin/env python
# -*- coding: utf-8 -*-


class MediaContent:
    def __init__(self):
        self.content_type = None
        self.production_year = -1
        self.title = None
        self.durationS = 0
        self.scrape_source = None
        self.unique_id = None
        self.season_number = None
        self.episode_number = None
        self.episode_title = None
        self.photos_urls = []
        self.poster_urls = []
        self.plot_outline = None
        self.genres = []
        self.public_url = None

        
    def __repr__(self):
        retStr = "<MediaContent "
        retStr += "content: " + self.content_type + ", "
        retStr += "year: " + str(self.production_year) + ", "
        retStr += "title: " + self.title
        retStr += ">"
        
        return retStr
