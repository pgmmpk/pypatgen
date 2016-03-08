'''
Created on Feb 18, 2016

@author: mike
'''
from __future__ import print_function

import collections
import codecs
import pickle
import os
from datetime import datetime


EMPTYSET = frozenset()

MISSED_HYPHEN = '.'
FALSE_HYPHEN  = '*'
TRUE_HYPHEN   = '-'
NOT_A_HYPHEN  = ' '

DIGITS = '0123456789'


def stagger_range(start, end):
    middle = start + (end-start) // 2
    left = middle - 1
    right = middle + 1
    
    yield middle
    
    while left >= start or right < end:
        if left >= start:
            yield left
            left -= 1
        
        if right < end:
            yield right
            right += 1
