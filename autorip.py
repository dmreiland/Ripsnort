#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import shutil
import logging


import disc_drive


dirname = os.path.dirname(os.path.realpath( __file__ ))

sys.path.append( os.path.join(dirname,"ripper") )
import ripper

sys.path.append( os.path.join(dirname,"dependancies") )
import dvdfingerprint

sys.path.append( os.path.join(dirname,"notification" ) )
import notification

sys.path.append( os.path.join(dirname,"scraper" ) )
import scraper


def dictTypeConversion(dictionaryCheck):
    for key in dictionaryCheck:
        val = dictionaryCheck[key]
        if type(val) == type({}):
            val = dictTypeConversion(val)
        elif type(val) == type(''):
            val = val.lower().strip()
            valHasDots = len(val.split('.')) > 1
            
            floatVal = None
            
            try:
                floatVal = float(val)
            except:
                pass

            intVal = None
            
            try:
                intVal = int(val)
            except:
                pass
            
            if val == 'no' or val == 'false' or val == 'off':
                val = False
            elif val == 'yes' or val == 'true' or val == 'on':
                val = True
            elif valHasDots and floatVal is not None:
                val = floatVal
            elif intVal is not None:
                val = intVal
            elif val == 'none' or val == 'nil' or val == 'null':
                val = None
            else:
                #undo val changes
                val = dictionaryCheck[key]

        else:
            #value is not dict or string
            pass
            
        dictionaryCheck[key] = val
        
    return dictionaryCheck

def loadConfigFile(configFile):
    import ConfigParser
    
    logging.info('Loading file: ' + str(configFile))

    config = ConfigParser.RawConfigParser()
    config.read(configFile)
    
    d = dict(config._sections)
    for k in d:
        d[k] = dict(config._defaults, **d[k])
        d[k].pop('__name__', None)
    
    logging.info('Loaded dictionary: ' + str(d))

    return dictTypeConversion(d)

def contentTypeForTracksAndName(tracks,name,config):
    if len(name) == 0:
        return None
            
    logging.debug('Determining content type for tracks: ' + str(tracks) + ' track name: ' + str(name))

    contentType = None
    
    hasSeasonInName = 'season' in name.lower()
    hasSeriesInName = 'series' in name.lower()
    hasDiscInName = 'disc' in name.lower()
    hasDiskInName = 'disk' in name.lower()
    
    if ( hasSeasonInName or hasSeriesInName ) and ( hasDiscInName or hasDiskInName ):
        #nameIndicatesTVShow
        contentType = 'tvshow'
    else:
        #check the track lengths
        minDurationMovie = int(config['ripper']['movie_min_length_seconds'])
        maxDurationMovie = int(config['ripper']['movie_max_length_seconds'])

        minDurationTV = int(config['ripper']['tvepisode_min_length_seconds'])
        maxDurationTV = int(config['ripper']['tvepisode_max_length_seconds'])
        
        tracksMovies = tracksUnderDuration(maxDurationMovie, tracksOverDuration(minDurationMovie,tracks))

        tracksTV = tracksUnderDuration(maxDurationTV, tracksOverDuration(minDurationTV,tracks))
        
        if len(tracksTV) > 0 and len(tracksMovies) == 0:
            contentType = 'tvshow'
        elif len(tracksMovies) > 0 and len(tracksTV) == 0:
            contentType = 'movie'
        else:
            #we have both movie and video candidates
            
            #check the durations of the tv tracks, if they are similar in length, then we can assume they are episodes
            
            durations = []
            durationTotalS = 0
            
            for track in tracksTV:
                durations.append( track.durationS )
                durationTotalS += track.durationS
            
            durationAverage = durationTotalS / len(durations)
            
            durationsAreCloseToAverage = True
            
            for track in tracksTV:
                if abs(track.durationS / durationAverage) < 0.9 or abs(track.durationS / durationAverage) > 1.1:
                    durationsAreCloseToAverage = False
                    break
            
            logging.debug('Average track duration: ' + str(durationAverage) + ' durationsAreClose: ' + str(durationsAreCloseToAverage))
            
            if durationsAreCloseToAverage:
                contentType = 'tvshow'
            else:
                #durations don't all match, assume its a movie
                contentType = 'movie'
    
    logging.info('Content type for name:' + name + ', tracks:' + str(tracks) + ' = ' + contentType)
    
    return contentType


def tracksOverDuration(durationMin,discTracks):
    tracksRet = []
    
    for track in discTracks:
        if track.durationS >= durationMin:
            tracksRet.append(track)
    
    return tracksRet


def tracksUnderDuration(durationMax,discTracks):
    tracksRet = []
    
    for track in discTracks:
        if track.durationS <= durationMax:
            tracksRet.append(track)
    
    return tracksRet


def outputFileForTrackWithFormat(track,format):
    newFilePath = format
    
    logging.debug('Loading output file format: ' + format + ' for track: ' + track)
    
    import re
    
    newFilePath = newFilePath.replace('{N}',track.title)

    #season matches
    for match in re.findall(r'({[S|s].*?})',newFilePath):
        replacementText = str(track.season_number)
        padMatches = re.findall(r'\.pad\((\d)\)',match)
        
        if len(padMatches) > 0:
            padNum = int(padMatches[0])
            replacementText = str(track.season_number).zfill(padNum)

        newFilePath = newFilePath.replace(match,replacementText)

    #episode matches
    for match in re.findall(r'({[E|e].*?})',newFilePath):
        replacementText = str(track.episode_number)
        padMatches = re.findall(r'\.pad\((\d)\)',match)
        
        if len(padMatches) > 0:
            padNum = int(padMatches[0])
            replacementText = str(track.episode_number).zfill(padNum)

        newFilePath = newFilePath.replace(match,replacementText)

    newFilePath = newFilePath.replace('{T}',track.episode_title)

    newFilePath = newFilePath.replace('{Y}',str(track.production_year))

    assert '{' not in newFilePath
    assert '}' not in newFilePath
    
    return newFilePath


