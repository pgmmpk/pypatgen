'''
Created on Mar 7, 2016

@author: mike
'''
import collections


class Range(collections.namedtuple('_Range', ['start', 'end'])):
    
    @classmethod
    def parse(cls, rng):
        parts = rng.split('-')
        
        if len(parts) != 2:
            raise ValueError('failed to parse Range: expect two integers delimitered with a dash, e.g. "1-3". Got: %s' % rng)
        
        return cls(*tuple(int(x) for x in parts))
    
    def __repr__(self):
        return '%s-%s' % self
