'''
Created on Mar 7, 2016

@author: mike
'''
from patgen import EMPTYSET, DIGITS
from patgen.suffix_array import SuffixArray


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
    
    def keys(self):
        keys = set()
        for layer in self:
            keys.update(layer.keys())
        return keys

    def pattern_strings(self):

        for key in sorted(self.keys()):
            control = self.get_pattern_control(key)
            
            if control:
                yield self.format_pattern(key, control)

    def get_pattern_control(self, key):

        control = {}
        for level0, layer in enumerate(self):
            for index in layer.get(key, EMPTYSET):
                control[index] = level0 + 1

        return control

    def set_pattern_control(self, key, control):
        for layer in self:
            layer[key].clear()
            
        for i, level in control.items():
            if level > 0:  # paranoid
                layer = self[level - 1]
                layer[key].add(i)

    def compact(self):
        patterns = {}

        for key in self.keys():
            patterns[key] = self.get_pattern_control(key)

        suffix_array = SuffixArray.build(patterns.keys())

        # patterns that are substrings of other patterns
        # can cancel longer pattern's control
        for key, control in patterns.items():
            for lkey, offset in suffix_array.superstrings(key):
                if lkey == key:
                    continue  # do not attempt to compact self!

                lcontrol = patterns[lkey]
                for i, val in control.items():
                    lval = lcontrol.get(offset + i, 0)
                    if 0 < lval <= val:
                        del lcontrol[offset + i] 

        for key, control in patterns.items():
            self.set_pattern_control(key, control)

    @staticmethod
    def format_pattern(key, control):
        out = []
        for i in range(len(key) + 1):
            if i > 0:
                out.append(key[i-1])
            c = control.get(i, 0)
            if c > 0:
                out.append(str(c))
        return ''.join(out)

    @staticmethod
    def parse_pattern(string):
        text = []
        control = {}
        
        for c in string:
            if c in DIGITS:
                control[len(text)] = int(c)
            else:
                text.append(c)

        return ''.join(text), control

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
