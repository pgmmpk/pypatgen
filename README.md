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
wget https://raw.githubusercontent.com/slavonic/cu-tex/master/data/words.txt
> Resolving raw.githubusercontent.com... 23.235.46.133
> Connecting to raw.githubusercontent.com|23.235.46.133|:443... connected.
> HTTP request sent, awaiting response... 200 OK
> Length: 274628 (268K) [text/plain]
> Saving to: 'words.txt'
```

2. Create project. Lets call it "words":
   ```bash
pypatgen words new  words.txt
> Automatically detecting hyphenation margins (from dictionary)
> Created project words from dictionary words.txt
> 
> Project file words
>     created: 2016-02-28 18:09:40.801447
>     last modified: 2016-02-28 18:09:40.801478
>     margin_left: 1
>     margin_right: 1
>     dictionary size: 17507
>     total hyphens: (weighted) 42174
>     number of pattern levels: 0
```
   Note that we did not set hyphenation and therfore system inferred them from the dictionary. 
Computed margins are (1, 1), because Church Slavonic allows hypenating after the first letter and just before the last letter.
In other languages hyphenation margins are different. For example, English uses (2, 3) -- i.e. it never hyphenates after first letter, but can hyphenate 
after two-letter prefix.

3. Lets try finding good hyphenation patterns (this will be the first pattern set that we select). As a start, lets
try patterns of length 1 and 2 only. And lets use selector "1:2:20". Remember, that this step does not
update the project (unless we use `--commit` switch). So we can try different values and find the best.
   ```bash
pypatgen words train -r 1,2 -s 1:2:20
> Training hyphenation patterns (level=1)
>     range of pattern lengths: 1..2
>     selector: 1:2:20
> Selected 358 patterns at level 1
> Selected 381 patterns at level 1
> Missed (weighted): 2385 (5.655%)
> False (weighted): 14077 (33.378%)
```
   Selected patterns correctly predicted 93% of hyphens (i.e. they missed 6%), but introduced about 33% of false hyphens.

4. Lets make selector somewhat stricter - to lessen the number of false hyphens: 
   ```bash
pypatgen words train -r 1,2 -s 1:3:20
> Training hyphenation patterns (level=1)
>     range of pattern lengths: 1..2
>     selector: 1:3:20
> Selected 318 patterns at level 1
> Selected 335 patterns at level 1
> Missed (weighted): 4829 (11.450%)
> False (weighted): 6471 (15.344%)```
```
   Now we covered 89% of hyphens and introduced 15% of false hyphenations. Still too many false hits and too few correct hits. Lets try longer patterns:
   ```bash
pypatgen words train -r 1,3 -s 1:4:20
Training hyphenation patterns (level=1)
>     range of pattern lengths: 1..3
>     selector: 1:4:20
> Selected 294 patterns at level 1
> Selected 307 patterns at level 1
> Selected 1302 patterns at level 1
> Missed (weighted): 2382 (5.648%)
> False (weighted): 5096 (12.083%)
```   
   Lets commit - this is pretty good for the first layer!
   ```bash
pypatgen words train -r 1,3 -s 1:4:20 --commit
> Training hyphenation patterns (level=1)
>     range of pattern lengths: 1..3
>     selector: 1:4:20
> Selected 294 patterns at level 1
> Selected 307 patterns at level 1
> Selected 1302 patterns at level 1
> Missed (weighted): 2382 (5.648%)
> False (weighted): 5096 (12.083%)
> ... Committed!
```

5. Now lets train the next level of patterns. Since this is the second (i.e. even) level, this will be
inhibiting patterns. We want to supress those false positives. Lets try these parameters:
   ```bash
pypatgen words train -r 1,3 -s 1:2:5 
> Training inhibiting patterns (level=2)
>     range of pattern lengths: 1..3
>     selector: 1:2:5
> Selected 181 patterns at level 2
> Selected 192 patterns at level 2
> Selected 676 patterns at level 2
> Missed (weighted): 2675 (6.343%)
> False (weighted): 582 (1.380%)
```
Hmm, we reduced the number of false hits drastically at a cost of just slightly lowering the number of true hits.
Lets commit!
   ```bash
pypatgen words train -r 1,3 -s 1:2:5 --commit 
> Training inhibiting patterns (level=2)
>     range of pattern lengths: 1..3
>     selector: 1:2:5
> Selected 181 patterns at level 2
> Selected 192 patterns at level 2
> Selected 676 patterns at level 2
> Missed (weighted): 2675 (6.343%)
> False (weighted): 582 (1.380%)
> ...Committed!
```

6. Lets find more hyphens:
   ```
pypatgen words train -r 1,3 -s 1:2:5 
> Training hyphenation patterns (level=3)
>     range of pattern lengths: 1..3
>     selector: 1:2:5
> Selected 73 patterns at level 3
> Selected 76 patterns at level 3
> Selected 306 patterns at level 3
> Missed (weighted): 1021 (2.421%)
> False (weighted): 755 (1.790%)
```
   Lets try longer patterns and commit:
   ```
pypatgen words train -r 1,4 -s 1:2:5 -c
> Training hyphenation patterns (level=3)
>     range of pattern lengths: 1..4
>     selector: 1:2:5
> Selected 230 patterns at level 3
> Selected 303 patterns at level 3
> Selected 616 patterns at level 3
> Selected 619 patterns at level 3
> Missed (weighted): 886 (2.101%)
> False (weighted): 787 (1.866%)
> ...Committed!
```

