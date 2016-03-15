'''
Created on Feb 16, 2016

@author: mike
'''
from __future__ import print_function

import os
import codecs
import sys
from patgen.margins import Margins
from patgen.dictionary import Dictionary, format_dictionary_word,\
    format_word_as_pattern
from patgen.project import Project
from patgen.selector import Selector
from patgen.range import Range
from patgen.version import __version__
from patgen.patternset import PatternSet
from patgen.layer import Layer


def main_new(args):
    print('Creating new project', args.project, 'from dictionary', args.dictionary)
    
    if os.path.exists(args.project):
        print('Project file already exists! Use different name or delete old project first. File %s' % args.project)
        return -1
    
    if not os.path.exists(args.dictionary):
        print('Dictionary file not found', args.dictionary)
        return -1
    
    dictionary = Dictionary.load(args.dictionary)

    if args.margins is None:
        print('Automatically computing hyphenation margins from dictionary')
        margins = dictionary.compute_margins()
    else:
        margins = Margins.parse(args.margins)

    project = Project(dictionary, margins)
    project.save(args.project)

    return main_show(args)


def main_show(args):
    
    if not os.path.exists(args.project):
        print('Project file not found:', args.project)
        return -1
    
    project = Project.load(args.project)
    
    print('Project file', args.project)
    print('\tcreated:', project.created)
    print('\tlast modified:', project.modified)
    print('\tmargins:', project.margins)
    print('\tdictionary size:', len(project.dictionary.keys()))
    #if project.ignore_weights:
    #    print('\tdictionary weights were ignored (-i flag active)')
    print('\ttotal hyphens: (weighted)', project.total_hyphens)
    print('\ttotal missed : (weighted)', project.missed, percent(project.missed, project.total_hyphens))
    print('\ttotal false  : (weighted)', project.false, percent(project.false, project.total_hyphens))
    print('\tnumber of pattern levels:', len(project.patternset))
    
    for i, layer in enumerate(project.patternset):
        if i & 1 == 0:
            print((i+1), 'HYPHENATING patternset, num patterns:', len(layer))
        else:
            print((i+1), 'INHIBITING patternset, num patterns:', len(layer))
        print('\tTrained with: range %r, selector %r' % (layer.patlen_range, layer.selector))

    print()
    return 0


def main_train(args):
    print('Training project', args.project, 'using range', args.range, 'and selector', args.selector)
    
    project = Project.load(args.project)

    if len(project.patternset) & 1:
        print('Training INHIBINTING pattern layer (level=%s)' % (len(project.patternset)+1))
    else:
        print('Training HYPHENATION pattern layer (level=%s)' % (len(project.patternset)+1))

    patlen_rng = Range.parse(args.range)
    selector = Selector.parse(args.selector)

    print('\tpattern lengths:', patlen_rng)
    print('\tselector:', args.selector)
    
    total_hyphens = project.total_hyphens

    project.train_new_layer(patlen_rng, selector)

    missed, false = project.missed, project.false

    print('Missed (weighted):', missed, percent(missed, total_hyphens))
    print('False (weighted):', false, percent(false, total_hyphens))

    if args.commit:
        project.save(args.project)
        print('...Committed!')
    else:
        print('...Projects NOT changed (use --commit flag to save changes)')

    print()
    return 0


def main_batchtrain(args):
    print('Batch-training of project', args.project, 'using specs from', args.specs)

    with codecs.open(args.specs, 'r', 'utf-8') as f:
        l = {}
        exec(f.read(), {}, l)
        batches = l['SPECS']

    for params in batches:
        args.range = params['range']
        args.selector = params['selector']
        args.commit = True
        
        rc = main_train(args)
        if rc:
            print('Error:', rc)
            return rc
    
    return 0


def main_export(args):
    print('Exporting patterns from', args.project, 'and saving them in TeX format to', args.output)

    if os.path.exists(args.output):
        print('Pattern file already exists! Delete it first, or change the name. Pattern file: %s' % args.output)
        return -1
    
    project = Project.load(args.project)

    pattern_strings = list(project.patternset.pattern_strings())
    exceptions = list(project.patternset.errors(project.dictionary, project.margins))

    with codecs.open(args.output, 'w', 'utf-8') as f:
        f.write('\\patterns{\n')
        for patt in pattern_strings:
            f.write(patt + '\n')
        f.write('}\n')
        f.write('\\hyphenation{\n')
        for word, hyphens, _, _ in exceptions:
            text = format_dictionary_word(word, hyphens)
            f.write(text + '\n')
        f.write('}\n')
    
    print('Created TeX patterns file', args.output)
    print('Number of patterns:', len(pattern_strings))
    print('Number of exceptions:', len(exceptions))

    if args.patterns:
        print()
        with codecs.open(args.patterns, 'w', 'utf-8') as f:
            for patt in pattern_strings:
                f.write(patt + '\n')
        print('Written raw patterns to', args.patterns)

    if args.exceptions:
        print()
        with codecs.open(args.exceptions, 'w', 'utf-8') as f:
            for word, hyphens, _, _ in exceptions:
                text = format_dictionary_word(word, hyphens)
                f.write(text + '\n')
        print('Written raw exceptions to', args.exceptions)

    print()
    return 0

