'''
Created on Mar 7, 2016

@author: mike
'''
from patgen.dictionary import parse_dictionary_word, format_dictionary_word
import unittest


class TestDictionary(unittest.TestCase):
    
    def test_parse(self):
        
        text, hyphens, missed, false, weights = parse_dictionary_word('hy-phe-2n-a-tion')
        
        self.assertEqual(text, 'hyphenation')
        self.assertEqual(hyphens, {2, 5, 6, 7})
        self.assertEqual(missed, set())
        self.assertEqual(false, set())
        self.assertEqual(weights, {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1})

    def test_format(self):
        
        s = format_dictionary_word('hyphenation', {2, 5, 6, 7})

        self.assertEqual(s, 'hy-phe-n-a-tion')

    def test_format_weights(self):
        
        s = format_dictionary_word('hyphenation', {2, 5, 6, 7}, weights={0: 3, 1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 3, 10: 3, 11: 3})

        self.assertEqual(s, '3hy-phe-n-a-tion')