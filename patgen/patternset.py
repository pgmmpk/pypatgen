'''
Created on Mar 7, 2016

@author: mike
'''
from patgen import EMPTYSET


class PatternSet(list):

    def __init__(self):
        list.__init__(self)

    @property
    def maxchunk(self):
        if len(self) == 0:
            return 0
        
        return max(x.maxchunk for x in self)

    def hyphenate(self, word, margins):
        
        prediction = set()
        for i, layer in enumerate(self):
            if (i & 1) == 0:
                # hyphenation layer
                prediction.update(layer.predict(word, margins))
            else:
                # inhibiting layer
                prediction.difference_update(layer.predict(word, margins))
        
        return prediction
    
    def pattern_strings(self):
        keys = set()
        for layer in self:
            keys.update(layer.keys())
    
        for key in sorted(keys):
            controls = [0] * (len(key) + 1)
            level = 0
            for layer in self:
                level += 1
                for index in layer.get(key, EMPTYSET):
                    controls[index] = level
    
            out = []
            for i, c in enumerate(controls):
                if i > 0:
                    out.append(key[i-1])
                if c > 0:
                    out.append(str(c))
    
            yield ''.join(out)
    
    def errors(self, dictionary, margins):

        for word, hyphens in dictionary.items():
            prediction = self.hyphenate(word, margins=margins) 

            missed = hyphens - prediction
            false  = prediction - hyphens
            
            if missed or false:
                yield word, hyphens, missed, false

    def evaluate(self, dictionary, margins):
        
        num_missed = 0
        num_false = 0
        
        for word, _, missed, false in self.errors(dictionary, margins):
            w = dictionary.weights[word]
            num_missed += sum(w[i] for i in missed)
            num_false  += sum(w[i] for i in false)
        
        return num_missed, num_false
