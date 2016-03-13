'''
Created on Mar 7, 2016

@author: mike
'''
import collections
from patgen import EMPTYSET


class Layer:
    
    @property
    def maxchunk(self):
        return self.patlen_range.end

    def __init__(self, patlen_range, selector, inhibiting):
        self.patlen_range = patlen_range
        self.selector = selector
        self.inhibiting = inhibiting
        
        self._data = collections.defaultdict(set)
    
    def __getitem__(self, i):
        return self._data[i]
    
    def get(self, i, defaultval=None):
        return self._data.get(i, defaultval)

    def __len__(self):
        return len(self._data)
    
    def keys(self):
        return self._data.keys()
    
    def items(self):
        return self._data.items()
    
    def values(self):
        return self._data.values()
    
    def update(self, vals):
        self._data.update(vals)
    
    def __repr__(self):
        return '<Layer patlen_range=%r, selector=%r, data=%r>' % (self.patlen_range, self.selector, self._data)
    
    def compute_num_patterns(self):
        return sum(len(val) for val in self.values())

    def train(self, patlen, dictionary, margins):
        patterns = collections.defaultdict(set)
        for position in range(0, patlen+1):
            for ch, num_good, num_bad in dictionary.generate_pattern_statistics(
                                                                            self.inhibiting, 
                                                                            patlen, 
                                                                            position, 
                                                                            margins=margins):
                    if self.selector.select(num_good, num_bad):
                        patterns[ch].add(position)

        self.update(patterns)
        return patterns

    def predict(self, word, margins):
        '''
        Applies a single pattern layer set to the word
        
        Result is the set of indices that patterset "suggested".
        For hyphenation patternsets, these are indices where hyphenation is predicted.
        For inhibiting patternsets, these are indices where hyphenation is inhibited.
        '''
        word = '.' + word + '.'
    
        prediction = set()
    
        for chunklen in range(1, self.maxchunk+1):
            for start in range(0, len(word) - chunklen + 1):
                ch = word[start: start+chunklen]
                allowed = self._data.get(ch, EMPTYSET)
                for index in allowed:
                    if start + index > margins.left and start+index <= len(word) - 1 - margins.right:
                        prediction.add(index + start - 1)  # -1 corrects for the added front padding
    
        return prediction

    def apply_to_dictionary(self, inhibiting, dictionary, margins):
        num_missed = 0
        num_false  = 0
    
        for word, hyphens in dictionary.items():
            predicted = self.predict(word, margins=margins)
            
            missed = dictionary.missed[word]
            false  = dictionary.false[word]
            weights = dictionary.weights[word]
    
            if not inhibiting:
                missed.difference_update(predicted)
                false.update(predicted - hyphens)
            else:
                false.difference_update(predicted)
                missed.update(hyphens & (predicted - missed))
    
            num_missed += sum(weights[i] for i in missed)
            num_false += sum(weights[i] for i in false)
        
        return num_missed, num_false
