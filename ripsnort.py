#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import os
import sys
import shutil
import logging
import Queue
import threading


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
import string_match
import objectcache


def sanitizeFilePath(filePathString):
    import string
    valid_chars = "-_.()/\\ %s%s" % (string.ascii_letters, string.digits)
    newPath = ''.join(c for c in filePathString if c in valid_chars)
    return newPath


def isInternetConnectionAvailable():
    try:
        '''Google IP'''
        import urllib2
        response=urllib2.urlopen('http://74.125.228.100',timeout=5)
        return True
    except urllib2.URLError as err:
        return False


def doesFolderContainVideoFiles(folderDir):
    doesContentVideoFiles = False
    
    osList = []
    
    try:
        osList = os.listdir(folderDir)
    except:
        pass
    
    for fileName in osList:
        try:
            ext = fileName.split('.')[-1]
            if ext == 'mkv' or ext == 'mp4' or ext == 'avi' or ext == 'm2ts' or ext == 'ts':
                doesContentVideoFiles = True
        except:
            pass
    
    return doesContentVideoFiles


def contentTypeForTracksAndName(tracks,name,config):
    if len(name) == 0 or len(tracks) == 0:
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
        minDuration = int(config['ripper']['videotrack_min_length_seconds'])
        maxDuration = int(config['ripper']['videotrack_max_length_seconds'])
        
        tracksFiltered = disc_track.tracksBetweenDurationMinMax(tracks,minDuration,maxDuration)
        
        #check the durations of the tv tracks, if they are similar in length, then we can assume they are episodes
        
        durations = []
        durationTotalS = 0
        
        for track in tracksFiltered:
            durations.append( track.durationS )
            durationTotalS += track.durationS
        
        if len(durations) > 0:
            durationAverage = durationTotalS / len(durations)        
            durationsAreCloseToAverage = True
    
            for track in tracksFiltered:
                if abs(track.durationS / durationAverage) < 0.9 or abs(track.durationS / durationAverage) > 1.1:
                    durationsAreCloseToAverage = False
                    break
        
            logging.debug('Average track duration: ' + str(durationAverage) + ' durationsAreClose: ' + str(durationsAreCloseToAverage))
        
            if durationsAreCloseToAverage:
                contentType = 'tvshow'
            else:
                #durations don't all match, assume its a movie
                contentType = 'movie'
    
    if contentType == None:
        contentType = 'Unknown'
    
    logging.debug('Content type for name:' + str(name) + ', tracks:' + str(tracks) + ' = ' + str(contentType))
    
    return contentType


def outputFileForTrackWithFormat(mediaObj,fileformat):
    newFilePath = fileformat
    
    logging.debug('Loading output file format: ' + str(fileformat) + ' for track: ' + str(mediaObj))
    
    newFilePath = newFilePath.replace('{N}',mediaObj.title)

    #season matches
    for match in re.findall(r'({[S|s].*?})',newFilePath):
        replacementText = ''
        
        seasonNumber = ''
        
        if hasattr(mediaObj,'season_number'):
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
        
        if hasattr(mediaObj,'episode_number'):
            if mediaObj.episode_number is not None:
                episodeNumber = str(mediaObj.episode_number)
            
        replacementText = episodeNumber

        padMatches = re.findall(r'\.pad\((\d)\)',match)
        
        if len(padMatches) > 0:
            padNum = int(padMatches[0])
            replacementText = str(episodeNumber).zfill(padNum)

        newFilePath = newFilePath.replace(match,replacementText)
        
    episodeTitle = ''
    
    if hasattr(mediaObj,'episode_title'):
        if mediaObj.episode_title is not None:
            episodeTitle = mediaObj.episode_title

    newFilePath = newFilePath.replace('{T}',episodeTitle)

    productionYear = ''
    
    if hasattr(mediaObj,'production_year'):
        if mediaObj.production_year is not None:
            productionYear = mediaObj.production_year

    newFilePath = newFilePath.replace('{Y}',str(productionYear))

    assert '{' not in newFilePath
    assert '}' not in newFilePath
    
    return newFilePath


