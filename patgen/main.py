'''
Created on Feb 16, 2016

@author: mike
'''
from __future__ import print_function

import os
import codecs
import collections
import datetime
from patgen import load_dictionary, save_project, load_project, parse_selector,\
    stagger_range, generate_pattern_statistics, evaluate_pattern_set, EMPTYSET,\
    compute_dictionary_errors, format_dictionary_word,\
    TRUE_HYPHEN, MISSED_HYPHEN, FALSE_HYPHEN, NOT_A_HYPHEN, apply_patterns,\
    format_hyphenation, parse_margins
import sys


class SimpleNamespace:
    
    def __init__(self, **kav):
        for name, value in kav.items():
            setattr(self, name, value)

def main_new(args):
    
    if os.path.exists(args.project):
        print('Project file already exists! Use different name or delete old project first. File %s' % args.project)
        return -1
    
    if not os.path.exists(args.dictionary):
        print('Dictionary file not found', args.dictionary)
        return -1
    
    dictionary, weights = load_dictionary(args.dictionary, ignore_weights=args.ignore_weights)
    for hyphen in dictionary.values():
        for i in range(len(hyphen)):
            if hyphen[i] == TRUE_HYPHEN:
                hyphen[i] = MISSED_HYPHEN
            elif hyphen[i] == FALSE_HYPHEN:
                hyphen[i] = NOT_A_HYPHEN

    if args.margins is None:
        print('Automatically detecting hyphenation margins (from dictionary)')
        margin_left = 1000
        margin_right = 1000
        for hyphen in dictionary.values():
            for i in range(len(hyphen)):
                if hyphen[i] != NOT_A_HYPHEN:
                    margin_left = min(margin_left, i)
                    margin_right = min(margin_right, len(hyphen) - 1 - i)
    else:
        margin_left, margin_right = parse_margins(args.margins)

    total_hyphens = 0
    for word, hyphens in dictionary.items():
        weight = weights[word]
        total_hyphens += count_hyphens(hyphens, weight)
        total_hyphens += count_missed(hyphens, weight)
    
    project = SimpleNamespace(
            dictionary=dictionary,
            weights=weights,
            margin_left=margin_left,
            margin_right=margin_right,
            ignore_weights=args.ignore_weights,
            total_hyphens=total_hyphens,
            patterns=[],
            params=[],
            created=datetime.datetime.now(),
            modified=datetime.datetime.now()
        )
    
    save_project(project, args.project)
    
    print('Created project', args.project, 'from dictionary', args.dictionary)
    print()
    
    return main_show(args)


def main_show(args):
    
    if not os.path.exists(args.project):
        print('Project file not found:', args.project)
        return -1
    
    project = load_project(args.project)
    
    print('Project file', args.project)
    print('\tcreated:', project.created)
    print('\tlast modified:', project.modified)
    print('\tmargin_left:', project.margin_left)
    print('\tmargin_right:', project.margin_right)
    print('\tdictionary size:', len(project.dictionary))
    if project.ignore_weights:
        print('\tdictionary weights were ignored (-i flag active)')
    print('\ttotal hyphens: (weighted)', project.total_hyphens)
    print('\tnumber of pattern levels:', len(project.patterns))
    
    for i, patternset in enumerate(project.patterns):
        if i & 1 == 0:
            print((i+1), 'HYPHENATING patternset, num patterns:', len(patternset))
        else:
            print((i+1), 'INHIBITING patternset, num patterns:', len(patternset))
        params = project.params[i]
        print('\tTrained with: range %s, selector %s' % (params.range, params.selector))

    return 0


def main_train(args):
    
    good_weight, bad_weight, threshold = parse_selector(args.selector)

    project = load_project(args.project)

    inhibiting = False
    if len(project.patterns) & 1:
        print('Training inhibiting patterns (level=%s)' % (len(project.patterns)+1))
        inhibiting = True
    else:
        print('Training hyphenation patterns (level=%s)' % (len(project.patterns)+1))
    
    min_pattern_length, max_pattern_length = parse_margins(args.range)

    print('\trange of pattern lengths: %s..%s' % (min_pattern_length, max_pattern_length))
    print('\tselector:', args.selector)
    
    total_hyphens = project.total_hyphens

    patternset = collections.defaultdict(set)
    for pattlen in stagger_range(min_pattern_length, max_pattern_length+1):
        for position in range(0, pattlen+1):
            for ch, num_good, num_bad in generate_pattern_statistics(project.dictionary,
                                                                    project.weights,
                                                                    inhibiting, 
                                                                    pattlen, 
                                                                    position, 
                                                                    margin_left=project.margin_left,
                                                                    margin_right=project.margin_right):
                if good_weight * num_good - bad_weight * num_bad >= threshold:
                    patternset[ch].add(position)

        print('Selected %s patterns at level %s' % (len(patternset), len(project.patterns) + 1))

    # evaluate
    evaluate_pattern_set(patternset, inhibiting, project.dictionary, margin_left=project.margin_left, margin_right=project.margin_right)

    missed = 0
    false = 0
    for word, hyphens in project.dictionary.items():
        weight = project.weights[word]
        
        missed += count_missed(hyphens, weight)
        false += count_false(hyphens, weight)

    print('Missed (weighted):', missed, '(%4.3f%%)' % (missed * 100 / (total_hyphens + 0.000001)))
    print('False (weighted):', false,   '(%4.3f%%)' % (false * 100 / (total_hyphens + 0.000001)))

    if args.commit:
        project.params.append(SimpleNamespace(
            range = args.range,
            selector   = args.selector
        ))
        project.patterns.append(patternset)
        save_project(project, args.project)
        print('...Committed!')

    return 0


