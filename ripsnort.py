#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import os
import sys
import shutil
import logging


import disc_drive
import disc_name
import disc_track
import apppath


dirname = os.path.dirname(os.path.realpath( __file__ ))

sys.path.append( os.path.join(dirname,"ripper") )
import ripper

sys.path.append( os.path.join(dirname,"dependancies") )
import dvdfingerprint

sys.path.append( os.path.join(dirname,"notification" ) )
import notification

sys.path.append( os.path.join(dirname,"scraper" ) )
import scraper

sys.path.append( os.path.join(dirname,"utils" ) )
import inireader


def sanitizeFilePath(filePathString):
    import string
    valid_chars = "-_.()/\\ %s%s" % (string.ascii_letters, string.digits)
    newPath = ''.join(c for c in filePathString if c in valid_chars)
    return newPath


def isInternetConnectionAvailable():
    try:
        '''Google IP'''
        import urllib2
        response=urllib2.urlopen('http://74.125.228.100',timeout=1)
        return True
    except urllib2.URLError as err:
        return False
    
def doesFolderContainVideoFiles(folderDir):
    doesContentVideoFiles = False
    
    for fileName in os.listdir(folderDir):
        try:
            ext = fileName.split('.')[-1]
            if ext == 'mkv' or ext == 'mp4' or ext == 'avi' or ext == 'm2ts' or ext == 'ts':
                doesContentVideoFiles = True
        except:
            pass
    
    return doesContentVideoFiles


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
    
    logging.debug('Content type for name:' + name + ', tracks:' + str(tracks) + ' = ' + contentType)
    
    return contentType


def outputFileForTrackWithFormat(mediaObj,fileformat):
    newFilePath = fileformat
    
    logging.debug('Loading output file format: ' + str(fileformat) + ' for track: ' + str(mediaObj))
    
    newFilePath = newFilePath.replace('{N}',mediaObj.title)

    #season matches
    for match in re.findall(r'({[S|s].*?})',newFilePath):
        replacementText = ''
        
        seasonNumber = ''
        
        if mediaObj.season_number is not None:
            seasonNumber = str(mediaObj.season_number)
            
        replacementText = str(seasonNumber)
        
        padMatches = re.findall(r'\.pad\((\d)\)',match)
        
        if len(padMatches) > 0:
            padNum = int(padMatches[0])
            replacementText = str(seasonNumber).zfill(padNum)

        newFilePath = newFilePath.replace(match,replacementText)

    #episode matches
    for match in re.findall(r'({[E|e].*?})',newFilePath):
        replacementText = ''
        
        episodeNumber = ''
        
        if mediaObj.episode_number is not None:
            episodeNumber = str(mediaObj.episode_number)
            
        replacementText = episodeNumber

        padMatches = re.findall(r'\.pad\((\d)\)',match)
        
        if len(padMatches) > 0:
            padNum = int(padMatches[0])
            replacementText = str(episodeNumber).zfill(padNum)

        newFilePath = newFilePath.replace(match,replacementText)
        
    episodeTitle = ''
    
    if mediaObj.episode_title is not None:
        episodeTitle = mediaObj.episode_title

    newFilePath = newFilePath.replace('{T}',episodeTitle)

    productionYear = ''
    
    if mediaObj.production_year is not None:
        productionYear = mediaObj.production_year

    newFilePath = newFilePath.replace('{Y}',str(productionYear))

    assert '{' not in newFilePath
    assert '}' not in newFilePath
    
    return newFilePath


