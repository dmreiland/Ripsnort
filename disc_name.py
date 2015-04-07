#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import re
import sys
import json
import logging


import apppath


dirname = os.path.dirname(os.path.realpath( __file__ ))

sys.path.append( os.path.join(dirname,"subtitle") )
import caption


class DiscName:

    def __init__(self,disc_name):
        self.originalDiscName = disc_name
        
        title, season, disc = DiscName.titleSeasonAndDiscFromDiscName(DiscName._removeUnnecessaryCharsFromTitle(disc_name))
        title = DiscName._titleUpdateSpecialCases(title)
        self.title = title
        self.season = season
        self.discNumber = disc
        
        if self.discNumber == None:
           self.discNumber = 1 

        self.formattedName = self.title
        
        if self.season is not None:
            self.formattedName = self.formattedName + ' - Season ' + str(self.season)
        
        if self.discNumber is not None:
            self.formattedName = self.formattedName + ' - DiscNumber ' + str(self.discNumber)
            
        logging.info('DiscName converted ' + str(self.originalDiscName) + ' to ' + str(self.title) + ' season ' + str(self.season) + ' discnum ' + str(self.discNumber))

    @staticmethod
    def _removeUnnecessaryCharsFromTitle(title):
        tmpName = title
        
        #Given file path
        if os.path.exists(tmpName):
            #remove extension
            filePath, fileExtension = os.path.splitext(tmpName)
            tmpName = tmpName.replace(fileExtension,'')

            #Remove noise
            pathComponents = DiscName._OSSplitPath(tmpName)
            pathComponents = DiscName._removeUnnecessaryCharsFromPathComponents(pathComponents)
            
            regMakeMkvTitleTest = re.compile(r'^(?i)title\d+')
            
            pathComponents = filter(lambda x:not regMakeMkvTitleTest.match(x), pathComponents)
            
            tmpName = (' '.join(pathComponents)).strip()
            
            logging.debug('Stripped file path down to ' + tmpName)
        
        tmpName = re.sub('(?i).iso$', '', tmpName)

        # Remove anything in brackets
        tmpName = re.sub(r'\[.*?\]','',tmpName)
        tmpName = re.sub(r'\{.*?\}','',tmpName)
        tmpName = re.sub(r'\(\D+\)','',tmpName)
        
        #remove anything in brackets that is not of length 4
        tmpName = re.sub(r'\(\w{5,}?\)','',tmpName)
        tmpName = re.sub(r'\(\w{1,3}?\)','',tmpName)
        
        tmpName = re.sub(r'\-\=.*\=\-','',tmpName)
        tmpName = re.sub(r'\~\=.*\=\~','',tmpName)

        tmpName = re.sub('(?i)\ de\ ', ' the ', tmpName)

        regexRemove = [
                       r'(?i)non[-| ]retail',
                       r'(?i)(?:unrated|extended|special|ultimate|limited|collectors|standard|delux|deluxe|non)?[_| ]?(?:cut|3d|retail|dvd|bluray|blu-ray)?[ |_]?(?:cut|edition|version)',

                       r'(?i)[_| ]?TrueHD7.1',
                       r'(?i)[_| ]?TrueHD5.1',
                       r'(?i)[_| ]?MA[-|_| ]?7.1',
                       r'(?i)[_| ]?MA[-|_| ]?5.1',
                       r'(?i)[_| ]?TrueHD5.1',
                       r'(?i)[_| ]?DTS-MA',
                       r'(?i)[_| ]?DTS-HD',
                       r'(?i)[_| ]?DD-?5.1C?h?',
                       r'(?i)[_| ]?DD-?7.1C?h?',
                       r'(?i)[_| ]?[5|7].1 Audio Channel',
                       r'(?i)[_| ]?[5|7].1 Channel Audio',
                       r'(?i)[_| ]?Dual[\-|\ |\_]?Audio',
                       r'(?i)[_| ]?flac',
                       r'(?i)[_| ]?mp3',
                       r'(?i)[_| ]?aac',
                       r'(?i)[_| ]?aac2',
                       r'(?i)[_| ]?aac3',
                       r'(?i)[_| ]?ac3',

                       r'(?i)[_| ]?srt',
                       r'(?i)[_| ]?vobsub',
                       r'(?i)[_| ]?MSubs',

                       r'(?i)[_| ]?AVC',
                       r'(?i)[_| ]?CHDBits',
                       r'(?i)[_| ]?ETRG?',
                       r'(?i)[_| ]?eztv',
                       r'(?i)[_| ]?LOL',
                       r'(?i)[_| ]?KILLERS',
                       r'(?i)[_| ]?EVO',
                       r'(?i)[_| ]?RePack?',
                       r'(?i)[_| ]?Codex',
                       r'(?i)[_| ]?YIFY',
                       r'(?i)[_| ]?RARBG',
                       r'(?i)[_| ]?PSYCHD',
                       r'(?i)[_| ]?PublicHD',
                       r'(?i)[_| ]?SPLiTSVILLE',
                       r'(?i)[_| ]?READNFO',
                       r'(?i)[_| ]?\juggs',
                       r'(?i)[_| ]?\NoGrouP',
                       r'(?i)[_| ]?\SUMO',
                       r'(?i)[_| ]?\MAXSPEED',
                       r'(?i)[_| ]?\New\ Source?',
                       r'(?i)[_| ]?\BiDA',
                       r'(?i)[_| ]?\TeamTNT',
                       r'(?i)[_| ]?\ShAaNiG',
                       r'(?i)[_| ]?2Lions\-Team',
                       r'(?i)[_| ]?padderax',
                       r'(?i)[_| ]?TMRG',
                       r'(?i)[_| ]?MSubs$',
                       r'(?i)[_| ]?D3viL',
                       r'(?i)[_| ]?Mafiaking',
                       r'(?i)[_| ]?Dts-wiki',
                       r'(?i)[_| ]?CRYME',
                       r'(?i)[_| ]?JYK',
                       r'(?i)[_| ]?Hon3y',
                       r'(?i)[_| ]?Team TellyTNT',
                       r'(?i)[_| ]?ESubs',
                       r'(?i)[_| ]?MBRHDRG',
                       r'(?i)[_| ]?ACAB',

                       r'ᴴᴰ',
                       r'(?i)[_| ]repack',
                       r'(?i)[_| ]internal',
                       r'(?i)[_| ]nfofix',
                       r'(?i)[_| ]proper',
                       r'(?i)[_| ]unrated',
                       r'(?i)[_| ]?[1|2][_| ]?cd',
                       r'(?i)[_| ]?[1|2][_| ]?dvd',
                       r'(?i)[_| ]?1080[p|i]',
                       r'(?i)[_| ]?720[p|i]',
                       r'(?i)[_| ]?576[p|i]',
                       r'(?i)[_| ]?480[p|i]',
                       r'(?i)[_| ]?avi$',
                       r'(?i)[_| ]?xvid',
                       r'(?i)[_| ]?divx',
                       r'(?i)[_| ]?mkv',
                       r'(?i)[_| ]?mp4',
                       r'(?i)[_| ]?[h|x]264',
                       r'(?i)[_| ]?iTunes$',
                       r'(?i)[_| ]?WEB\-?RIP',
                       r'(?i)[_| ]?WEB\-?DL',
                       r'(?i)[_| ]?DVDSCR',
                       r'(?i)[_| ]?HDCAM',
                       r'(?i)[_| ]?HD\-?TS',
                       r'(?i)[_| ]?TS$',
                       r'(?i)[_| ]?hd[\-|\_| ]?rip',
                       r'(?i)[_| ]?hd[\-|\_| ]?screener',
                       r'(?i)[_| ]?br[\-|\_| ]?rip',
                       r'(?i)[_| ]?br[\-|\_| ]?screener',
                       r'(?i)[_| ]?dvd[\-|\_| ]?rip',
                       r'(?i)[_| ]?dvd[\-|\_| ]?screener',
                       r'(?i)[_| ]?screener',
                       r'(?i)[_| ]?telecine',
                       r'(?i)[_| ]?telesync',
                       r'(?i)[_| ]?pal$',
                       r'(?i)[_| ]?ntsc',
                       r'(?i)[_| ]?dvd$',
                       r'(?i)[_| ]?blu[\-|_| ]?ray',
                       r'(?i)[_| ]?retail',
                       r'(?i)[_| ]?3d']

        didRegexMatch = True
    
        while didRegexMatch:
            didRegexMatch = False

            for regTest in regexRemove:
                matchResults = re.search(regTest,tmpName)
                if matchResults != None:
                    tmpName = re.sub(regTest,'',tmpName)
                    didRegexMatch = True

        # Clean up
        tmpName = tmpName.replace("\"", "")
        tmpName = tmpName.replace(".", " ")
        tmpName = tmpName.replace("-", " ")
        tmpName = tmpName.replace("  ", " ")

        #replace any erronous chars with space & remove double spaces
        tmpName = tmpName.replace('[]',' ').replace('()',' ').replace('{}',' ').replace('--',' ').replace('_',' ').strip()
        tmpName = re.sub('\s{2,}', ' ', tmpName)

        if tmpName[-1] == '-' or tmpName[-1] == '.' or tmpName[-1] == '_' or tmpName[-1] == '\\' or tmpName[-1] == '{' or tmpName[-1] == '}':
            tmpName = tmpName[0:-1]
    
        #capitalize first letter of each word
        tmpName = tmpName.title()
        
        return tmpName.strip()


    @staticmethod
    def titleSeasonAndDiscFromDiscName(disc_name):
        tmpName = disc_name
    
        logging.debug('Removed unnecessary chars to \'' + tmpName + '\'')

        tmpName, season = DiscName._seasonNumberOnlyFromDiscName(tmpName)
        tmpName, disc = DiscName._discNumberOnlyFromDiscName(tmpName)
        
        tmpName, seasonMixed, discMixed = DiscName._mixedDiscAndSeasonFromDiscName(tmpName)
        tmpName, discShort = DiscName._discNumberShortFromDiscName(tmpName)
        
        if season == None:
            season = seasonMixed
            
        if disc == None:
            disc = discMixed
            
        if disc == None:
            disc = discShort
        
        #look for numbers prepended to the end of the last word and add space
        numberWhitespacing = r'\b(\D+)(\d+)\b$'
        numberWhitespacingRE = re.compile(numberWhitespacing)
        
        if len(numberWhitespacingRE.findall(tmpName)) > 0:
            whitespaceSearch = numberWhitespacingRE.search(tmpName)
            tmpName = re.sub(numberWhitespacing,whitespaceSearch.groups()[0] + ' ' + whitespaceSearch.groups()[1],tmpName)
            
        tmpName = tmpName.strip()

        #if its a short name, chances are its an acronym i.e CSI
        if len(tmpName) <= 3:
            tmpName = tmpName.upper()
            
        tmpName = re.sub('\s{2,}', ' ', tmpName)

        logging.debug('Converted disc name: \'' +disc_name+ '\' to title:' + tmpName + ', season:' + str(season) + ', disc:' + str(disc))

        return [tmpName,season,disc]
    
    @staticmethod
    def _seasonNumberOnlyFromDiscName(disc_name):
        tmpName = disc_name
        
        #first matching group - season, 2nd - disc number
        regexSeason = [r'(?i)(?:season|series)(?:[_|\.|\ ])?([\d{1,2}])']

        season = None

        for regTest in regexSeason:
            regexSearch = re.search(regTest,tmpName)

            if regexSearch != None:
                logging.debug('Matched regex: ' + regTest + ', for text: ' + tmpName)
                matchGroups = regexSearch.groups()

                try:
                    season = int( matchGroups[0] )
                except:
                    pass

                tmpName = re.sub(regTest,'',tmpName)
                didRegexMatch = True
                
        return [tmpName,season]
        
    @staticmethod
    def _discNumberOnlyFromDiscName(disc_name):
        regexDiskOnly = [r'(?i)(?:disknumber|discnumber|disc|disk)(?:_|\.|\ )([\d{1,2}])']

        disc = None
        tmpName = disc_name

        for regTest in regexDiskOnly:
            regexSearch = re.search(regTest,tmpName)

            if regexSearch != None:
                logging.debug('Matched regex: ' + regTest + ', for text: ' + tmpName)
                matchGroups = regexSearch.groups()

                try:
                    disc = int( matchGroups[0] )
                except:
                    pass

                tmpName = re.sub(regTest,'',tmpName)
                
        return [tmpName,disc]
    
    @staticmethod
    def _discNumberShortFromDiscName(disc_name):
        regexDiskOnly = [r'(?i)(?:d|disc|disk)[-|_| ]?([\b\d{1,2}]\b)',
                           r'(?i)(?:d|disc|disk)(\d{1,2})[-|_| ]?(?:[t|T]\d{1,2})']

        disc = None
        tmpName = disc_name

        for regTest in regexDiskOnly:
            regexSearch = re.search(regTest,tmpName)

            if regexSearch != None:
                logging.debug('Matched regex: ' + regTest)
                matchGroups = regexSearch.groups()

                try:
                    disc = int( matchGroups[0] )
                except:
                    pass

                tmpName = re.sub(regTest,'',tmpName)
                
        return [tmpName,disc]
    
    @staticmethod
    def _mixedDiscAndSeasonFromDiscName(disc_name):
        tmpName = disc_name
        
        #first matching group - season, 2nd - disc number
        regexSeasonDisk = [r'(?i)s([\d{1,2}])_?d([\d{1,2}])',
                           r'(?i)(?:season|series|s)?_?([\d{1,2}])_?(?:disknumber|discnumber|disc|disk|d)[_|\ ]([\d{1,2}])',
                           r'(?i)(?:s|series|season\s)[-|_| ]?([\d{1,2}]).*(?:d|disc|disk)[-|_| ]?([\d{1,2}])',
                           r'(?i)([\d{1,2}])[-|_| ]([\d{1,2}])$']
        
        season = None
        disc = None

        for regTest in regexSeasonDisk:
            print 'testing ' + regTest + ',' + tmpName
            regexSearch = re.search(regTest,tmpName)

            if regexSearch != None:
                logging.debug('Matched regex: ' + regTest)
                matchGroups = regexSearch.groups()

                try:
                    season = int( matchGroups[0] )
                except:
                    pass
                
                try:
                    disc = int( matchGroups[1] )
                except:
                    pass

                tmpName = re.sub(regTest,'',tmpName)
                didRegexMatch = True
        
        return [tmpName,season,disc]
    
    @staticmethod
    def _titleUpdateSpecialCases(disc_name):
        tmpName = disc_name
        tmpName = tmpName.replace('Bones F1','Bones')
        tmpName = tmpName.replace('Eu 109579','Frasier Season 1')
        tmpName = tmpName.replace('Eu 109580','Frasier Season 2')
        tmpName = tmpName.replace('Eu 109819','Frasier Season 3')
        
        return tmpName


    @staticmethod
    def _OSSplitPath(split_path):
        if split_path[-1] == r'/' or split_path[-1] == r'\\':
            split_path = split_path[0:len(split_path)-1]

        pathSplit_lst = []
        while os.path.basename(split_path):
            pathSplit_lst.append( os.path.basename(split_path) )
            split_path = os.path.dirname(split_path)
        pathSplit_lst.reverse()
        return pathSplit_lst
    
    @staticmethod
    def _removeUnnecessaryCharsFromPathComponents(pathComponents):
        filteredComponents = pathComponents
        
        homePathComponents = DiscName._OSSplitPath(os.path.expanduser('~'))
        
        for pathStrip in homePathComponents:
            filteredComponents = filter(lambda x:x.lower()!=pathStrip.lower(), filteredComponents)
        
        regexChecks = [r'^(?i)(my)?\s?(home)?\s?movies?$',
                       r'^(?i)(my)?\s?(home)?\s?films?$',
                       r'^(?i)(my)?\s?(home)?\s?videos?$',
                       r'^(?i)(my)?\s?(home)?\s?tv\s?shows?$',
                       r'^(?i)(my)?\s?(home)?\s?tv$',
                       r'^(?i)(my)?\s?(home)?\s?downloads?$',
                       r'^(?i)(my)?\s?(home)?\s?shares?$',
                       r'^(?i)(my)?\s?(home)?\s?desktops?$',
                       r'^(?i)(my)?\s?(home)?\s?documents?$',
                       r'^(?i)(my)?\s?(home)?\s?app(lication)?s?$',
                       r'^(?i)$',
                       r'^(?i)homes?$',
                       r'^(?i)use?rs?$',
                       r'^(?i)libs?$',
                       r'^(?i)lo?ca?l?$',
                       r'^(?i)var$',
                       r'^(?i)s?bin$',
                       r'^(?i)etc$',
                       r'^(?i)opt$',
                       r'^(?i)private$',
                       r'^(?i)dis[c|k]$',
                       r'^(?i)workspaces?$',
                       r'^(?i)volumes?$',
                       r'^(?i)mo?u?nts?$',
                       r'^(?i)ripsnort$',
                       r'^(?i)(in)?completes?$',
                       ]
        
        for regTest in regexChecks:
            filteredComponents = filter(lambda x:not re.compile(regTest).match(x), filteredComponents)

        return filteredComponents
    