def allMediaCandidatesForDiscName(discname):
    candidateListMovie = scraper.MediaScraper().findContent(discname.title,'movie')
    candidateListTVShow = scraper.MediaScraper().findContent(discname.title,'tvshow')
    candidateListTVEpisodes = []

    '''Remove duplicates'''
    candidateListMovie=list(set(candidateListMovie))
    candidateListTVShow=list(set(candidateListTVShow))

    #sort candidates by the titles proximity to the disc name
    candidateListMovie.sort(key=lambda x: string_match.distanceBetweenStrings(x.title,discname.title))
    candidateListTVShow.sort(key=lambda x: string_match.distanceBetweenStrings(x.title,discname.title))

    for candidateShow in candidateListTVShow:
        if candidateShow is None:
            continue

        logging.debug('Searching for episodes from season ' + str(discname.season) + ' show:' + str(candidateShow))

        if discname.season is not None:
            logging.info('Fetching all episodes for TV show: ' + str(candidateShow.title) + ', this may take some time')
            tvMediaObjs = scraper.MediaScraper().findTVEpisodesForSeason(candidateShow,discname.season)
        else:
            tvMediaObjs = scraper.MediaScraper().findTVEpisodesForShow(candidateShow)

        logging.debug('Adding TV Media candidates: ' + str(tvMediaObjs))

        candidateListTVEpisodes += tvMediaObjs

    returnCandidateList = candidateListMovie+candidateListTVEpisodes

    return returnCandidateList


def getMediaObjectForLocalVideoTrack(trackPath,candidateList):
    mediaObjReturn = None
    mediaObjMatchRatio = 0.0

    localVideoTrack = disc_track.LocalTrackMkv(trackPath)
    logging.debug('Opened video file: ' + trackPath + ' track:' + str(localVideoTrack) + ' targetDuration:' + str(localVideoTrack.durationS))
    
    if localVideoTrack == None or localVideoTrack.numberOfSubtitles() == 0:
        logging.warn('Either invalid video track or no subtitles. Aborting search for media: ' + trackPath)
        return None
    
    subScraper = scraper.SubtitleScraper()
    
    allLanguages = localVideoTrack.allSubtitleLanguages()
    
    #Prefer english for searching if available
    if 'eng' in allLanguages:
        allLanguages.remove('eng')
        allLanguages.insert(0,'eng')
    
    #Get all the subtitle languages and test 2 versions of each (maximum of 3 languages)
    for localSubLangIndex in range(0,min(3,len(allLanguages))):
        localSubLang = allLanguages[localSubLangIndex]
        for localSubIndex in range(0,min(2,localVideoTrack.numberOfSubtitlesOfLanguage(localSubLang))):

            logging.debug('Track local caption at index: ' + str(localSubLangIndex) + ' for language ' + str(localSubLang))

            subLocal = localVideoTrack.subtitleOfLanguageAtSubindex(localSubLang,localSubIndex)
            assert(len(subLocal.text)>0)

            for mediaObj in candidateList:
                subsRemote = subScraper.subtitlesForMediaContent(mediaObj,localSubLang)

                if len(subsRemote) == 0:
                    logging.error('No subs to compare')
                    continue

                subCmp = subsRemote[0]

                logging.debug('Testing for media object: ' + str(mediaObj) + ', found ' + str(subCmp) + ' subtitles. ' + str(len(localVideoTrack.subtitles)) + ' local subtitles')

                newRatio = subLocal.matchRatioWithCaption(subCmp)

                logging.debug('Got match ratio: ' + str(newRatio) + ' for caption\nlocal: ' + str(subLocal.textCompare[0:300]) + ',\nremote: ' + str(subCmp.textCompare[0:300]))
                
                if newRatio > mediaObjMatchRatio and newRatio > 0.70:
                    mediaObjMatchRatio = newRatio
                    mediaObjReturn = mediaObj

                if newRatio > 0.90:
                    logging.debug('Ending search prematurely, result found with confidence(' +str(newRatio)+ ') for media: ' + str(mediaObjReturn))
                    return mediaObjReturn

    logging.debug('Best match ratio:' + str(mediaObjMatchRatio) + ' for mediafile: ' +str(mediaObjReturn))

    return mediaObjReturn 


