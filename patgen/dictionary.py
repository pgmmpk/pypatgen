'''
Created on Mar 7, 2016

@author: mike
'''
import collections
import codecs
from patgen import FALSE_HYPHEN, MISSED_HYPHEN, TRUE_HYPHEN, DIGITS
from patgen.margins import Margins
from patgen.chunker import Chunker


class Dictionary:
    ''' Hyphenation dictionary.
    Holds set of allowed hyphenation positions for each word.
    Additionally, can store hyphenation errors (missed and false) and hyphenation weights
    '''
    
    def __init__(self):
        self._hyphens = collections.OrderedDict()
        self._weights = {}
        self._missed = {}
        self._false = {}

    @property
    def weights(self):
        return self._weights
    
    @property
    def missed(self):
        return self._missed

    @property
    def false(self):
        return self._false

    def __getitem__(self, key):
        return self._hyphens[key]
    
    def __setitems__(self, key, val):
        self._hyphens[key] = val
    
    def keys(self):
        return self._hyphens.keys()
    
    def items(self):
        return self._hyphens.items()
    
    def values(self):
        return self._hyphens.values()
    
    def compute_total_hyphens(self):
        return sum(len(h) for h in self.values())

    def compute_margins(self):
        margin_left = 1000
        margin_right = 1000
        for word, hyphen in self.items():
            if hyphen:
                hmin = min(hyphen)
                hmax = max(hyphen)
                margin_left = min(margin_left, hmin)
                margin_right = min(margin_right, len(word) - hmax)

        return Margins(margin_left, margin_right)

    def make_all_missed(self):
        for word in self.keys():
            self.missed[word].clear()
            self.missed[word].update(self[word])  # all hyphens are initially missing
            self.false[word].clear()

    @classmethod
    def load(cls, filename):

        with codecs.open(filename, 'r', 'utf-8') as f:
            return cls.from_string(f.read())
    
    @classmethod
    def from_string(cls, string):
        dictionary = cls()
        for line in string.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):  # comment line
                continue

            text, hyphens, missed, false, weight = parse_dictionary_word(line)
            dictionary._hyphens[text] = hyphens
            dictionary._weights[text] = weight
            dictionary._missed[text] = missed
            dictionary._false[text] = false

        return dictionary
    
    def save(self, filename):

        with codecs.open(filename, 'w', 'utf-8') as f:
            
            for word, hyphens in self._hyphens.items():
                w = self._weights[word]
                
                f.write(format_dictionary_word(word, hyphens, w))
                f.write('\n')

    def generate_pattern_statistics(self, inhibiting, patt_len, hyphen_position, margins):
        '''
        Takes a dictionary of word hyphenations and
        1. Finds all possible patterns of a given length and given hyphen position, and
        2. Computes performance of each pattern - how many times pattern finds "good" hyphen, and how many time it errors
        '''
        chunker = Chunker(patt_len, margins=margins)
        
        good = collections.defaultdict(int)
        bad  = collections.defaultdict(int)
    
        for word in self.keys():
            hyphens = self[word]
            missed  = self.missed[word]
            false   = self.false[word]
            weight  = self.weights[word]
    
            for start, ch in chunker(word, hyphenpos=hyphen_position):
                index = start + hyphen_position - 1
                w     = weight[start + hyphen_position - 1]
                if not inhibiting:
                    if index in missed:
                        good[ch] += w
                    elif index not in hyphens:
                        bad[ch] += w
                else:
                    if index in  false:
                        good[ch] += w
                    elif index in hyphens and index not in missed:
                        bad[ch] += w
        
        ##print('.x', len([x for x in sorted(set(good.keys()) | set(bad.keys())) if x.startswith('.') ]))
        ##print('x.', len([x for x in sorted(set(good.keys()) | set(bad.keys())) if x.endswith('.') ]))
    
        return [(ch, good[ch], bad[ch]) for ch in sorted(set(good.keys()) | set(bad.keys()))]


def parse_dictionary_word(word):

    text = []
    weights = {}
    hyphens = set()
    missed = set()
    false = set()
    
    default_weight = 1
    if word[0] in DIGITS:
        default_weight = int(word[0])

    weights[0] = default_weight

    for c in word:
        if c == TRUE_HYPHEN:
            hyphens.add(len(text))
        elif c == MISSED_HYPHEN:
            hyphens.add(len(text))
            missed.add(len(text))
        elif c == FALSE_HYPHEN:
            false.add(len(text))
        elif c in DIGITS:
            weights[len(text)] = int(c)
        else:
            text.append(c)
            weights[len(text)] = default_weight

    return ''.join(text).lower(), hyphens, missed, false, weights


def format_dictionary_word(word, hyphens, missed=None, false=None, weights=None):
    text = []

    for i in range(len(word) + 1):
        if i > 0:
            text.append(word[i-1])

        if false is not None and i in false:
            text.append(FALSE_HYPHEN)
        elif missed is not None and i in missed:
            text.append(MISSED_HYPHEN)
        elif i in hyphens:
            text.append(TRUE_HYPHEN)

        if weights is not None:
            if i == 0:
                if weights[0] > 1:
                    text.append(str(weights[0]))
            elif weights[i] != weights[0]:
                text.append(str(weights[i]))

    return ''.join(text)


def format_word_as_pattern(word, missed=None, false=None):
    text = []

    for i in range(len(word) + 1):
        if i > 0:
            text.append(word[i-1])

        if false is not None and i in false:
            text.append('8')
        elif missed is not None and i in missed:
            text.append('7')

    return '.' + ''.join(text) + '.'
