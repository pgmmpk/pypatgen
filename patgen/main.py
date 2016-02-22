'''
Created on Feb 16, 2016

@author: mike
'''
import os
import codecs
import collections
from types import SimpleNamespace
import datetime
from patgen import load_dictionary, save_project, load_project, parse_selector,\
    stagger_range, generate_pattern_statistics, evaluate_pattern_set, EMPTYSET,\
    compute_dictionary_errors, format_dictionary_word,\
    TRUE_HYPHEN, MISSED_HYPHEN, FALSE_HYPHEN, NOT_A_HYPHEN


def main_new(args):
    
    if os.path.exists(args.project):
        print('Project file already exists! Use different name or delete old project first. File %s' % args.project)
        return -1
    
    if not os.path.exists(args.dictionary):
        print('Dictionary file not found', args.dictionary)
        return -1
    
    dictionary = load_dictionary(args.dictionary)
    for hyphen in dictionary.values():
        for i in range(len(hyphen)):
            if hyphen[i] == TRUE_HYPHEN:
                hyphen[i] = MISSED_HYPHEN
            elif hyphen[i] == FALSE_HYPHEN:
                hyphen[i] = NOT_A_HYPHEN

    project = SimpleNamespace(
            dictionary=dictionary,
            margin_left = args.margin_left,
            margin_right = args.margin_right,
            patterns = [],
            params = [],
            created = datetime.datetime.now(),
            modified = datetime.datetime.now()
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
    print('\ttotal hyphens:', sum(count_hyphens(x)+count_missed(x) for x in project.dictionary.values()))
    print('\tnumber of pattern levels:', len(project.patterns))
    
    for i, patternset in enumerate(project.patterns):
        if i & 1 == 0:
            print((i+1), 'Hyphenating patternset, num patterns:', len(patternset))
        else:
            print((i+1), 'Inhibiting patternset, num patterns:', len(patternset))
        params = project.params[i]
        print('\tTrained with: pattern length %s..%s, selector %s' % (params.min_length, params.max_length, params.selector))

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

    print('\tmin_pattern_length:', args.min_pattern_length)
    print('\tmax_pattern_length:', args.max_pattern_length)
    print('\tselector:', args.selector)
    
    total_hyphens = sum(count_hyphens(x)+count_missed(x) for x in project.dictionary.values())

    patternset = collections.defaultdict(set)
    for pattlen in stagger_range(args.min_pattern_length, args.max_pattern_length+1):
        for position in range(0, pattlen+1):
            for ch, num_good, num_bad in generate_pattern_statistics(project.dictionary,
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
    missed = sum(count_missed(x) for x in project.dictionary.values())
    false  = sum(count_false(x) for x in project.dictionary.values())

    print('Missed:', missed, '(%4.3f%%)' % (missed * 100 / (total_hyphens + 0.000001)))
    print('False:', false,   '(%4.3f%%)' % (false * 100 / (total_hyphens + 0.000001)))
    
    ## was here to cross-check incremental computation of stats above
    #from patgen import evaluate_dictionary
    #total_hyphens, missed, false = evaluate_dictionary(project.patterns + [patternset], project.dictionary)
    #print('*Missed:', missed, '(%4.3f%%)' % (missed * 100 / (total_hyphens + 0.000001)))
    #print('*False:', false,   '(%4.3f%%)' % (false * 100 / (total_hyphens + 0.000001)))

    if args.commit:
        project.params.append(SimpleNamespace(
            min_length = args.min_pattern_length,
            max_length = args.max_pattern_length,
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


def count_hyphens(hyphens):
    return sum(1 if x == TRUE_HYPHEN else 0 for x in hyphens)
def count_missed(hyphens):
    return sum(1 if x == MISSED_HYPHEN else 0 for x in hyphens)
def count_false(hyphens):
    return sum(1 if x == FALSE_HYPHEN else 0 for x in hyphens)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generates TeX hyphenation patterns')
    parser.add_argument('project', help='Name of the project file')
    sub    = parser.add_subparsers(help='Commands', dest='cmd')
    
    # "new" command
    parser_new = sub.add_parser('new', help='Creates new hyphenation pattern project from dictionary')
    parser_new.add_argument('dictionary', help='Dictionary of hyphenated words (one word per line)')
    parser_new.add_argument('--margin_left', default=1, type=int, help='hyphenation left margin. Default is 1.')
    parser_new.add_argument('--margin_right', default=1, type=int, help='hyphenation right margin. Default is 1.')

    # "show" command
    parser_show = sub.add_parser('show', help='Displays information about current hyphenation project')  # @UnusedVariable

    # "train" command
    parser_train = sub.add_parser('train', help='Trains next level of hyphenation patterns')
    parser_train.add_argument('--selector', default='1:5:10', help='triplet of numbers that control pattern selection. Format is: "good_weight:bad_weight:threshold"')
    parser_train.add_argument('--min_pattern_length', default=1, type=int, help='minimal length of pattern. Default is 1')
    parser_train.add_argument('--max_pattern_length', default=5, type=int, help='maximal length of pattern. Default is 5')
    parser_train.add_argument('--commit', default=False, action='store_true', help='If set, project is modified')

    # "export" command
    parser_export = sub.add_parser('export', help='Exports project as a set of TeX patterns')
    parser_export.add_argument('output', help='Name of the TeX pattern file to create')

    # "show_errors" command
    parser_show_errors = sub.add_parser('show_errors', help='Shows all errors')  # @UnusedVariable

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
    else:
        parser.error('Command required')

if __name__ == '__main__':
    main()