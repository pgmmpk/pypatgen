'''
Created on Mar 7, 2016

@author: mike
'''
from datetime import datetime
from patgen.patternset import PatternSet
import pickle
import os
from patgen.layer import Layer
from patgen import stagger_range


class Project:
    
    VERSION = '2016/03/07'

    def __init__(self, dictionary, margins=None, total_hyphens=None):
        
        self.dictionary = dictionary
        self.dictionary.make_all_missed()

        self.margins = margins or dictionary.compute_margins()
        self.total_hyphens = total_hyphens or dictionary.compute_total_hyphens()
        self.created = self.modified = datetime.now()
        self.patternset = PatternSet()

        # statistics
        self.missed = self.total_hyphens
        self.false = 0

    def __getstate__(self):
        return (
            self.VERSION, 
            self.created, 
            datetime.now(), 
            self.dictionary, 
            self.margins, 
            self.total_hyphens, 
            self.patternset, 
            self.missed, 
            self.false
        )
    
    def __setstate__(self, state):
        (
            version, 
            self.created, 
            self.modified, 
            self.dictionary, 
            self.margins, 
            self.total_hyphens, 
            self.patternset, 
            self.missed, 
            self.false
        ) = state
        
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

    def train_new_layer(self, patlen_range, selector):

        inhibiting = len(self.patternset) & 1
    
        layer = Layer(patlen_range, selector, inhibiting)
        self.patternset.append(layer)
        
        for patlen in stagger_range(patlen_range.start, patlen_range.end + 1):
            additions = layer.train(patlen, self.dictionary, self.margins)
            print('Selected %s patterns of length %s' % (len(additions), patlen))
    
        # evaluate
        missed, false = layer.apply_to_dictionary(inhibiting, self.dictionary, margins=self.margins)
        self.missed = missed
        self.false = false
        
        return layer
