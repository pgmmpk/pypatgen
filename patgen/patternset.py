'''
Created on Mar 7, 2016

@author: mike
'''


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
