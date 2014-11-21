#!/usr/bin/env python
# -*- coding: utf-8 -*-


import imp
import logging
import difflib


'''Code used from http://ginstrom.com/scribbles/2007/12/01/fuzzy-substring-matching-with-levenshtein-distance-in-python/ '''
def distanceBetweenStrings(needle, haystack):
        
    """Calculates the fuzzy match of needle in haystack,
    using a modified version of the Levenshtein distance
    algorithm.
    The function is modified from the levenshtein function
    in the bktree module by Adam Hupp"""

    doesLevenshteinModuleExist = False

    m, n = len(needle), len(haystack)

    # base cases
    if m == 1:
        return not needle in haystack
    if not n:
        return m

    row1 = [0] * (n+1)
    for i in range(0,m):
        row2 = [i+1]
        for j in range(0,n):
            cost = ( needle[i] != haystack[j] )

            row2.append( min(row1[j+1]+1, # deletion
                               row2[j]+1, #insertion
                               row1[j]+cost) #substitution
                           )
        row1 = row2
    return min(row1)


def matchRatio(textA,textB,quickMatch=False):
    curMatchRatio = 0.0
    
    diffMatches = difflib.SequenceMatcher(None,textA,textB)
    quickRatio = diffMatches.ratio()
    logging.debug('Quick match ratio:' + str(quickRatio))
        
    '''Check ratio is sufficient to do a full scan. Dont do a full scan if difflib is telling us its 92% match ratio'''
    if (quickRatio > 0.02) and (quickRatio < 0.92) and (not quickMatch):
        distance = distanceBetweenStrings(textA,textB)
        curMatchRatio = float((len(textA)-distance))/float(len(textA))
        return curMatchRatio

    else:
        
        matchingBlocks = diffMatches.get_matching_blocks()
        
        for match in matchingBlocks:
            matchSize = match[2]
            matchIsPercentageOfString = float(matchSize)/float(len(textA))
            curMatchRatio += matchIsPercentageOfString

        stringDistanceTotal = 0
        deltaATotal = ''
        deltaBTotal = ''
            
        for i in range(1,len(matchingBlocks)):
            matchingBlockA = matchingBlocks[i-1]
            matchingBlockB = matchingBlocks[i]
            blockASize = matchingBlockA[2]
            blockBSize = matchingBlockB[2]
            blockATextAOffset = matchingBlockA[0]
            blockATextBOffset = matchingBlockA[1]
            blockBTextAOffset = matchingBlockB[0]
            blockBTextBOffset = matchingBlockB[1]

            deltaTextA = textA[blockATextAOffset+blockASize:blockBTextAOffset]
            deltaTextB = textB[blockATextBOffset+blockASize:blockBTextBOffset]
            
            deltaATotal += deltaTextA
            deltaBTotal += deltaTextB
            
        #break up the delta strings into 1000 char blocks for easier (computationaly) comparison
        deltaABlocks = [deltaATotal[i:i+4000] for i in range(0, len(deltaATotal), 4000)]
        deltaBBlocks = [deltaBTotal[i:i+4000] for i in range(0, len(deltaBTotal), 4000)]
        
        for i in range(0,min(len(deltaABlocks),len(deltaBBlocks))):
            deltaA = deltaABlocks[i]
            deltaB = deltaBBlocks[i]

            distance = float(distanceBetweenStrings(deltaA,deltaB))
            deltaALen = float(len(deltaA))
            matchRatio = (deltaALen - distance)/deltaALen
            percentageOfString = deltaALen / float(len(textA))
            ratioToAdd = percentageOfString * matchRatio
            curMatchRatio += ratioToAdd

    logging.debug('Returning ratio: ' + str(curMatchRatio))
    return curMatchRatio
