'''
Created on Mar 9, 2016

@author: mike
'''
from bisect import bisect_left

class SuffixArray:
    def __init__(self, sarray):
        self._sarray = sarray
    
    @classmethod
    def build(cls, values):
        
        sarray = []
        for value in values:
            for suffix, offset in suffixes_with_offset(value):
                sarray.append( (suffix, value, offset) )

        sarray.sort()
        
        return SuffixArray(sarray)
    
    def superstrings(self, query):
        i = bisect_left(self._sarray, (query, '', 0))

        while i < len(self._sarray):
            entry = self._sarray[i]
            if not entry[0].startswith(query):
                break
            assert entry[1][entry[2]:].startswith(query)
            yield entry[1], entry[2]
            i += 1

def suffixes_with_offset(value):
    for i in range(len(value)-1):
        yield value[i:], i