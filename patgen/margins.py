'''
Created on Mar 7, 2016

@author: mike
'''
import collections

# hyphenation margins
class Margins(collections.namedtuple('_Margins', ['left', 'right'])):

    @classmethod
    def parse(cls, margins):
        parts = margins.split(',')

        if len(parts) != 2:
            raise ValueError('margins format error: expect two numbers delimitered with a comma, e.g. "1,1". Got: %s' % margins)
    
        return Margins(*tuple(int(x) for x in parts))
    
    def __repr__(self):
        return '%s,%s' % self