def isTrackInDurationRange(config,ripTrack):
    shouldKeep = False

    minDuration = config['ripper']['videotrack_min_length_seconds']
    maxDuration = config['ripper']['videotrack_max_length_seconds']
    ripExtraContent = config['ripper']['rip_extras']

    logging.debug('MinDuration ' + str(minDuration) + ' maxDuration ' + str(maxDuration) + ' ripExtraContent ' + str(ripExtraContent))
        
    if ( ripExtraContent ):
        shouldKeep = True
    elif ( ripTrack.durationS >= minDuration and ripTrack.durationS <= maxDuration ):
        shouldKeep = True
        
    return shouldKeep

def ripPathIncompleteForContentType(config,contentType):
    
    if str(contentType) == 'movie':
        ripPathIncomplete = config['ripper']['movie_incomplete_save_path']

    elif str(contentType) == 'tvshow':
        ripPathIncomplete = config['ripper']['tv_incomplete_save_path']

    else:
        if not contentType:
            contentType = 'Unknown'

        ripPathIncomplete = os.path.join(apppath.pathTemporary(),contentType)
        
    return ripPathIncomplete

def ripPathCompleteForContentType(config,contentType):
    
    if str(contentType) == 'movie':
        ripPathComplete = config['ripper']['movie_complete_save_path']

    elif str(contentType) == 'tvshow' or str(contentType) == 'tvepisode':
        ripPathComplete = config['ripper']['tv_complete_save_path']

    else:
        if not contentType:
            contentType = 'Unknown'

        ripPathComplete = os.path.join(apppath.pathTemporary(),contentType)
        
    return ripPathComplete

def findNonConflictingFilePath(dstFile):
    #We don't want to override an existing file, so find a filename not currently used
    if os.path.exists(dstFile):
        dstFileName = os.path.basename(dstFile)
        dstDir = os.path.dirname(dstFile)
        fileExt = os.path.splitext(dstFileName)[1]
        fileName = os.path.splitext(dstFileName)[0]

        newFile = dstFile
        idx = 1
        while os.path.exists(newFile):
            newFile = os.path.join(dstDir, (fileName + ' (' + str(idx) + ')' + fileExt))
            idx += 1

        dstFile = newFile
    
    return dstFile

def identifyContent(ripTrackPath,candidates=[]):
    mediaObjectReturn = None
    
    if not ripTrackPath.endswith(('.mkv')):
        logging.error('File not supported. Only mkv files supported')

    #We don't want to override an existing file, so find a filename not currently used
    elif os.path.exists(ripTrackPath):
        discName = disc_name.DiscName(ripTrackPath)
    
        candidates = allMediaCandidatesForDiscName(discName)
        
        videoTrack = disc_track.LocalTrackMkv(ripTrackPath)
        
        mediaObjectReturn = getMediaObjectForLocalVideoTrack(ripTrackPath,candidates)
        
    else:
        logging.error('File does not exist: ' + str(ripTrackPath))
    
    return mediaObjectReturn