def main_hyphenate(args):
    print('Hyphenating', args.input, 'into', args.output, 'using project', args.project)
    
    project = Project.load(args.project)

    with codecs.open(args.input or sys.stdin.fileno(), 'r', 'utf-8') as f:
        with codecs.open(args.output or sys.stdout.fileno(), 'w', 'utf-8') as out:

            for word in f:
                word = word.strip()
                if not word:
                    continue
    
                prediction = project.patterns.hyphenate(word, margins=project.margins) 

                s = format_dictionary_word(word, prediction)
                out.write(s + '\n')
    
    print()
    return 0


def main_test(args):
    print('Testing', args.project, 'on dictionary', args.dictionary)
    project = Project.load(args.project)

    dictionary = Dictionary.load(args.dictionary)

    print('Performance of', args.project, 'on', args.dictionary)
    do_test(project, dictionary)

    if args.errors:
        with codecs.open(args.errors, 'w', 'utf-8') as f:
            for word, hyphens, missed, false in project.patternset.errors(dictionary, project.margins):
                f.write(format_dictionary_word(word, hyphens, missed, false) + '\n')
        print('Saved errors to', args.errors)

    if args.patterns:
        with codecs.open(args.patterns, 'w', 'utf-8') as f:
            for word, hyphens, missed, false in project.patternset.errors(dictionary, project.margins):
                f.write(format_word_as_pattern(word, missed, false) + '\n')
        print('Saved errors to', args.patterns)

    print()
    return 0


def main_swap(args):
    print('Swapping inhibiting layers between', args.project, 'and', args.project2)

    project = Project.load(args.project)
    project2 = Project.load(args.project2)
    
    if len(project.patternset) != len(project2.patternset):
        raise ValueError('You can only swap layers between projects with same number of layers!')
    
    for i in range(1, len(project.patternset), 2):
        project.patternset[i], project2.patternset[i] = project2.patternset[i], project.patternset[i]

    print('Performance of', args.project)
    project.missed, project.false = do_test(project, project.dictionary)
    print('Performance of', args.project2)
    project2.missed, project2.false = do_test(project2, project2.dictionary)
    
    if args.commit:
        project.save(args.project)
        project2.save(args.project2)
        print('...Committed')
    else:
        print('...Projects NOT changed (use --commit flag to save changes)')
    
    print()
    return 0


def main_compact(args):
    print('Compacting hyphenation patterns for', args.project)
    project = Project.load(args.project)

    before_compact = [layer.compute_num_patterns() for layer in project.patternset]
    
    project.patternset.compact()
    
    after_compact =  [layer.compute_num_patterns() for layer in project.patternset]
    
    print('Result:')
    for level0, (before, after) in enumerate(zip(before_compact, after_compact)):
        print('\tLevel %s: %6d => %6d' % (level0+1, before, after))
    
    if args.commit:
        project.save(args.project)
        print('...Committed')
    else:
        print('...Project NOT changed (use --commit flag to save changes)')
    
    print()
    return 0


def do_test(project, dictionary):

    total_hyphens = dictionary.compute_total_hyphens()

    num_missed, num_false = project.patternset.evaluate(dictionary, project.margins)

    print('Missed (weighted):', num_missed, '(%4.3f%%)' % (num_missed * 100 / (total_hyphens + 0.000001)))
    print('False (weighted):', num_false,   '(%4.3f%%)' % (num_false * 100 / (total_hyphens + 0.000001)))
    
    return num_missed, num_false


