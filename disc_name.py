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
        self.title = title
        self.season = season
        self.discNumber = disc

        self.formattedName = self.title
        
        if self.season is not None:
            self.formattedName = self.formattedName + ' - Season ' + str(self.season)
        
        if self.discNumber is not None:
            self.formattedName = self.formattedName + ' - DiscNumber ' + str(self.discNumber)

    @staticmethod
    def _removeUnnecessaryCharsFromTitle(title):
        tmpName = title

        # Clean up
        tmpName = tmpName.replace("\"", "")
        tmpName = tmpName.replace("_", " ")
        tmpName = tmpName.replace("  ", " ")
    
        regexRemove = [r'(?i)(?:extended|special|ultimate|limited|collectors|standard)?[_| ]?(?:3d|retail|dvd|bluray|blu-ray)?[ |_]?edition',
                       r'(?i)[_| ]?pal$',
                       r'(?i)[_| ]?ntsc$',
                       r'(?i)[_| ]?dvd$',
                       r'(?i)[_| ]?blu[\-|_| ]?ray$',
                       r'(?i)[_| ]?retail$',
                       r'(?i)[_| ]?3d$']

        didRegexMatch = True
    
        while didRegexMatch:
            didRegexMatch = False

            for regTest in regexRemove:
                matchResults = re.search(regTest,tmpName)
                if matchResults != None:
                    tmpName = re.sub(regTest,'',tmpName)
                    didRegexMatch = True
    
        #capitalize first letter of each word
        tmpName = tmpName.title()

        return tmpName.strip()


    @staticmethod
    def titleSeasonAndDiscFromDiscName(disc_name):
        tmpName = disc_name
    
        logging.info('Removed unnecessary chars to \'' + tmpName + '\'')
    
        #first matching group - season, 2nd - disc number
        regexSeasonDisk = [r'(?i)s([\d{1,2}])_?d([\d{1,2}])',
                           r'(?:season|series)_?([\d{1,2}])_?(?:disc|disk|d)_?([\d{1,2}])',
                           r'(?i)(?:s|series|season)[-|_| ]?([\d{1,2}]).*(?:d|disc|disk)[-|_| ]?([\d{1,2}])',
                           r'(?i)([\d{1,2}])[-|_| ]([\d{1,2}])']

        season = None
        disc = None

        for regTest in regexSeasonDisk:
            regexSearch = re.search(regTest,tmpName)

            if regexSearch != None:
                logging.debug('Matched regex: ' + regTest)
                matchGroups = regexSearch.groups()
                season = int( matchGroups[0] )
                disc = int( matchGroups[1] )
                tmpName = re.sub(regTest,'',tmpName)
                didRegexMatch = True    
            
        #look for numbers prepended to the end of the last word and add space
        numberWhitespacing = r'\b(\w+)(\d+)\b$'
        numberWhitespacingRE = re.compile(numberWhitespacing)
        
        if len(numberWhitespacingRE.findall(tmpName)) > 0:
            whitespaceSearch = numberWhitespacingRE.search(tmpName)
            tmpName = re.sub(numberWhitespacing,whitespaceSearch.groups()[0] + ' ' + whitespaceSearch.groups()[1],tmpName)
            
        tmpName = tmpName.strip()
    
        #if its a short name, chances are its an acronym i.e CSI
        if len(tmpName) <= 3:
            tmpName = tmpName.upper()

        logging.info('Converted disc name: ' +disc_name+ ' to ' + tmpName + ', season:' + str(season) + ', disc:' + str(disc))

        return [tmpName,season,disc]


def test():

    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_PAL')
    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_NTSC')
    
    expectedText2 = 'Die Hard'
 
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('Die Hard Limited Edition')
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('Die Hard limited_Edition')
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('Die Hard Special Edition')
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('Die Hard special_edition')
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('Die Hard Extended Edition')
    assert expectedText2 == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_EXTENDED_EDITION')

    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_SPECIAL_3D_EDITION')
    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_RETAIL')
    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_3D_RETAIL')
    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_DVD')
    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_BLURAY')
    assert 'Die Hard' == DiscName._removeUnnecessaryCharsFromTitle('DIE_HARD_BLU_RAY')

    assert 'Pals' == DiscName._removeUnnecessaryCharsFromTitle('PALS')
    assert 'Pals' == DiscName._removeUnnecessaryCharsFromTitle('pals')

    assert DiscName('DIE_HARD_SPECIAL_3D_EDITION').title == 'Die Hard'
    assert DiscName('DIE_HARD_SPECIAL_3D_EDITION').season == None
    assert DiscName('DIE_HARD_SPECIAL_3D_EDITION').discNumber == None

    assert DiscName('AVATAR_3D_EDITION').title == 'Avatar'
    assert DiscName('AVATAR_3D_EDITION').season == None
    assert DiscName('AVATAR_3D_EDITION').discNumber == None

    assert DiscName('The Good, the Bad and the Ugly').title == 'The Good, The Bad And The Ugly'
    assert DiscName('The Good, the Bad and the Ugly').season == None
    assert DiscName('The Good, the Bad and the Ugly').discNumber == None

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
    


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test()