def ripContent(config,notify,ripper,ripType,ripPath):
    drive = None

    if ripType == 'disc':
        drive = disc_drive.DiscDrive(ripPath)
    
        if drive.isOpen():
           drive.closeTray()
    
        if not drive.isDiscInserted():
            logging.error('No disc inserted!')
            sys.exit(1)

    if ripType == 'disc':
        discName = disc_name.DiscName(drive.mountedDiscName())
    elif ripType == 'file' or ripType == 'dir':
        discName = disc_name.DiscName(os.path.basename(ripPath))

    contentType = contentTypeForTracksAndName(ripper.tracks(),discName.formattedName,config)

    logging.info('Content type: ' + str(contentType) + ', disc ' + str(discName.title))

    ripPathIncomplete = ripPathIncompleteForContentType(config,contentType)

    ripTracks = []

    '''While we rip the video tracks. Asynchronously pre-cache all the possible media candidates'''
    t = threading.Thread(target=allMediaCandidatesForDiscName)
    t.daemon = True
    t.start()
        
    if ripper.hasLocatedMediaTracks():
        discTracksToRip = ripper.tracks()

        logging.info( 'All video tracks:' + str(ripTracks) )

        if len(ripper.tracks()) > 0:
            discTracksToRip = filter(lambda x: isTrackInDurationRange(config,x), discTracksToRip)

        logging.info('Ripping disc tracks: ' + str(discTracksToRip))
        notify.startedRippingTracks( discTracksToRip, discName.formattedName )

        ripTracks = ripper.ripTracks( discTracksToRip, os.path.join(ripPathIncomplete,discName.formattedName) )
            
        logging.info('Ripped tracks ' + str(ripTracks))
    else:
        #Unable to find out matching track candidates. Rip all then filter after
        notify.startedRippingTracks( [], discName.formattedName )
            
        ripPath = os.path.join(ripPathIncomplete,discName.formattedName)

        logging.info('Ripping all disc tracks to: ' + str(ripPath))

        ripTracks = ripper.ripAllTracks( ripPath )
 
        deleteRipTracks = []
        keepRipTracks = []
            
        for track in ripTracks:
            if isTrackInDurationRange(config,track):
                keepRipTracks.append(track)
            else:
                deleteRipTracks.append(track)
            
        #remove files
        for track in deleteRipTracks:
            os.remove(track.filepath)

        ripTracks = keepRipTracks

            
    t.join()
            
    mediaCandidates = allMediaCandidatesForDiscName(discName)
    mediaCandidates.sort(key=lambda x: string_match.distanceBetweenStrings(x.title,discName.title))        

    logging.info('Found media candidates: ' + str(mediaCandidates))

    ripTrackMediaMap = {}

    for rippedTrack in ripTracks:
        if os.path.exists(rippedTrack.filepath) == False:
            logging.error('Failed to find extracted ripped file: ' + rippedTrack.filepath)
            continue
                
        logging.debug('Finding media for track: ' + str(rippedTrack))
        mediaObj = getMediaObjectForLocalVideoTrack(rippedTrack.filepath,mediaCandidates)
        logging.debug('Got media object: ' + str(mediaObj) + ' for file: ' + rippedTrack.filepath)
                
        if mediaObj is None:
            continue
                
        ripTrackMediaMap[rippedTrack] = mediaObj

        fileformat = ''

        if mediaObj.content_type == 'movie':
            fileformat = config['ripper']['movie_save_format']
            ripPathComplete = ripPathCompleteForContentType(config,mediaObj.content_type)

        elif mediaObj.content_type == 'tvshow' or mediaObj.content_type == 'tvepisode':
            fileformat = config['ripper']['tv_save_format']
            ripPathComplete = ripPathCompleteForContentType(config,mediaObj.content_type)

        else:
            logging.error('Unrecognised content type: ' + str(mediaObj.content_type))
            continue

        logging.debug('Content type: ' + str(mediaObj.content_type) + ', destination folder: ' + str(ripPathComplete))

        newFileExt = rippedTrack.filepath.split('.')[-1]
        newFileName = outputFileForTrackWithFormat(mediaObj,fileformat)
        newFileName = sanitizeFilePath(newFileName)
        dstFile = os.path.join(ripPathComplete,(newFileName+'.'+newFileExt))
                
        if not os.path.exists(os.path.dirname(dstFile)):
            logging.debug('Creating folder path: ' + os.path.dirname(dstFile))
            os.makedirs(os.path.dirname(dstFile))
        
        dstFile = findNonConflictingFilePath(dstFile)

        logging.info('Moving file from: ' + rippedTrack.filepath + ' destination: ' + dstFile)
        os.rename(rippedTrack.filepath,dstFile)

    incompleteFolder = os.path.join(ripPathIncomplete,discName.formattedName) 
    if not doesFolderContainVideoFiles(incompleteFolder):
        logging.info('Removing folder: ' + str(incompleteFolder))
        try:
            shutil.rmtree(incompleteFolder)
        except:
            pass
                
    #TODO change notify message to include move location

    if len(ripTracks) > 0:
        notify.finishedRippingTracks( ripTracks, discName.formattedName, ripTrackMediaMap )
    else:
        notify.failure( discName.formattedName, 'Failed to locate correct video tracks to rip' )

    if ripType == 'disc':
        logging.info('Ejecting drive: ' + str(ripPath))
        drive.openTray()

    return ripTracks


