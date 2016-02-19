'''
Created on Feb 18, 2016

@author: mike
'''
import collections
import codecs
import pickle
import os
from datetime import datetime


EMPTYSET = frozenset()

MISSED_HYPHEN = '.'
FALSE_HYPHEN  = '*'
TRUE_HYPHEN   = '-'
NOT_A_HYPHEN  = ' '

def chunker(word, *, chunklen, hyphen_position, margin_left=1, margin_right=1):
    '''
    Takes word "word" and generates all chunks of the given length "chunklen" with
    hyphen position "hyphen_position".
    
    margin_left sets the minimal length of word prefix where hyphenation is not allowed.
        this is the same as TeX's \lefthyphenmin
    margin_right sets the minimal length of word suffix where hyphention is not allowed.
        this is the same as TeX's \righthyphenmin
    
    Example:
        chunker('mike', 2, 2) will produce this sequence:
        ".m"
        "mi"
        "ik"
    '''
    
    word = '.' + word + '.'
    
    start = 0
    end = len(word) - chunklen  # last valid offset
    
    start = max(start, margin_left+1-hyphen_position)
    end = min(end, len(word)-margin_right-hyphen_position)
    
    for i in range(start, end):
        #if i + hyphen_position < margin_left + 1:
        #    continue
        #if i + hyphen_position > len(word) - margin_right - 1:
        #    continue 
        yield i, word[i:i+chunklen]


def parse_dictionary_word(word):
        text = []
        hyphens = [NOT_A_HYPHEN] * (len(word) + 1)
        
        special_seen = False
        for c in word:
            if not special_seen:
                if c in (TRUE_HYPHEN, MISSED_HYPHEN, FALSE_HYPHEN):
                    hyphens[len(text)] = c
                    special_seen = True
                    continue

            special_seen = False
            text.append(c)

        return ''.join(text).lower(), hyphens

