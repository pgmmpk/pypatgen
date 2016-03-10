'''
Created on Mar 7, 2016

@author: mike
'''
from patgen.margins import Margins

class Chunker:
    
    def __init__(self, chunklen, margins=Margins(1,1)):
        self.chunklen = chunklen
        self.margins = margins

    def __call__(self, word, hyphenpos):
        '''
        Takes word :word: and generates all chunks of the given length with
        hyphen position :hyphenpos:.
        
        margin_left sets the minimal length of word prefix where hyphenation is not allowed.
            this is the same as TeX's \lefthyphenmin
        margin_right sets the minimal length of word suffix where hyphention is not allowed.
            this is the same as TeX's \righthyphenmin
        
        Example:
            chunker = Chunker(2)
            chunker('mike', 2) will produce this sequence:
            0, ".m"
            1, "mi"
            2, "ik"
        '''
        if hyphenpos > len(word):
            return  # word is too short

        assert 0 <= hyphenpos <= len(word)
    
        word = '.' + word + '.'
        
        start = 0
        end = len(word) - self.chunklen + 1 # last valid offset
        
        start = max(start, self.margins.left+1-hyphenpos)
        end = min(end, len(word)-self.margins.right-hyphenpos)
        
        for i in range(start, end):
            yield i, word[i:i+self.chunklen]