def usage():
    return '''
usage: [-v] disc
    -h --help  Prints this usage information.
    -q --quiet         print nothing to stdout
    -v --verbose       print extra information
    -i --identify      identify media content only
    -r --rename        rename media content after identifying
    -c --clearcache    clear everything from cache

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

    ripPath=''
    ripType=''
    identifyMode = False
    renameMode = False

    argsList = sys.argv[1:]
    
    loggingLevel = "info"
    
    while ( len(argsList) > 0 ):
        arg = argsList[0]

        if arg == '-h' or arg == '--h' or arg == '--help':
            print usage()
            sys.exit(0)
        
        elif arg == '-q' or arg == '--quiet':
            loggingLevel = None
        
            
        elif arg == '-i' or arg == '--i' or arg == '--identify':
            identifyMode = True
            
        elif arg == '-r' or arg == '--r' or arg == '--rename':
            renameMode = True
            
        elif arg == '-c' or arg == '--c' or arg == '--cache':
            objectcache.clearAllCaches()
            print 'Cache cleared'

        elif arg == '-v' or arg == '--v' or arg == '--verbose':
            loggingLevel = "debug"

        else:
            isFolder = os.path.isdir(arg)
            isISO = os.path.isfile(arg)
            isDiscDevice = disc_drive.DiscDrive.doesDeviceExist(arg)
            
            if isFolder:
                ripPath = arg
                ripType = 'dir'

            elif isISO:
                ripPath = arg
                ripType = 'file'

            elif isDiscDevice:
                ripPath = arg
                ripType = 'disc'

            else:
                print 'Unrecognised disc/argument: \'' + arg + '\''
                print usage()
                sys.exit(1)

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

    #load config
    config = inireader.loadFile(os.path.join(os.path.dirname(__file__),'config.ini'))

    if identifyMode or renameMode:
        logging.info('Ripsnort begin -------')

        mediaObj = identifyContent(ripPath)
        if mediaObj:
            if renameMode:
                if mediaObj.content_type == 'movie':
                    fileformat = config['ripper']['movie_save_format']
                    ripPathComplete = ripPathCompleteForContentType(config,mediaObj.content_type)

                elif mediaObj.content_type == 'tvshow' or mediaObj.content_type == 'tvepisode':
                    fileformat = config['ripper']['tv_save_format']
                    ripPathComplete = ripPathCompleteForContentType(config,mediaObj.content_type)

                else:
                    logging.error('Unrecognised content type: ' + str(mediaObj.content_type))
                    sys.exit(1)

                logging.debug('Content type: ' + str(mediaObj.content_type) + ', destination folder: ' + str(ripPathComplete))

                newFileExt = ripPath.split('.')[-1]
                newFileName = outputFileForTrackWithFormat(mediaObj,fileformat)
                newFileName = sanitizeFilePath(newFileName)
                dstFile = os.path.join(ripPathComplete,(newFileName+'.'+newFileExt))

                if not os.path.exists(os.path.dirname(dstFile)):
                    logging.debug('Creating folder path: ' + os.path.dirname(dstFile))
                    os.makedirs(os.path.dirname(dstFile))
        
                dstFile = findNonConflictingFilePath(dstFile)

                logging.info('Moving file from: ' + str(ripPath) + ' destination: ' + str(dstFile))
                os.rename(ripPath,dstFile)

            else:
                if mediaObj.content_type == 'tvepisode':
                    print 'ContentMatch Show: ' + str(mediaObj.title)
                    print 'ContentMatch Season: ' + str(mediaObj.season_number)
                    print 'ContentMatch EpisodeNumber: ' + str(mediaObj.episode_number)
                    print 'ContentMatch EpisodeName: ' + str(mediaObj.episode_title)
                else:
                    print 'ContentMatch Title: ' + str(mediaObj.title)

                print 'ContentMatch Year: ' + str(mediaObj.production_year)
        else:
            print 'Failed to find media for: ' + str(ripPath)

        logging.info('Ripsnort complete -------')

    elif ripPath:
        logging.info('Ripsnort begin -------')

        #load ripper, scraper and notification
        notify = notification.Notification(config['notification'])
        ripper = ripper.Ripper(config['ripper'],ripPath,ripType)

        ripContent(config,notify,ripper,ripType,ripPath)
        logging.info('Ripsnort complete -------')

    else:
        print 'Invalid arguments'
        print usage()
        sys.exit(1)



