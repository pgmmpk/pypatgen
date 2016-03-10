'''
Created on Mar 10, 2016

@author: mike
'''
import unittest
from patgen.patternset import PatternSet
from patgen.layer import Layer


class TestCompact(unittest.TestCase):
    
    def test(self):
        
        pset = PatternSet()
        pset.append(Layer(None, None, False))
        
        pset[0].update({'azhe.': {1}, 'zhe.': {0}})
        
        pset.compact()
        
        patterns = set(pset.pattern_strings())
        self.assertEqual(len(patterns), 1)