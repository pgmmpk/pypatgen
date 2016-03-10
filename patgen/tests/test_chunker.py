'''
Created on Feb 18, 2016

@author: mike
'''
import unittest
from patgen.chunker import Chunker
from patgen.margins import Margins


class TestChunker(unittest.TestCase):
    
    def test1(self):
        
        chunker = Chunker(2, Margins(2,2))
        
        chunks = set(chunker('mike', hyphenpos=1))
        
        self.assertEquals(chunks, {(2, 'ik')})

    def test2(self):
        
        chunker = Chunker(2, Margins(2,2))

        chunks = set(chunker('mike', hyphenpos=0))
        
        self.assertEquals(chunks, {(3, 'ke')})

    def test3(self):
        
        chunker = Chunker(2, Margins(2,2))

        chunks = set(chunker('mike', hyphenpos=2))
        
        self.assertEquals(chunks, {(1, 'mi')})

    def test4(self):
        
        chunker = Chunker(2, Margins(1,1))

        chunks = set(chunker('mike', hyphenpos=1))
        
        self.assertEquals(chunks, {(1, 'mi'), (2, 'ik'), (3, 'ke')})

    def test5(self):
        
        chunker = Chunker(3, Margins(1,1))
        
        chunks = set(chunker('word', hyphenpos=1))

        self.assertEquals(chunks, {(1, 'wor'), (2, 'ord'), (3, 'rd.')})
        