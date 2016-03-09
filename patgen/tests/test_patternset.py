'''
Created on Mar 9, 2016

@author: mike
'''
import unittest
from patgen.patternset import PatternSet



class TestPatternSet(unittest.TestCase):
    
    def test_format_pattern(self):
        
        s = PatternSet.format_pattern('hello', {2: 2, 3: 1})
        
        self.assertEqual(s, 'he2l1lo')