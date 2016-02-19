# pypatgen
TeX hypenation pattern generator (python version of "patgen").

Some 30+ years ago Frank Liang proposed a hyphenation algorithm based on patterns. The advantage was that it was reasonably fast and
required limited memory to run. For pattern training Liang used a heuristics, and implemented it in a `patgen` program that is part
of standard TeX distribution. It is interesting that this hyphenation algorithm survived for 30+ years. Moreover, OpenOffice (aka LibreOffice)
apparently uses the same machinery and the same patterns for hyphenation.

I tried to reproduce the logic described in [Frank Liang's thesis](https://tug.org/docs/liang/liang-thesis.pdf),
without using weird data structures and obscure Web2C programming language.

I was able to successfully generate a pattern set, achieving about 3% error on the test set.

However, there is no guarantee that logic implemented here is compatible with Liang's. In fact, its very likely that
this code differs in some subtle details and if you feed the same hyphenation dictionary to original Linag's `patgen` program you 
will get a different set of patterns.

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

Sample training session
=======================

TODO
