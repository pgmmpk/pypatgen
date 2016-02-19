# pypatgen
TeX hypenation pattern generator (python version of "patgen").

WARNING: pre-alpha quality! Work-in-progress! You've been warned.

Some 30+ years ago Frank Liang proposed a hyphenation algorithm based on patterns. The advantage was that it was reasonably fast and
required limited memory to run. For pattern training Liang used a heuristics, and implemented it in a `patgen` program that is part
of standard TeX distribution. It is interesting that this hyphenation algorithm survived for 30+ years. Moreover, OpenOffice (aka LibreOffice)
apparently uses the same machinery and the same patterns for hyphenation.

I tried to reproduce the logic described in [Frank Liang's thesis](https://tug.org/docs/liang/liang-thesis.pdf),
without using weird data structures and obscure Web2C programming language.

I was able to successfully generate a pattern set, achieving pretty good hyphenation.

However, there is no guarantee that logic implemented here is compatible with Liang's. In fact, its very likely that
this code differs in some subtle details and if you feed the same hyphenation dictionary to original Linag's `patgen` program you 
will get a different set of patterns.

Input and output files use UTF-8 encoding. Generated patterns and exception list can be
directly used in modern Unicode TeX engines (XeTeX, LuaTeX). If you want to build hyphenation 
patterns for 8-bit (legacy) TeX engines, re-encode output accordingly.


How to train it
===============

TeX uses hyphenation patterns that are organized in a list of pattern sets. First pattern set in the list generates hyphenation suggestions.
Second pattern set in the list generates pattern inhibitions. Third pattern set suggests some more hyphenations, and so on and so forth.

In TeX there can be up to 9 alternating pattern sets (the limitation is imposed by the format that TeX uses to represent patterns in
its input file). Here we are not technically limited by 9 pattern sets. But since we eventually want to use generated patterns in TeX, it
is recommended not to overstep this limitation.

When training, one creates pattern sets one at a time. At each step the goal is to choose training parameters such that you cover as many 
hyphenations as possible without introducing too many false positives. When training inhibiting sets the goal is to remove as many false 
positives as possible without removing too many true positives.

The overall workflow is like this:

1. Create a "Project" by using `new` command and giving it a hyphenation dictionary. You should also set hyphenation margins.

2. Train pattern set by running `train` command on this project and giving it training parameters. Most important parameter is
   the selector. You can also limit the length of patterns that are examined. By default, this does NOT alter the project in any way (i.e. trained
   pattern set is not added to the project patterns).

3. Repeat step (2) trying different values for the training parameters, until you are satisfied with the performance of this
   pattern set. The performance is reported as the number of "missed" hyphens and the number of "false" hyphens. Missed ones are the ones that
   we failed to detect. False ones are the ones that were suggested incorrectly. You should aim to minimized both.
   Once you are happy, you repeat the last `train` command adding `--commit` option. This will add the trained pattern set
   to the patterns list in project file.

4. Now you are ready to train the next pattern set. Keep in mind that even sets are inhibiting. So training inhibiting layers makes number of 
   "false" hyphenations smaller, at the expense of having some extra "missed" ones. Odd ones are hyphenating patterns, and training it will make
   "missed" statistics smaller, at the expense of possibly some extra "false" hits.
5. Repeat training patterns until you are satisfied (remember to not exceed TeX limitation on the total number of pattern sets).

6. Finally you can `export` trained patterns in TeX format.

7. At any time you can examine project by using `show` command.


Sample training session: generating hyphenation patterns for [Church Slavonic](https://en.wikipedia.org/wiki/Church_Slavonic_language)
=======================

1. Download hyphenation dictionary for Church Slavonic language:
   ```bash
wget https://raw.githubusercontent.com/typiconman/Perl-Lingua-CU/master/lib/Lingua/CU/words.txt
> Resolving raw.githubusercontent.com... 23.235.46.133
> Connecting to raw.githubusercontent.com|23.235.46.133|:443... connected.
> HTTP request sent, awaiting response... 200 OK
> Length: 274628 (268K) [text/plain]
> Saving to: 'words.txt'
```

2. Create project. Lets call it "words":
   ```bash
patgen words new words.txt --margin_left 1 --margin_right 1
> Created project words from dictionary words.txt
> Project file words
>     created: 2016-02-19 10:14:00.656172
>     last modified: 2016-02-19 10:14:00.656198
>     margin_left: 1
>     margin_right: 1
>     dictionary size: 12385
>     total hyphens: 28863
>     number of pattern layers:
```
   Note that we set hyphenation margins to (1, 1), because Church Slavonic allows hypenating after the first letter and just before the last letter.
In other languages hyphenation margins are different. For example, English uses (2, 3) -- i.e. it never hyphenates after first letter, but can hyphenate 
after two-letter prefix.

3. Lets try finding good hyphenation patterns (this will be the first pattern set that we select). As a start, lets
try patterns of length 2 and 3 only. And lets use fairly concervative selector "1:10:50". Remember, that this step does not
update the project (unless we use `--commit` switch). So we can try different values and find the best.
   ```bash
patgen words train --min_pattern_length 2 --max_pattern_length 3 --selector 1:10:50
> Training hyphenation patterns (level=1)
>     min_pattern_length: 2
>     max_pattern_length: 3
>     selector: 1:10:50
> Selected 174 patterns at level 1
> Selected 278 patterns at level 1
> Missed: 9616 (33.316%)
> False: 628 (2.176%)
```
   Selected patterns correctly predicted 67% of hyphens (i.e. they missed 33%), and introduced about 2% of false hyphens.

4. Lets relax a bit selection criteria to get better coverage (this will likely increase the number of false hits) 
   ```bash
patgen words train --min_pattern_length 2 --max_pattern_length 3 --selector 1:10:10
> Training hyphenation patterns (level=1)
>     min_pattern_length: 2
>     max_pattern_length: 3
>     selector: 1:10:10
> Selected 1283 patterns at level 1
> Selected 1586 patterns at level 1
> Missed: 2405 (8.332%)
> False: 939 (3.253%)
```
   Now we covered 92% of hyphens and introduced 3% of false hyphenations. Lets commit - this is pretty good for the first layer!
   ```bash
patgen words train --min_pattern_length 2 --max_pattern_length 3 --selector 1:10:10 --commit
> Training hyphenation patterns (level=1)
>     min_pattern_length: 2
>     max_pattern_length: 3
>     selector: 1:10:10
> Selected 1283 patterns at level 1
> Selected 1586 patterns at level 1
> Missed: 2405 (8.332%)
> False: 939 (3.253%)
> ... Committed!
```

5. Now lets train the next level of patterns. Since this is the second (i.e. even) level, this will be
inhibiting patterns. We want to supress those false positives. Lets try these parameters:
   ```bash
patgen words train --min_pattern_length 2 --max_pattern_length 3 --selector 1:10:10 
> Training inhibiting patterns (level=2)
>     min_pattern_length: 2
>     max_pattern_length: 3
>     selector: 1:10:10
> Selected 16 patterns at level 2
> Selected 33 patterns at level 2
> Missed: 2405 (8.332%)
> False: 556 (1.926%)
```
Hmm, we almost halved the number of false hits. But this is not good enough. We want to be very sensitive
about introducing false hyphenations. It is better to miss few true hyphens than to introduce an invalid one. So lets
relax selector drastically:
   ```bash
patgen words train --min_pattern_length 2 --max_pattern_length 3 --selector 1:1:1  
> Training inhibiting patterns (level=2)
>     min_pattern_length: 2
>     max_pattern_length: 3
>     selector: 1:1:1
> Selected 692 patterns at level 2
> Selected 894 patterns at level 2
> Missed: 2552 (8.842%)
> False: 93 (0.322%)
```
   Now it looks pretty good. We have only 93 false positives, without affecting true predictions too much. Lets commit!

   ```
patgen words train --min_pattern_length 2 --max_pattern_length 3 --selector 1:1:1 --commit
> Training inhibiting patterns (level=2)
>     min_pattern_length: 2
>     max_pattern_length: 3
>     selector: 1:1:1
> Selected 692 patterns at level 2
> Selected 894 patterns at level 2
> Missed: 2552 (8.842%)
> False: 93 (0.322%)
> ...Committed!
```

   Lets find more hyphens:
   ```
patgen words train --min_pattern_length 2 --max_pattern_length 3 --selector 1:2:1 
Training hyphenation patterns (level=3)
    min_pattern_length: 2
    max_pattern_length: 3
    selector: 1:2:1
Selected 1712 patterns at level 3
Selected 2004 patterns at level 3
Missed: 383 (1.327%)
False: 439 (1.521%)
```
   We are missing only 1.3% of true hyphens. This sounds pretty good! Lets commit.
   ```bash
patgen words train --min_pattern_length 2 --max_pattern_length 3 --selector 1:2:1 --commit
> Training hyphenation patterns (level=3)
>     min_pattern_length: 2
>     max_pattern_length: 3
>     selector: 1:2:1
> Selected 1712 patterns at level 3
> Selected 2004 patterns at level 3
> Missed: 383 (1.327%)
> False: 439 (1.521%)
> ...Committed!
```

   Now its time to clean up false hyphens. Lets allow for the longer patterns and use very relaxing selector:
   ```
patgen words train --min_pattern_length 1 --max_pattern_length 5 --selector 1:2:1 
> Training inhibiting patterns (level=4)
>     min_pattern_length: 1
>     max_pattern_length: 5
>     selector: 1:2:1
> Selected 358 patterns at level 4
> Selected 476 patterns at level 4
> Selected 1142 patterns at level 4
> Selected 1147 patterns at level 4
> Selected 2094 patterns at level 4
> Missed: 400 (1.386%)
> False: 34 (0.118%)
```

   Wow! Only 34 false hyphens left. I'll take this - commit!
   ```bash
patgen words train --min_pattern_length 1 --max_pattern_length 5 --selector 1:2:1 --commit
> Training inhibiting patterns (level=4)
>     min_pattern_length: 1
>     max_pattern_length: 5
>     selector: 1:2:1
> Selected 358 patterns at level 4
> Selected 476 patterns at level 4
> Selected 1142 patterns at level 4
> Selected 1147 patterns at level 4
> Selected 2094 patterns at level 4
> Missed: 400 (1.386%)
> False: 34 (0.118%)
> ...Committed!
```

   Now patterns look pretty good. But lets add few more layers on top of this:
   ```
patgen words train --min_pattern_length 1 --max_pattern_length 5 --selector 1:2:1 --commit
Training hyphenation patterns (level=5)
    min_pattern_length: 1
    max_pattern_length: 5
    selector: 1:2:1
Selected 14 patterns at level 5
Selected 16 patterns at level 5
Selected 274 patterns at level 5
Selected 274 patterns at level 5
Selected 844 patterns at level 5
Missed: 60 (0.208%)
False: 73 (0.253%)
...Committed!
```

   And inhibiting level:
   ```
patgen words train --min_pattern_length 1 --max_pattern_length 5 --selector 1:2:1 --commit
Training inhibiting patterns (level=6)
    min_pattern_length: 1
    max_pattern_length: 5
    selector: 1:2:1
Selected 17 patterns at level 6
Selected 21 patterns at level 6
Selected 68 patterns at level 6
Selected 68 patterns at level 6
Selected 151 patterns at level 6
Missed: 60 (0.208%)
False: 37 (0.128%)
...Committed!
```

   We are done now with training. We missed 60 hyphens and we introduced only 37 false hyphens. This sounds pretty
good to me (probably overfit :).

6. Next (and last) step is to export generated patterns in TeX format:
   ```
patgen words export words.tex       
Created TeX patterns file words.tex
Number of patterns: 6697
Number of exceptions: 74
```

The content of generated file is:
```TeX
\patterns{
.а҆4вв
.а҆г4
.а҆г4г
.а҆г5к
.а҆г4р
.а҆4лв
.а҆4лл
.а҆4лм
.а҆4лф
.а҆ск4
.би2
.бл҃4
.бл҃4г
.бл҃4ж
.бл҃4з
.бо́5д
.в4
  ... many more patterns ...
ꙋ1ѧ
2ꙋⷧ
2ꙋⷧ҇
2ꙋⷩ
2ꙋⷩ҇
ꙗ3в
ꙗ3ви
ꙗ҆́с4
ꙗ҆́5с4н
ꙗ҆1п
ꙗ҆3р
}
\hyphenation{
а҆н-глі́й-стїи
а҆н-глі́й-стїи
бо-га́-тї-и
бо-го-ви́-днѡ
бра́-тї-и
ве́д-шї-и
ве-се́-лї-и
вос-кре-се́-нї-ю
вос-кре-се́-нї-ю
воскрⷭ҇нъ
 ... some more exception ...
сы́-и
три-дне́в-ство-ва-вша
че-ты-ре-де-сѧ-то-дне́-вный
че-ты-ре-де-сѧ-то-дне́-вный
ше-сто-кри-ла́-тї-и
}
```