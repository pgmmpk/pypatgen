'''
Created on Mar 7, 2016

@author: mike
'''
import unittest
from patgen.dictionary import Dictionary
from patgen.project import Project
from patgen.range import Range
from patgen.selector import Selector


class TestIntegration(unittest.TestCase):
    
    def test(self):

        dictionary = Dictionary.from_string('''
            lo-rem
            ip-sum
            do-l-or
            sit
            a-met
            con-sec-te-tur
            adi-pis-cing
            elit
            ves-ti-bu-l-um
            eu-is-mod
            di-am
            eg-et
            bi-b-en-d-um
            ''')

        project = Project(dictionary)

        rng = Range.parse('1-2')
        selector = Selector.parse('1:1:1')

        project.train_new_layer(rng, selector)

        self.assertEqual(1, len(project.patternset))
        
        self.assertEqual(project.missed, 0)
        self.assertEqual(project.false, 3)

        project.train_new_layer(rng, selector)

        self.assertEqual(2, len(project.patternset))
        
        self.assertEqual(project.missed, 0)
        self.assertEqual(project.false, 0)

        patterns = list(project.patternset.pattern_strings())
        self.assertEqual(patterns, [
            '.e2',
            '1a',
            '1a1m',
            '1b',
            '1b1e',
            'bi1',
            '1bu1',
            '1ci',
            'co2',
            'c1t',
            'di1',
            'do1',
            '1d1u',
            'ec1',
            'eg1',
            'e2l',
            '1en1',
            'es1',
            'e1t',
            'eu1',
            'g1',
            'g1e',
            'i1a',
            'i1b',
            'is1',
            '1l',
            '2li',
            '1lo1',
            '1l1u',
            '1m',
            '1me',
            '1mo',
            '2n1',
            'n1d1',
            '2n1s',
            'o1',
            'o1l1',
            'o2n1',
            'o1r',
            '1pi',
            'p1s2',
            '1r',
            '1re',
            's1c',
            '1se',
            's1m',
            's1t',
            '1s2u',
            '1t',
            '1te1',
            '1ti1',
            '1tu',
            'u1',
            'u1i',
            'u1l1',
            '1um'
        ])