def load_dictionary(filename):

    dictionary = collections.OrderedDict()
    with codecs.open(filename, 'r', 'utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):  # comment line
                continue
            
            text, hyphens = parse_dictionary_word(line)
            dictionary[text] = hyphens
    
    return dictionary


def format_hyphenation(word, hyphens, true_hyphens=None):
    if true_hyphens is not None:
        missed = true_hyphens - hyphens
        false  = hyphens - true_hyphens
    else:
        missed = EMPTYSET
        false  = EMPTYSET

    out = []
    for i in range(len(word)+1):
        if i > 0:
            out.append(word[i-1])
        if i in missed:
            out.append(MISSED_HYPHEN)
        elif i in false:
            out.append(FALSE_HYPHEN)
        elif i in hyphens:
            out.append(TRUE_HYPHEN)

    return ''.join(out)


def load_project(filename):

    if not os.path.exists(filename):
        raise RuntimeError('Project file not found: %s' % filename)

    with open(filename, 'rb') as f:
        return pickle.load(f)


def save_project(project, filename):
    project.modified = datetime.now()
    with open(filename, 'wb') as f:
        pickle.dump(project, f, pickle.HIGHEST_PROTOCOL)


def parse_selector(selector):
    '''
    Parses pattern selector value.
    
    Pattern selector is a triplet of integers:
        - good_weight
        - bad_weight
        - threshold
    
    We encode it in a single string with semicolon as a delimiter. For example, selector "1:3:10" means
    that good_weight=1, bad_weight=3, and threshold=10.
    
    This function parses such strings and return 3-tuple of (good_weight, bad_weight, threshold).
    
    Selector is used to select "good" patterns. For that we check how a particular pattern performs on
    the whole dictionary. Such a statistics has two numbers: good_hits and bad_hits. Fomer being the number when 
    pattern correctly predicted hyphen position, and latter being the number of times it fired an incorrect prediction.
    
    Selection criteria is:
    
        good_weight * good_hits - bad_weight * bad_hits >= threshold
    '''
    parts = selector.split(':')
    
    if len(parts) != 3:
        raise ValueError('selector format error: expect three values delimitered with a senicolon, e.g. "1:2:10". Got: %s' % selector)
    
    return tuple(float(x) for x in parts)


def format_dictionary_word(text, true_hyphens, predicted_hyphens=None):
    if predicted_hyphens is None:
        predicted_hyphens = set(i for i in range(len(true_hyphens)) if true_hyphens[i] in (TRUE_HYPHEN, MISSED_HYPHEN))
    out = []

    for i in range(len(text)+1):
        if i > 0:
            out.append(text[i-1])

        if i in predicted_hyphens:
            if true_hyphens[i] in (TRUE_HYPHEN, MISSED_HYPHEN):
                out.append(TRUE_HYPHEN)
            else:
                out.append(FALSE_HYPHEN)
        else:
            if true_hyphens[i] in (TRUE_HYPHEN, MISSED_HYPHEN):
                out.append(MISSED_HYPHEN)

    return ''.join(out)


def generate_pattern_statistics(dictionary, inhibiting, patt_len, hyphen_position, *, margin_left=1, margin_right=1):
    '''
    Takes a dictionary of word hyphenations and
    1. Finds all possible patterns of a given length and given hyphen position, and
    2. Computes performance of each pattern - how many times pattern finds "ggod" hyphen, and how many time it errors
    '''
    
    good = collections.defaultdict(int)
    bad  = collections.defaultdict(int)

    for word, hyphens in dictionary.items():

        for start, ch in chunker(word, chunklen=patt_len, hyphen_position=hyphen_position, margin_left=margin_left, margin_right=margin_right):
            code = hyphens[start + hyphen_position - 1]
            if not inhibiting:
                if code == MISSED_HYPHEN:
                    good[ch] += 1
                elif code == NOT_A_HYPHEN:
                    bad[ch] += 1
            else:
                if code == FALSE_HYPHEN:
                    good[ch] += 1
                elif code == TRUE_HYPHEN:
                    bad[ch] += 1

    return [(ch, good[ch], bad[ch]) for ch in sorted(set(good.keys()) | set(bad.keys()))]


def evaluate_pattern_set(patternset, inhibiting, dictionary, *, margin_left=1, margin_right=1):
    
    maxchunk = max(len(x) for x in patternset.keys()) if patternset else 0

    for word, hyphens in dictionary.items():
        predicted = apply_pattern_set(patternset, word, maxchunk, margin_left=margin_left, margin_right=margin_right)

        if not inhibiting:
            for i in range(len(hyphens)):
                if i in predicted:
                    if hyphens[i] == MISSED_HYPHEN:
                        hyphens[i] = TRUE_HYPHEN
                    elif hyphens[i] == NOT_A_HYPHEN:
                        hyphens[i] = FALSE_HYPHEN
        else:
            for i in range(len(hyphens)):
                if i in predicted:
                    if hyphens[i] == TRUE_HYPHEN:
                        hyphens[i] = MISSED_HYPHEN
                    elif hyphens[i] == FALSE_HYPHEN:
                        hyphens[i] = NOT_A_HYPHEN
            

def apply_pattern_set(patternset, word, maxchunk, *, margin_left=1, margin_right=1):
    '''
    Applies a single pattern set to the word
    
    Result is the set of indices that patterset "suggested".
    For hyphenation patternsets, these are indices where hyphenation is predicted.
    For inhibiting patternsets, these are indices where hyphenation is inhibited.
    '''
    word = '.' + word + '.'

    prediction = set()

    for chunklen in range(1, maxchunk+1):
        for start in range(0, len(word) - chunklen):
            ch = word[start: start+chunklen]
            allowed = patternset.get(ch, EMPTYSET)
            for index in allowed:
                if start + index > margin_left and start+index <= len(word) - 1 - margin_right:
                    prediction.add(index + start - 1)  # -1 corrects for the added front padding

    return prediction


def apply_patterns(patterns, word, maxchunk, *, margin_left=1, margin_right=1):
    '''
    Applies patterns to a word.
    
    Patterns "patterns" is a list of pattern sets. Hyphenation and inhibiting patternsets are
    alternating: firt element in the list is a hyphenation pattern set, next one is inhibiting, and so on.
    In other words, even list slots contain hyphenation patterns. Odd ones contain inhibiting patterns.
    '''
    hyphens = set()
    level = 0
    for patternset in patterns:
        level += 1
        
        prediction = apply_pattern_set(patternset, word, maxchunk=maxchunk, margin_left=margin_left, margin_right=margin_right)
        
        if level & 1:
            # hyphenation level
            hyphens.update(prediction)
        else:
            hyphens.difference_update(prediction)
    
    return hyphens


def evaluate_dictionary(patterns, dictionary, *, margin_left=1, margin_right=1):
    '''
    Evaluates the performance of patterns on a dictionary.
    
    Returns number of hyphens in the dictionary, number of hyphens that patterns missed, and
    number of hyphens that were incorrectly introduced by the patterns.
    '''
    
    maxchunk = 0
    for patternset in patterns:
        if patternset:
            maxchunk = max(maxchunk, max(len(x) for x in patternset.keys()))
    
    total = 0
    missed = 0
    false = 0
    for word, hyphens in dictionary.items():
        
        prediction = apply_patterns(patterns, word, maxchunk, margin_left=margin_left, margin_right=margin_right)
        
        for i, code in enumerate(hyphens):
            if code in (TRUE_HYPHEN, MISSED_HYPHEN):
                total += 1
                if i not in prediction:
                    missed += 1
            else:
                if i in prediction:
                    false += 1
    
    return total, missed, false


def stagger_range(start, end):
    middle = start + (end-start) // 2
    left = middle - 1
    right = middle + 1
    
    yield middle
    
    while left >= start or right < end:
        if left >= start:
            yield left
            left -= 1
        
        if right < end:
            yield right
            right += 1


def compute_dictionary_errors(patterns, dictionary, *, margin_left=1, margin_right=1):
    maxchunk = 0
    for patternset in patterns:
        if patternset:
            maxchunk = max(maxchunk, max(len(x) for x in patternset.keys()))

    for word, hyphens in dictionary.items():
        prediction = apply_patterns(patterns, word, maxchunk, margin_left=margin_left, margin_right=margin_right)

        true_hyphens = set(i for i,h in enumerate(hyphens) if h in (TRUE_HYPHEN, MISSED_HYPHEN))
        if prediction != true_hyphens:
            yield word, prediction