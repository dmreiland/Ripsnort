#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import logging


dirname = os.path.dirname(os.path.realpath( __file__ ))


class SubtitleSearch(object):
    def __init__(self):
        print 'Hello'
        
    def searchTV(self,imdbShowId,seasonNumber,episodeNumber):
        imdbShowId = str(int(imdbShowId.replace('tt','')))
        sublisting_url = 'http://www.opensubtitles.org/en/ssearch/sublanguageid-eng/imdbid-' + imdbShowId
        print sublisting_url
        return []



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    s = SubtitleSearch()
    s.searchTV('tt0903747',1,1)


