
# Modified from code by Andrew McCallum of UMass Amherst

# Your job is to replace the two sections marked below with code and
# run the classifier on test files.

import math
import sys
import glob
import pickle
from collections import defaultdict
# import nltk
from treebank import TreebankWordTokenizer
import string
import re

m = 1000.0

# test 3 specific punctuation (this may be problematic for non english emails...)
def punc_training(dirs):
    """Train by punctuation"""
    """Special characters to look for: !, *, %, $, ^ <= though those two are money tag"""
    """Characters that are fine: ., @, &, +, -, anything not an alphabet or digit but
    what about emails in other languages?"""
    # Set up the vocabulary for all files in the training set
    vocab = defaultdict(int)
    for dir in dirs:
        vocab.update(files2countdict(glob.glob(dir+"/*"), has_alphanum=False))
    # Set all counts to 0
    classes = []
    total_num_punc_all_docs = sum(vocab.values())
    vocab = defaultdict(int, zip(vocab.iterkeys(), [0 for i in vocab.values()]))
    for dir in dirs:
        print dir
        # Initialize to zero counts
        countdict = defaultdict(int, vocab)
        # Add in counts from this class
        countdict.update(files2countdict(glob.glob(dir+"/*"), has_alphanum=False))
        # turn into a dictionary of smoothed punctuation probabilities
        total_num_punc = float(sum(countdict.values()))
        # we want specifically the punctuation: !, *
        #punc = ['!', '*']
        total_num_spam_punc = 0.0
        #for p in punc:
        #    if p in countdict:
        #        total_num_spam_punc += countdict[p]
        #for p in punc:
        #    if p in countdict:
        #        print "num of special char " + p + " is " + str(countdict[p])
        x = len(countdict)
        sum_val = 0.0
        for char in countdict: # this will calculate for all punctuation
            countdict[char] = (countdict[char] + 1/m)/(total_num_punc + x/m)
            sum_val += countdict[char]
        #print sum_val
        #print "the total number of spam punc is " + str(total_num_spam_punc)
        #print "the total num of punc all docs is " + str(total_num_punc_all_docs)
        print "the p(this cat) is " + str(total_num_punc/total_num_punc_all_docs)
        classes.append([dir, countdict, total_num_punc, total_num_spam_punc])
    return (classes, total_num_punc_all_docs)

def punc_classify(classes, filename):
    """Classify by punctuation"""
    answers = []
    print 'Classifying', filename
    categories = classes[0]
    total_num_punc_all_docs = classes[1]
    for c in categories: #classes:
        score = 0 # this is 0 because log products will sum
        countdict = c[1]
        # for every x_i in the document find the P(x_i | c)
        tokens = tokenize_file(filename, has_alphanum=False)
        x = len(countdict)
        # first update the probabilities
#        punc = ['!', '*']
        total_num_punc = c[2] + x/m
        total_num_spam_punc = c[3]
 #       for p in punc:
 #           if p in tokens and p not in countdict:
 #               countdict[p] = (1/m)/total_num_punc
 #       for p in punc:
 #           if p in tokens:
 #               score += math.log(countdict[p])
        for token in tokens:
            if token not in countdict:
                #total_num_punc += 1/m
                #for countdict_token in countdict: # update all the probs
                #    countdict[countdict_token] *= ((total_num_punc-(1/m))/total_num_punc)
                countdict[token] = (1/m)/total_num_punc # add the new probability
        # now product it up
        for token in tokens:
        #    if token in punc:
            score += math.log(countdict[token])
        # we also need to add on the log(P(c))
        # P(c) is all words in a category / all words in all N documents
        score += math.log(total_num_punc/total_num_punc_all_docs) 
        answers.append((score, c[0]))
    # answers.sort()
    return answers

# test 1 (capitalized characters)
def cap_training(dirs):
    """Train by capitalization"""
    # Set up the vocabulary for all files in the training set
    vocab = defaultdict(int)
    for dir in dirs:
        vocab.update(files2countdict(glob.glob(dir+"/*"), False))
    # Set all counts to 0
    vocab = defaultdict(int, zip(vocab.iterkeys(), [0 for i in vocab.values()]))
    cap_characters = {}
    for char in string.uppercase:
        cap_characters[char] = 0
    classes = []
    total_num_characters_all_docs = 0 # potentially add just alphanumeric characters
    for dir in dirs:
        print dir
        # Initialize to zero counts
        countdict = defaultdict(int, vocab)
        # Add in counts from this class
        countdict.update(files2countdict(glob.glob(dir+"/*"), False))
        # turn into a dictionary ofsmoothed CAPS probabilities
        for key in countdict:
            if key.islower():
                continue
            else:
                # get every character of this key TIMES the number of times
                # this key shows up
                val = countdict[key]
                for char in key:
                    if char.isupper():
                        cap_characters[char] += val
            char_only_word = "".join(re.findall("[a-zA-Z]+", key))
            total_num_characters_all_docs += (len(char_only_word)*countdict[key])
        # now update cap characters to reflect probabilities
        total_num_characters = sum(cap_characters.values())
        x = len(cap_characters)
        for char in cap_characters:
            cap_characters[char] = (cap_characters[char] + 1/m)/(total_num_characters + x/m)
        classes.append([dir, cap_characters, total_num_characters])
    return (classes, total_num_characters_all_docs)

