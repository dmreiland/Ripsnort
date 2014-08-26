#!/usr/bin/env python
# -*- coding: utf-8 -*-


import imp
import logging


'''Code used from http://ginstrom.com/scribbles/2007/12/01/fuzzy-substring-matching-with-levenshtein-distance-in-python/ '''
def distanceBetweenStrings(needle, haystack):
        
    """Calculates the fuzzy match of needle in haystack,
    using a modified version of the Levenshtein distance
    algorithm.
    The function is modified from the levenshtein function
    in the bktree module by Adam Hupp"""

    doesLevenshteinModuleExist = False

    try:
        imp.find_module('editdist')
        doesLevenshteinModuleExist = True
    except ImportError:
        pass
    
    if doesLevenshteinModuleExist:
        import editdist
        return editdist.distance(needle,haystack)
    else:
        logging.warn('Using local levenshtein calculation. Recommend installing \'editdist\' module to improve performance (https://pypi.python.org/pypi/editdist/0.1) this may take some time, please be patient')

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
