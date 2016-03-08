'''
Created on Mar 7, 2016

@author: mike
'''
import collections


class Selector(collections.namedtuple('_Selector', ['good_weight', 'bad_weight', 'threshold'])):

    @classmethod
    def parse(cls, selector):
        parts = selector.split(':')
        
        if len(parts) != 3:
            raise ValueError('selector format error: expect three values delimitered with a senicolon, e.g. "1:2:10". Got: %s' % selector)

        return cls(*tuple(float(x) for x in parts))
    
    def select(self, num_good, num_bad):
        return num_good * self.good_weight - num_bad * self.bad_weight >= self.threshold

    def __repr__(self):
        return '%s:%s:%s' % self