def cap_classify(classes, filename):
    answers = []
    print 'Classifying', filename
    categories = classes[0]
    total_num_characters_all_docs = classes[1]
    for c in categories:
        score = 0 # this is 0 because log products will sum
        # ***
        # Here, compute the naive bayes score for a file for a given class by:
        # 1. Reading in each word, and converting it to lower case (see code below)
        # 2. Adding  the log probability of that word for that class
        # ***
        cap_characters = c[1]
        # for every x_i in the document find the P(x_i | c)
        tokens = tokenize_file(filename, False)
        x = len(cap_characters)
        # first update the probabilities
        total_num_characters = c[2] + x/m
        for token in tokens:
            if token.islower():
                continue
            else:
                for char in token:
                    if char.isupper():
                        if char not in cap_characters:
                            cap_characters[char] = (1/m)/total_num_characters # add the new probability
        # now product it up
        for token in tokens:
            if token.islower():
                continue
            else:
                for char in token:
                    if char.isupper():
                        if char not in cap_characters:
                            print "Error: token was not properly added to cap_characters"
                        else:
                            score += math.log(cap_characters[char])
        # we also need to add on the log(P(c))
        # P(c) is all words in a category / all words in all N documents
        score += math.log(total_num_characters/total_num_characters_all_docs)
        answers.append((score, c[0]))
    # answers.sort()
    return answers

def naivebayes (dirs):
    """Train and return a naive Bayes classifier.
    The datastructure returned is an array of tuples, one tuple per
    class; each tuple contains the class name (same as dir name)
    and the multinomial distribution over words associated with
    the class"""
    # Set up the vocabulary for all files in the training set
    vocab = defaultdict(int)
    for dir in dirs:
        vocab.update(files2countdict(glob.glob(dir+"/*")))

    total_num_words_all_docs = sum(vocab.values())
    # Set all counts to 0
    vocab = defaultdict(int, zip(vocab.iterkeys(), [0 for i in vocab.values()]))

    classes = []
    for dir in dirs:
        print dir
        # Initialize to zero counts
        countdict = defaultdict(int, vocab)
        # Add in counts from this class
        countdict.update(files2countdict(glob.glob(dir+"/*")))
        # Here turn the "countdict" dictionary of word counts into
        # into a dictionary of smoothed word probabilities
        x = len(countdict) + 1 # or len vocab?
        total_num_words = sum(countdict.values()) + (x/m)
        for key in countdict:
            val = (countdict[key] + 1/m)/total_num_words
            countdict[key] = val
        # check the sum and make sure it's 1
        countdict['\/unknown\/'] = (1/m)/total_num_words
        classes.append([dir, countdict, total_num_words])
    return (classes, total_num_words_all_docs) # MODIFIED return

def classify (classes, filename):
    """Given a trained naive Bayes classifier returned by naivebayes(), and
    the filename of a test document, d, return an array of tuples, each
    containing a class label; the array is sorted by log-probability
    of the class, log p(c|d)"""
    answers = []
    print 'Classifying', filename
    # changed the return value to add the total number of all words in all docs
    categories = classes[0]
    total_num_words_all_docs = classes[1]
    for c in categories: #classes:
        score = 0 # this is 0 because log products will sum
        # ***
        # Here, compute the naive bayes score for a file for a given class by:
        # 1. Reading in each word, and converting it to lower case (see code below)
        # 2. Adding  the log probability of that word for that class
        # ***
        countdict = c[1]
        tokens = files2countdict([filename]) #tokenize_file(filename)#files2countdict([filename])
        x = len(countdict)
        for token in tokens:
            key = token
            if token not in countdict:
                key = '\/unknown\/'
            score += (math.log(countdict[key])*tokens[token])
        score += math.log(sum(countdict.values())/total_num_words_all_docs)
        answers.append((score, c[0]))
    # answers.sort()
    return answers

def files2countdict (files, to_lower=True, has_alphanum=True):
    """Given an array of filenames, return a dictionary with keys
    being the space-separated, lower-cased words, and the values being
    the number of times that word occurred in the files."""
    d = defaultdict(int)
    d['num_capitalized_words'] = 0
    for file in files:
        # for word in nltk.word_tokenize(open(file).read()): #.split():
        # for word in nltk.regexp_tokenize(open(file).read(), pattern=r'\w+([.,]\w+)*|\S+'):
        t =TreebankWordTokenizer()
        for word in t.tokenize_by_web_with_overpunc(open(file).read()):
            if has_alphanum:
                if word.isupper():
                    d['num_capitalized_words'] += 1
                if to_lower:
                    d[word.lower()] += 1
                else:
                    d[word] += 1
            else:
                if not word.isalnum():
                    for char in word:
                        if not char.isalnum():
                            d[char] += 1
    return d

if __name__ == '__main__':
    print 'argv', sys.argv
    print "Usage:", sys.argv[0], "classdir1 classdir2 [classdir3...] testfile"
    dirs = sys.argv[1:-1]
    testfiles = glob.glob(sys.argv[-1]+"/*")
    # use the first 200 as testfiles
    nb = naivebayes (dirs)
#    cap = cap_training(dirs)
#    punc = punc_training(dirs)
    spam = 'spamham/spam'
    ham = 'spamham/ham'
    wrong = 0.0
    for testfile in testfiles:
        s = classify(nb, testfile)
#        c = cap_classify(cap, testfile)
#        p = punc_classify(punc, testfile)
#        print "the first one is " + p[0][1]
#        print "the second one is " + p[1][1]
#        sp = [(p[0][0], p[0][1]), (p[1][0], p[1][1])]
#        sp = [(0*s[0][0] + 0*c[0][0] + 1*p[0][0], c[0][1]),
#              (0*s[1][0] + 0*c[1][0] + 1*p[1][0], s[1][1])]
        s.sort()
        print s
        if s[1][1] != spam:
            wrong += 1
    print wrong
    print wrong/len(testfiles)
 #   pickle.dump(nb, open("classifier.pickle",'w'))
