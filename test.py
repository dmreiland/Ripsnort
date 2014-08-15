#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import logging


dirname = os.path.dirname(os.path.realpath( __file__ ))


import disc_track
import disc_name


sys.path.append( os.path.join(dirname,"notification","audionotify") )
import audionotify

sys.path.append( os.path.join(dirname,"notification","emailsmtp") )
import emailsmtp

sys.path.append( os.path.join(dirname,"notification","localnotify") )
import localnotify

sys.path.append( os.path.join(dirname,"notification","macnotificationcenter") )
import macnotificationcenter

sys.path.append( os.path.join(dirname,"scraper") )
import scraper

sys.path.append( os.path.join(dirname,"scraper","imdb") )
import imdb

sys.path.append( os.path.join(dirname,"scraper","opensubtitles") )
import opensubtitles


if __name__ == "__main__":
    email_source='email@gmail.com'
    email_password='password'
    email_server='smtp.gmail.com'

    logging.basicConfig(level=logging.DEBUG)

    disc_track.test()
    disc_name.test()
    audionotify.test()
    emailsmtp.test(email_source,email_password,email_server)
    localnotify.test()
    scraper.test()
    imdb.test()
    opensubtitles.test()