def main_export(args):
    if os.path.exists(args.output):
        print('Pattern file already exists! Delete it first, or change the name. Pattern file: %s' % args.output)
        return -1
    
    project = load_project(args.project)

    keys = set()
    for patternset in project.patterns:
        keys.update(patternset.keys())
    
    patts = []
    for key in sorted(keys):
        controls = [0] * (len(key) + 1)
        level = 0
        for patternset in project.patterns:
            level += 1
            for index in patternset.get(key, EMPTYSET):
                controls[index] = level

        out = []
        for i, c in enumerate(controls):
            if i > 0:
                out.append(key[i-1])
            if c > 0:
                out.append(str(c))
        patt = ''.join(out)
        patts.append(patt)
    
    
    num_patterns = 0
    num_exceptions = 0
    
    with codecs.open(args.output, 'w', 'utf-8') as f:
        f.write('\\patterns{\n')
        for patt in patts:
            f.write(patt + '\n')
            num_patterns += 1
        f.write('}\n')
        f.write('\\hyphenation{\n')
        for word, _ in compute_dictionary_errors(project.patterns,
                                                          project.dictionary,
                                                          margin_left=project.margin_left,
                                                          margin_right=project.margin_right):
            text = format_dictionary_word(word, project.dictionary[word])
            f.write(text + '\n')
            num_exceptions += 1
        f.write('}\n')
    
    print('Created TeX patterns file', args.output)
    print('Number of patterns:', num_patterns)
    print('Number of exceptions:', num_exceptions)
    
    return 0


def main_show_errors(args):
    project = load_project(args.project)

    for word, prediction in compute_dictionary_errors(project.patterns, 
                                            project.dictionary, 
                                            margin_left=project.margin_left, 
                                            margin_right=project.margin_right):
        
        text = format_dictionary_word(word, prediction, project.dictionary[word])
        print(text, text.encode('unicode-escape').decode())
    
    return 0


def main_hyphenate(args):
    
    project = load_project(args.project)
    
    maxchunk = 0
    for patternset in project.patterns:
        if patternset:
            maxchunk = max(maxchunk, max(len(x) for x in patternset.keys()))

    with codecs.open(args.input or sys.stdin.fileno(), 'r', 'utf-8') as f:
        with codecs.open(args.output or sys.stdout.fileno(), 'w', 'utf-8') as out:

            for word in f:
                word = word.strip()
                if not word:
                    continue
    
                prediction = apply_patterns(project.patterns, word, maxchunk, 
                                            margin_left=project.margin_left, 
                                            margin_right=project.margin_right)
                
                s = format_hyphenation(word, prediction)
                out.write(s + '\n')


def count_hyphens(hyphens, weights):
    return sum(weights[i] if x == TRUE_HYPHEN else 0 for i,x in enumerate(hyphens))
def count_missed(hyphens, weights):
    return sum(weights[i] if x == MISSED_HYPHEN else 0 for i,x in enumerate(hyphens))
def count_false(hyphens, weights):
    return sum(weights[i] if x == FALSE_HYPHEN else 0 for i,x in enumerate(hyphens))


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generates TeX hyphenation patterns')
    parser.add_argument('project', help='Name of the project file')
    sub    = parser.add_subparsers(help='Commands', dest='cmd')
    
    # "new" command
    parser_new = sub.add_parser('new', help='Creates new hyphenation pattern project from dictionary')
    parser_new.add_argument('dictionary', help='Dictionary of hyphenated words (one word per line)')
    parser_new.add_argument('-m', '--margins', help='Hyphenation margins. If not set, will  be computed from the dictionary')
    parser_new.add_argument('-i', '--ignore_weights', default=False, action='store_true', help='If set, ignores dictionary weights (not recommented)')
    
    # "show" command
    parser_show = sub.add_parser('show', help='Displays information about current hyphenation project')  # @UnusedVariable

    # "train" command
    parser_train = sub.add_parser('train', help='Trains next level of hyphenation patterns')
    parser_train.add_argument('-s', '--selector', default='1:5:10', help='triplet of numbers that control pattern selection. Format is: "good_weight:bad_weight:threshold"')
    parser_train.add_argument('-r', '--range', default='1,5', help='range of patterns lengths. Default is 1,5')
    parser_train.add_argument('-c', '--commit', default=False, action='store_true', help='If set, project is modified')

    # "export" command
    parser_export = sub.add_parser('export', help='Exports project as a set of TeX patterns')
    parser_export.add_argument('output', help='Name of the TeX pattern file to create')

    # "show_errors" command
    parser_show_errors = sub.add_parser('show_errors', help='Shows all errors')  # @UnusedVariable

    # "hyphenate" command
    parser_hyphenate = sub.add_parser('hyphenate', help='Hyphenates a list of words')
    parser_hyphenate.add_argument('-i', '--input', default=None, help='Input file with word list - one word per line. If not given, reads stdin.')
    parser_hyphenate.add_argument('-o', '--output', default=None, help='Output file with hyphenated words - one per line. If not given, writes to stdout.')

    args = parser.parse_args()
    if args.cmd == 'new':
        parser.exit(main_new(args))
    elif args.cmd == 'show':
        parser.exit(main_show(args))
    elif args.cmd == 'train':
        parser.exit(main_train(args))
    elif args.cmd == 'export':
        parser.exit(main_export(args))
    elif args.cmd == 'show_errors':
        parser.exit(main_show_errors(args))
    elif args.cmd == 'hyphenate':
        parser.exit(main_hyphenate(args))
    else:
        parser.error('Command required')


if __name__ == '__main__':
    main()