if __name__ == "__main__":
    
    if len(sys.argv) <= 1:
        print 'Call with drive i.e. autorip.py /dev/disk2'
        sys.exit(1)

    discdevice=''

    argsList = sys.argv[1:]
    
    while ( len(argsList) > 0 ):
        discdevice = argsList[0]

        #Remove last argument
        argsList = argsList[1:]
        
    drive = disc_drive.DiscDrive(discdevice)
    
    if drive.isOpen():
       drive.closeTray()
    
    if not drive.isDiscInserted():
        print 'No disc inserted!'
        sys.exit(1)

    else:
        #load config
        config = loadConfigFile(os.path.join(dirname,'settings.ini'))

        #load ripper, scraper and notification
        notify = notification.Notification(config['notification'])
        
        ripper = ripper.Ripper(config['ripper'],discdevice)

        logging.info('Formatted disc name: ' + ripper.formattedName())

        contentType = contentTypeForTracksAndName(ripper.discTracks(),ripper.formattedName(),config)
        
        logging.info('Content type: ' + contentType)

        mediascraper = scraper.MediaScraper(config['scraper'])
        
        mediaobjs = mediascraper.findContent(contentType,ripper.formattedName())
        
        if len(mediaobjs) is not 1:
            alt_name = dvdfingerprint.disc_title(drive.mountedPath())
            mediaobjs = mediascraper.findMovie(alt_name)
    
        ripTracks = []
    
        if contentType == 'movie':
            if config['ripper']['movie_rip_extras'] == True:
                minDuration = 0
                maxDuration = 9999
                ripExtraContent = True
            else:
                minDuration = config['ripper']['movie_min_length_seconds']
                maxDuration = config['ripper']['movie_max_length_seconds']
                ripExtraContent = False
            
            ripPathComplete = config['ripper']['movie_complete_save_path']
            ripPathIncomplete = config['ripper']['movie_incomplete_save_path']

        elif contentType == 'tvshow':
            if config['ripper']['tv_rip_extras'] == True:
                minDuration = 0
                maxDuration = 9999
                ripExtraContent = True
            else:
                minDuration = config['ripper']['tvepisode_min_length_seconds']
                maxDuration = config['ripper']['tvepisode_max_length_seconds']
                ripExtraContent = False

            ripPathComplete = config['ripper']['tv_incomplete_save_path']
            ripPathIncomplete = config['ripper']['tv_incomplete_save_path']
            
        else:
            print 'Unexpected content type ' + str(contentType)
            sys.exit(1)

        ripTracks = tracksUnderDuration(maxDuration, tracksOverDuration(minDuration,ripper.discTracks()))
        
        if ripExtraContent == False and len(mediaobjs) == 1:
            #we don't want the extra content and we have an exact match, Use the duration from the media object to filter out erronous matches
            mediaDurationS = mediaobjs[0].durationS
            logging.info( 'Filtering results to match duration ' + str(mediaDurationS) )
            ripTracks = tracksUnderDuration(mediaDurationS * 1.14, tracksOverDuration(mediaDurationS * 0.86,ripTracks))            


        logging.info( 'Video candidates:' + str(ripTracks) )

        if config['ripper']['backup_disc'] == False and config['ripper']['rip_disc'] == False:
            logging.error( 'No ripping enabled. Not much to do without either rip_disc or backup_disc set to True' )
            sys.exit(1)

        if config['ripper']['backup_disc'] == True:
            logging.info( 'Making disk backup' )

            notify.startedBackingUpDisc(ripper.formattedName())

            ripper.ripDiscBackup( os.path.join(ripPathIncomplete,ripper.formattedName()) )

            notify.finishedBackingUpDisc(ripper.formattedName())

        if config['ripper']['rip_disc'] == True:
            logging.info( 'Ripping disc tracks' )
            
            notify.startedRippingTracks( ripTracks, ripper.formattedName() )
            
            ripper.ripDiscTracks( ripTracks, os.path.join(ripPathIncomplete,ripper.formattedName()) )

            didMove = False
        
            #rename output file only if there is 1-1 match
            if len(mediaobjs) == 1 and len(ripTracks) == 1:
                srcFile = os.path.join(ripPathIncomplete,ripper.formattedName(),ripTracks[0].outputFileName)
                
                if mediaobjs[0].content_type == 'movie':
                    format = config['ripper']['movie_save_format']
                elif mediaobjs[0].content_type == 'tvshow':
                    format = config['ripper']['tv_save_format']
                
                newFileName = outputFileForTrackWithFormat(mediaobjs[0],format)
                newFileExt = ripTracks[0].outputFileName.split('.')[-1]
                dstFile = os.path.join(ripPathComplete,(newFileName+'.'+newFileExt))

                os.rename(srcFile,dstFile)
                shutil.rmtree( os.path.join(ripPathIncomplete,ripper.formattedName()) )
            
                didMove = True
                
            #TODO change notify message to include move location
            
            notify.finishedRippingTracks( ripTracks, ripper.formattedName(), mediaobjs )

        #lastly eject the tray
        drive.openTray()
        
    
    