def getMediaObjectForLocalVideoTrack(trackPath,discname,contentType):
    mediaObjReturn = None
    mediaObjMatchRatio = 0.0

    localVideoTrack = disc_track.LocalTrackMkv(trackPath)
    logging.debug('Opened video file: ' + trackPath + ' track:' + str(localVideoTrack) + ' targetDuration:' + str(localVideoTrack.durationS))

    candidateList = scraper.MediaScraper().findContent(discname.title,contentType,targetDurationS=localVideoTrack.durationS,durationTolerance=0.14)

    '''sort by least popular and then reverse'''
    candidateList.sort(key=lambda x: float(x.popularity))
    candidateList.reverse()

    logging.info('Candidate media objects: ' + str(candidateList))

    for candidate in candidateList:
        if candidate is None:
            continue
        
        mediaObjsCompare = [candidate]
        
        if contentType == 'tvshow':
            mediaObjsCompare = []
            for mediaObj in candidateList:
                seasonNumber = discname.season
                logging.debug('Searching for episodes from season ' + str(seasonNumber) + ' show:' + str(mediaObj))
                tvMediaObjs = scraper.MediaScraper().findTVEpisodesForSeason(mediaObj,seasonNumber)
                mediaObjsCompare += tvMediaObjs
                import time
                time.sleep(1)
            
            if len(mediaObjsCompare) == 0:
                continue

            '''If the average dvd contains 9000 seconds of content then if we know the disc number we should be able to estimate
               the best place to start searching for episodes by multiplying the averageDurationDiscS by the number of discs'''
            averageDurationDiscS = 9000 - 1000 #subtract 1000 so we undershoot rather than overshoot over target start point
            durationOffset = discname.discNumber * averageDurationDiscS
            episodeLength = mediaObjsCompare[0].shortestDuration()
            episodeIndexOffset = durationOffset / episodeLength
            mediaObjsCompare = mediaObjsCompare[episodeIndexOffset:len(mediaObjsCompare)] + mediaObjsCompare[0:episodeIndexOffset]
            logging.debug('Set start offset to search: ' + str(episodeIndexOffset))
                
        for mediaObj in mediaObjsCompare:
            subsRemote = scraper.SubtitleScraper().subtitlesForMediaContent(mediaObj)
            
            if len(subsRemote) == 0:
                logging.error('No subs to compare')
                continue

            subCmp = subsRemote[0]

            logging.debug('Testing for media object: ' + str(mediaObj) + ', found ' + str(len(subsRemote)) + ' subtitles')
            
            for subLocal in localVideoTrack.subtitles:
                newRatio = subLocal.matchRatioWithCaption(subCmp)

                logging.debug('Got match ratio: ' + str(newRatio) + ' for media: ' + str(mediaObj))
                
                if newRatio > mediaObjMatchRatio and newRatio > 0.70:
                    mediaObjMatchRatio = newRatio
                    mediaObjReturn = mediaObj

                if newRatio > 0.90:
                    logging.debug('Ending search prematurely, result found with confidence(' +str(newRatio)+ ')')
                    return mediaObjReturn

    logging.debug('Best match ratio:' + str(mediaObjMatchRatio) + ' for mediafile: ' +str(mediaObjReturn))
    return mediaObjReturn 



def usage():
    return '''
usage: [-v] disc
    -h --help  Prints this usage information.
    -q --quiet         print nothing to stdout
    -v --verbose       print extra information

example: ./autorip.py -v /dev/disk2
'''


if __name__ == "__main__":
    
    if len(sys.argv) <= 1:
        logging.error('No disc argument')
        print usage()
        sys.exit(1)
        
    if isInternetConnectionAvailable() == False:
        print '''No internet connection found. Ripsnort requires internet access to run'''
        sys.exit(1)

    discdevice=''

    argsList = sys.argv[1:]
    
    loggingLevel = "info"
    
    while ( len(argsList) > 0 ):
        arg = argsList[0]

        if arg == '-h' or arg == '--h' or arg == '--help':
            print usage()
            sys.exit(0)
        
        elif arg == '-q' or arg == '--quiet':
            loggingLevel = None
        
        elif arg == '-v' or arg == '--v' or arg == '--verbose':
            loggingLevel = "debug"

        elif disc_drive.DiscDrive.doesDeviceExist(arg) == False:
            print 'Unrecognised disc/argument: \'' + arg + '\''
            print usage()
            sys.exit(1)
        else:
            discdevice = arg

        #Remove last argument
        argsList = argsList[1:]

    if apppath.checkDependancies() != None:
        logging.error(apppath.checkDependancies())
        sys.exit(1)
        
    if loggingLevel == "debug":
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
        logging.debug('Verbose logging enabled')
    elif loggingLevel == "info":
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

    drive = disc_drive.DiscDrive(discdevice)
    
    if drive.isOpen():
       drive.closeTray()
    
    if not drive.isDiscInserted():
        logging.error('No disc inserted!')
        sys.exit(1)

    else:
        logging.info('Ripsnort begin -------')

        #load config
        config = inireader.loadFile(os.path.join(dirname,'config.ini'))

        #load ripper, scraper and notification
        notify = notification.Notification(config['notification'])
        ripper = ripper.Ripper(config['ripper'],discdevice)
        discName = disc_name.DiscName(drive.mountedDiscName())
        
        contentType = contentTypeForTracksAndName(ripper.discTracks(),discName.formattedName,config)
        
        logging.info('Content type: ' + contentType + ', disc ' + str(discName))

        ripTracks = ripper.discTracks()
    
        logging.info( 'All video tracks:' + str(ripTracks) )

        if contentType == 'movie':
            if config['ripper']['movie_rip_extras'] == True:
                minDuration = 0
                maxDuration = 99999
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
                maxDuration = 99999
                ripExtraContent = True
            else:
                minDuration = config['ripper']['tvepisode_min_length_seconds']
                maxDuration = config['ripper']['tvepisode_max_length_seconds']
                ripExtraContent = False

            ripPathComplete = config['ripper']['tv_complete_save_path']
            ripPathIncomplete = config['ripper']['tv_incomplete_save_path']
            
        else:
            logging.error('Unexpected content type ' + str(contentType))
            sys.exit(1)
            
        logging.debug('MinDuration ' + str(minDuration) + ' maxDuration ' + str(maxDuration) + ' ripExtraContent ' + str(ripExtraContent))

        if config['ripper']['backup_disc'] == False and config['ripper']['rip_disc'] == False:
            logging.error( 'No ripping enabled. Nothing to do without either rip_disc or backup_disc set to True' )
            sys.exit(1)

        if config['ripper']['backup_disc'] == True:
            logging.info( 'Making disk backup' )
            notify.startedBackingUpDisc(formattedName)
            ripper.ripDiscBackup( os.path.join(ripPathIncomplete,discName.formattedName) )
            notify.finishedBackingUpDisc(formattedName)

        ripTracks = disc_track.tracksBetweenDurationMinMax(ripTracks,minDuration,maxDuration)
        
        logging.info( 'Video candidates minDuration(' +str(minDuration)+ ') maxDuration(' +str(maxDuration)+ '):' + str(ripTracks) )

        if config['ripper']['rip_disc'] == True:
            logging.info('Ripping disc tracks: ' + str(ripTracks))
            
            if len(ripTracks) > 0:
                notify.startedRippingTracks( ripTracks, discName.formattedName )
            
