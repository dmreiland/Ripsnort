#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import logging


dirname = os.path.dirname(os.path.realpath( __file__ ))


import disc_track


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


if __name__ == "__main__":
    email_source='ripsnort.auto@gmail.com'
    email_password='Ryan1234'
    email_server='smtp.gmail.com'

    logging.basicConfig(level=logging.DEBUG)

    disc_track.test()
    audionotify.test()
    emailsmtp.test(email_source,email_password,email_server)
    localnotify.test()
    scraper.test()
    imdb.test()

