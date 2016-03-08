'''
Created on Mar 7, 2016

@author: mike
'''
from datetime import datetime
from patgen.patternset import PatternSet
import pickle
import os


class Project:
    
    VERSION = '2016/03/07'

    def __init__(self, dictionary, margins, total_hyphens):
        
        self.dictionary = dictionary
        self.margins = margins
        self.total_hyphens = total_hyphens
        self.created = self.modified = datetime.now()
        self.patternset = PatternSet()

    def __getstate__(self):
        return self.VERSION, self.created, datetime.now(), self.dictionary, self.margins, self.total_hyphens, self.patternset
    
    def __setstate__(self, state):
        version, self.created, self.modified, self.dictionary, self.margins, self.total_hyphens, self.patternset = state
        if version != self.VERSION:
            raise RuntimeError('Incompatible version: %s (expected %s)' % (version, self.VERSION))

    @classmethod
    def load(cls, filename):

        if not os.path.exists(filename):
            raise RuntimeError('Project file not found: %s' % filename)
        
        with open(filename, 'rb') as f:
            return pickle.load(f)

    def save(self, filename):
        
        with open(filename, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