7. Now its time to clean up false hyphens. Lets allow for the longer patterns and use very relaxing selector. After some trial
   and error, commit these parameters:
   ```bash
pypatgen words train -r 1,4 -s 1:1:2 -c
> Training inhibiting patterns (level=4)
>     range of pattern lengths: 1..4
>     selector: 1:1:2
> Selected 208 patterns at level 4
> Selected 295 patterns at level 4
> Selected 616 patterns at level 4
> Selected 619 patterns at level 4
> Missed (weighted): 970 (2.300%)
> False (weighted): 241 (0.571%)
> ...Committed!
```

8. Still have about 250 of false predictions and about 1000 of missed hyphens. Lets train another two layers:
```bash
pypatgen words train -r 1,5 -s 1:1:2 -c
> Training hyphenation patterns (level=5)
>     range of pattern lengths: 1..5
>     selector: 1:1:2
> Selected 262 patterns at level 5
> Selected 315 patterns at level 5
> Selected 689 patterns at level 5
> Selected 690 patterns at level 5
> Selected 1100 patterns at level 5
> Missed (weighted): 305 (0.723%)
> False (weighted): 378 (0.896%)
> ...Committed!
```
   and inhibiting layer:
```bash
pypatgen words train -r 1,6 -s 1:1:1 -c
> Training inhibiting patterns (level=6)
>     range of pattern lengths: 1..6
>     selector: 1:1:1
> Selected 632 patterns at level 6
> Selected 976 patterns at level 6
> Selected 1827 patterns at level 6
> Selected 1945 patterns at level 6
> Selected 2879 patterns at level 6
> Selected 2886 patterns at level 6
> Missed (weighted): 348 (0.825%)
> False (weighted): 26 (0.062%)
> ...Committed!
```
   Wow! Only 26 false hyphens left and 348 hyphens missed. This already looks great, but lets train
   two more layers.
   ```bash
pypatgen words train -r 1,6 -s 1:1:1 -c
> Training hyphenation patterns (level=7)
>     range of pattern lengths: 1..6
>     selector: 1:1:1
> Selected 619 patterns at level 7
> Selected 915 patterns at level 7
> Selected 1746 patterns at level 7
> Selected 1799 patterns at level 7
> Selected 2686 patterns at level 7
> Selected 2688 patterns at level 7
> Missed (weighted): 36 (0.085%)
> False (weighted): 45 (0.107%)
> ...Committed!
```
   and
   ```bash
pypatgen words train -r 1,6 -s 1:1:1 -c
> Training inhibiting patterns (level=8)
>     range of pattern lengths: 1..6
>     selector: 1:1:1
> Selected 25 patterns at level 8
> Selected 39 patterns at level 8
> Selected 75 patterns at level 8
> Selected 81 patterns at level 8
> Selected 120 patterns at level 8
> Selected 121 patterns at level 8
> Missed (weighted): 36 (0.085%)
> False (weighted): 27 (0.064%)
> ...Committed!
```
   We are done now with training. We missed 36 hyphens and we introduced only 27 false hyphens. This sounds pretty
good to me (probably overfit :).

6. Next (and last) step is to export generated patterns in TeX format:
   ```
pypatgen words export words.tex       
> Created TeX patterns file words.tex
> Number of patterns: 8552
> Number of exceptions: 42
```

The content of generated file is:
```TeX
\patterns{
.а҆5в
.а҆6вв
.а҆6вва
.а҆5в6д
.а҆в6ді
.а҆5ве
.а҆вен6
  ... many more patterns ...
ꙗ҆́7зю
ꙗ҆́с4
ꙗ҆́5сн
ꙗ҆7вѝ
ꙗ҆7вѧ
ꙗ҆7вѧ́
ꙗ҆7вѧ́т
ꙗ҆7р
ꙗ҆7рѧ
ꙗ҆7рѧ́
ꙗ҆7рѧ́щ
}
\hyphenation{
бла-го-сло-влю̀
во-ѡб-ра-зꙋ́-ю-ща-сѧ
во-скр҃си́-ти
во-скрⷭ҇нї-е
є҆ѵⷢ҇лїе
зе́-млю
и҆з-бав-ле́-нї-ѧ
 ... some more exception ...
со-ше́ст-вї-ю
сра-спи-на́-емь
три-пѣ́с-нецъ
чꙋ́-вствен-ный
чꙋ́-вствен-ныхъ
чꙋ̑вст-вї-ѧ
}
```

Last but not least. At any time you can examine the content of Project file by using `show` command:
```bash
pypatgen words show
> Project file words
>     created: 2016-02-28 18:09:40.801447
>     last modified: 2016-02-28 19:05:56.198309
>     margin_left: 1
>     margin_right: 1
>     dictionary size: 17507
>     total hyphens: (weighted) 42174
>     number of pattern levels: 8
> 1 HYPHENATING patternset, num patterns: 1302
>     Trained with: range 1,3, selector 1:4:20
> 2 INHIBITING patternset, num patterns: 676
>     Trained with: range 1,3, selector 1:2:5
> 3 HYPHENATING patternset, num patterns: 619
>     Trained with: range 1,4, selector 1:2:5
> 4 INHIBITING patternset, num patterns: 619
>     Trained with: range 1,4, selector 1:1:2
> 5 HYPHENATING patternset, num patterns: 1100
>     Trained with: range 1,5, selector 1:1:2
> 6 INHIBITING patternset, num patterns: 2886
>     Trained with: range 1,6, selector 1:1:1
> 7 HYPHENATING patternset, num patterns: 2688
>     Trained with: range 1,6, selector 1:1:1
> 8 INHIBITING patternset, num patterns: 121
>     Trained with: range 1,6, selector 1:1:1
```