def test():

    pathComponents = ['Die Hard','incomplete','ripsnort','private','disc','disk','desktop','documents','my home movies','volumes','users','mnt','user','lcl','local','bin','sbin','var','lib','libs','home','homes','mymovies','movies','homemovies','video','videos','video','myvideo','homevideos','download','mydownloads','share','shares','workspace']
    filteredComponents = DiscName._removeUnnecessaryCharsFromPathComponents(pathComponents)
    
    assert len(filteredComponents) == 1
    assert 'Die Hard' == filteredComponents[0]

    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_PAL')
    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_NTSC')
    
    expectedText2 = 'Die Hard'
 
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('Die Hard Limited Edition')
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('Die Hard limited_Edition')
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('Die Hard Special Edition')
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('Die Hard special_edition')
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('Die Hard Extended Edition')
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_EXTENDED_EDITION')
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_DELUX_VERSION')
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('DIE HARD DELUXE VERSION')

    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_SPECIAL_3D_EDITION')
    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_RETAIL')
    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_3D_RETAIL')
    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_DVD')
    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_BLURAY')
    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_BLU_RAY')

    assert 'Pals' == DiscName._removeUnnecessaryCharsFromTitle('PALS')
    assert 'Pals' == DiscName._removeUnnecessaryCharsFromTitle('pals')
    
    assert DiscName('band.of.brothers.disc1-padderax').title == 'Band Of Brothers'
    assert DiscName('band.of.brothers.disc1-padderax').discNumber == 1

    assert DiscName('DIE_HARD_SPECIAL_3D_EDITION').title == 'Die Hard'
    assert DiscName('DIE_HARD_SPECIAL_3D_EDITION').season == None
    assert DiscName('DIE_HARD_SPECIAL_3D_EDITION').discNumber == 1

    assert DiscName('AVATAR_3D_EDITION').title == 'Avatar'
    assert DiscName('AVATAR_3D_EDITION').season == None
    assert DiscName('AVATAR_3D_EDITION').discNumber == 1

    assert DiscName('The Good, the Bad and the Ugly').title == 'The Good, The Bad And The Ugly'
    assert DiscName('The Good, the Bad and the Ugly').season == None
    assert DiscName('The Good, the Bad and the Ugly').discNumber == 1

    assert DiscName('CSI2_3').title == 'CSI'
    assert DiscName('CSI2_3').season == 2
    assert DiscName('CSI2_3').discNumber == 3

    assert DiscName('BONES_SEASON_8_F1_DISC_1').title == 'Bones'
    assert DiscName('BONES_SEASON_8_F1_DISC_1').season == 8
    assert DiscName('BONES_SEASON_8_F1_DISC_1').discNumber == 1

    assert DiscName('BONES_SEASON_8_F1_D_1').title == 'Bones'
    assert DiscName('BONES_SEASON_8_F1_D_1').season == 8
    assert DiscName('BONES_SEASON_8_F1_D_1').discNumber == 1

    assert DiscName('BONES_SEASON_8_F1_D1').title == 'Bones'
    assert DiscName('BONES_SEASON_8_F1_D1').season == 8
    assert DiscName('BONES_SEASON_8_F1_D1').discNumber == 1

    assert DiscName('BONES_SEASON_7_DISC_1').title == 'Bones'
    assert DiscName('BONES_SEASON_7_DISC_1').season == 7
    assert DiscName('BONES_SEASON_7_DISC_1').discNumber == 1

    assert DiscName('bones_s7_d1').title == 'Bones'
    assert DiscName('bones_s7_d1').season == 7
    assert DiscName('bones_s7_d1').discNumber == 1

    assert DiscName('bones_season7_d1').title == 'Bones'
    assert DiscName('bones_season7_d1').season == 7
    assert DiscName('bones_season7_d1').discNumber == 1

    assert DiscName('bones_season_7_d1').title == 'Bones'
    assert DiscName('bones_season_7_d1').season == 7
    assert DiscName('bones_season_7_d1').discNumber == 1

    assert DiscName('bones_season_7_d_1').title == 'Bones'
    assert DiscName('bones_season_7_d_1').season == 7
    assert DiscName('bones_season_7_d_1').discNumber == 1
   
    assert DiscName('Frasier DiscNumber 1').title == 'Frasier'
    assert DiscName('Frasier DiscNumber 1').season == None
    assert DiscName('Frasier DiscNumber 1').discNumber == 1
   
    assert DiscName('Frasier Disc 2').title == 'Frasier'
    assert DiscName('Frasier Disc 2').season == None
    assert DiscName('Frasier Disc 2').discNumber == 2
   
    assert DiscName('Frasier Disc3').title == 'Frasier'
    assert DiscName('Frasier Disc3').season == None
    assert DiscName('Frasier Disc3').discNumber == 3
   
    assert DiscName('Frasier d4').title == 'Frasier'
    assert DiscName('Frasier d4').season == None
    assert DiscName('Frasier d4').discNumber == 4
    
    assert DiscName('My.Movie.3D.BluRay.1080p.AVC.TrueHD7.1-CHDBits.iso').title == 'My Movie'
    assert DiscName('My.Movie.2014.3D.BluRay.1080p.AVC.TrueHD7.1-CHDBits.iSo').title == 'My Movie 2014'
    assert DiscName('My.Movie.2014.3D.BluRay.720p.x264.DTS-MA-ac3.ISO').title == 'My Movie 2014'
    
    assert DiscName('My.Movie.2014.3D.BluRay.1080p.AVC.TrueHD7.1-CHDBits.iso').title == 'My Movie 2014'
 
    assert DiscName('My.Movie.2014.3D.BluRay.720p.x264.DTS-MA-ac3.ISO').title == 'My Movie 2014'
    assert DiscName('My.Movie.2014.3D.BluRay.1080p.AVC.TrueHD7.1-CHDBits.iso').title == 'My Movie 2014'

    assert DiscName('Heroes_Season_2_(Disc_1)').title == 'Heroes'
    assert DiscName('Heroes_Season_2_(Disc_1)').season == 2
    assert DiscName('Heroes_Season_2_(Disc_1)').discNumber == 1
    
    assert DiscName('red.hood.2010.dvdrip.xvid').title == 'Red Hood 2010'


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test()