def main_import(args):
    print('Loading patterns from', args.input, 'into project', args.project)
    project = Project.load(args.project)
    
    if len(project.patternset) > 0:
        print('ERROR: project already has some patterns. Can only load into empty project!')
        return -1

    patterns = {}
    entered = False
    with codecs.open(args.input, 'r', 'utf-8') as f:
        for line in f:
            line = line.strip()
            line = line.split('%')[0]
            if not line: 
                continue
            
            if line == '\\patterns{':
                entered = True
            
            elif entered and line == '}':
                break
            
            elif entered:
                text, control = PatternSet.parse_pattern(line)
                patterns[text] = control
    
    if patterns:
        maxlevel = 0
        for control in patterns.values():
            for level in control.values():
                maxlevel = max(maxlevel, level)
    
        patlen = max(len(text) for text in patterns.keys())
    
        for i in range(maxlevel):
            project.patternset.append(Layer(Range(1, patlen+2), None, i & 2 == 1))
    
        for text, control in patterns.items():
            project.patternset.set_pattern_control(text, control)
    else:
        print('WARNING: patterns file is empty!')

    project.missed, project.false = do_test(project, project.dictionary)

    if args.commit:
        project.save(args.project)
        print('...Committed')
    else:
        print('...Project NOT changed (use --commit flag to save changes)')
    
    print()
    return 0

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generates TeX hyphenation patterns')
    parser.add_argument('project', help='Name of the project file')

    sub    = parser.add_subparsers(help='Commands', dest='cmd')

    # "new" command
    parser_new = sub.add_parser('new', help='Creates new hyphenation pattern project from dictionary')
    parser_new.add_argument('dictionary', help='Dictionary of hyphenated words (one word per line)')
    parser_new.add_argument('-m', '--margins', help='Hyphenation margins. If not set, will  be computed from the dictionary')
    
    # "show" command
    parser_show = sub.add_parser('show', help='Displays information about current hyphenation project')  # @UnusedVariable

    # "train" command
    parser_train = sub.add_parser('train', help='Trains next level of hyphenation patterns')
    parser_train.add_argument('-s', '--selector', default='1:5:10', help='triplet of numbers that control pattern selection. Format is: "good_weight:bad_weight:threshold"')
    parser_train.add_argument('-r', '--range', default='1,5', help='range of patterns lengths. Default is 1,5')
    parser_train.add_argument('-c', '--commit', default=False, action='store_true', help='If set, project is modified')

    # "batchtrain" command
    parser_batchtrain = sub.add_parser('batchtrain', help='Trains all levels from batch specs')
    parser_batchtrain.add_argument('specs', help='file with batch training parameters specifications')

    # "export" command
    parser_export = sub.add_parser('export', help='Exports project as a set of TeX patterns')
    parser_export.add_argument('output', help='Name of the TeX pattern file to create')
    parser_export.add_argument('-p', '--patterns', help='Optional file to write raw hyphenation patterns')
    parser_export.add_argument('-e', '--exceptions', help='Optional file to write raw exceptions')

    # "hyphenate" command
    parser_hyphenate = sub.add_parser('hyphenate', help='Hyphenates a list of words')
    parser_hyphenate.add_argument('-i', '--input', default=None, help='Input file with word list - one word per line. If not given, reads stdin.')
    parser_hyphenate.add_argument('-o', '--output', default=None, help='Output file with hyphenated words - one per line. If not given, writes to stdout.')

    # "test" command
    parser_test = sub.add_parser('test', help='Test performance on a dictionary')
    parser_test.add_argument('dictionary', help='File name of a test dictionary')
    parser_test.add_argument('-p', '--patterns', help='Optional file to write errors as patterns')
    parser_test.add_argument('-e', '--errors', help='Optional file to write errors (for error analysis)')

    # "swap" command
    parser_swap = sub.add_parser('swap', help='Swaps odd layers between two projects (advanced)')
    parser_swap.add_argument('project2', help='File name of a second project')
    parser_swap.add_argument('-c', '--commit', default=False, action='store_true', help='If set, swapped projects are saved')

    # "compact" command
    parser_compact = sub.add_parser('compact', help='Removes redundancy from parterns')
    parser_compact.add_argument('-c', '--commit', default=False, action='store_true', help='If set, swapped projects are saved')

    # "import" command
    parser_import = sub.add_parser('import', help='Imports patterns from TeX file')
    parser_import.add_argument('input', help='Name of the TeX patterns file')
    parser_import.add_argument('-c', '--commit', default=False, action='store_true', help='If set, swapped projects are saved')

    if '-v' in sys.argv or '--version' in sys.argv:
        print('PYPATGEN version:', __version__)
        parser.exit(0)

    args = parser.parse_args()
    if args.cmd == 'new':
        parser.exit(main_new(args))
    elif args.cmd == 'show':
        parser.exit(main_show(args))
    elif args.cmd == 'train':
        parser.exit(main_train(args))
    elif args.cmd == 'export':
        parser.exit(main_export(args))
    elif args.cmd == 'hyphenate':
        parser.exit(main_hyphenate(args))
    elif args.cmd == 'batchtrain':
        parser.exit(main_batchtrain(args))
    elif args.cmd == 'test':
        parser.exit(main_test(args))
    elif args.cmd == 'swap':
        parser.exit(main_swap(args))
    elif args.cmd == 'compact':
        parser.exit(main_compact(args))
    elif args.cmd == 'import':
        parser.exit(main_import(args))
    else:
        parser.error('Command required')


def percent(x, base):
    return '%4.2f%%' % (100.0 * x / (base + 0.0000001))

if __name__ == '__main__':
    main()
