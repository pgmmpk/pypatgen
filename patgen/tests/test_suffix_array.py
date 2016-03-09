'''
Created on Mar 9, 2016

@author: mike
'''
import unittest
from patgen.suffix_array import SuffixArray


class TestSuffixArray(unittest.TestCase):
    
    def test(self):
        
        sa = SuffixArray.build(['aardvak', 'vakula', 'dvorzak', 'orc'])
        
        hits = set(sa.superstrings('or'))
        self.assertEqual(hits, {('dvorzak', 2), ('orc', 0)})