#            ripper.ripDiscTracks( ripTracks, os.path.join(ripPathIncomplete,discName.formattedName) )
            
            ripTrackMediaMap = {}

            for rippedTrack in ripTracks:
                srcFile = os.path.join(ripPathIncomplete,discName.formattedName,rippedTrack.outputFileName)
                
                if os.path.exists(srcFile) == False:
                    logging.error('Failed to find extracted ripped file: ' + srcFile)
                    continue
                
                logging.debug('Finding media for track: ' + str(rippedTrack))
                mediaObj = getMediaObjectForLocalVideoTrack(srcFile,discName,contentType)
                logging.debug('Got media object: ' + str(mediaObj) + ' for file: ' + srcFile)
                
                if mediaObj is None:
                    continue
                
                ripTrackMediaMap[rippedTrack] = mediaObj

                fileformat = ''

                if mediaObj.content_type == 'movie':
                    fileformat = config['ripper']['movie_save_format']
                elif mediaObj.content_type == 'tvshow' or mediaObj.content_type == 'tvepisode':
                    fileformat = config['ripper']['tv_save_format']
                else:
                    logging.error('Unrecognised content type: ' + str(mediaObj.content_type))
                    continue

                newFileExt = rippedTrack.outputFileName.split('.')[-1]
                newFileName = outputFileForTrackWithFormat(mediaObj,fileformat)
                newFileName = sanitizeFilePath(newFileName)
                dstFile = os.path.join(ripPathComplete,(newFileName+'.'+newFileExt))
                
                if not os.path.exists(os.path.dirname(dstFile)):
                    logging.debug('Creating folder path: ' + os.path.dirname(dstFile))
                    os.makedirs(os.path.dirname(dstFile))

                logging.info('Moving file from: ' + srcFile + ' destination: ' + dstFile)

                os.rename(srcFile,dstFile)

            incompleteFolder = os.path.join(ripPathIncomplete,discName.formattedName) 
            if not doesFolderContainVideoFiles(incompleteFolder):
                logging.info('Removing folder: ' + str(incompleteFolder))
                shutil.rmtree(incompleteFolder)
                
            #TODO change notify message to include move location
            
            if len(ripTracks) > 0:
                notify.finishedRippingTracks( ripTracks, discName.formattedName, ripTrackMediaMap )
            else:
                notify.failure( discName.formattedName, 'Failed to locate correct video tracks to rip' )
                
        logging.info('Ejecting drive: ' + str(discdevice))
        drive.openTray()
        
        logging.info('Ripsnort complete -------')
        
    
    
