'''
Created on Feb 18, 2016

@author: mike
'''
import unittest
from patgen import chunker

class TestChunker(unittest.TestCase):
    
    def test1(self):
        
        chunks = set(x[1] for x in chunker('mike', chunklen=2, hyphen_position=1, margin_left=2, margin_right=2))
        
        self.assertEquals(chunks, {'ik'})

    def test2(self):
        
        chunks = set(x[1] for x in chunker('mike', chunklen=2, hyphen_position=0, margin_left=2, margin_right=2))
        
        self.assertEquals(chunks, {'ke'})

    def test3(self):
        
        chunks = set(x[1] for x in chunker('mike', chunklen=2, hyphen_position=2, margin_left=2, margin_right=2))
        
        self.assertEquals(chunks, {'mi'})

    def test4(self):
        
        chunks = set(x[1] for x in chunker('mike', chunklen=2, hyphen_position=1, margin_left=1, margin_right=1))
        
        self.assertEquals(chunks, {'mi', 'ik', 'ke'})
