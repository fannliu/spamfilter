# Modified from code by Andrew McCallum of UMass Amherst

# Your job is to replace the two sections marked below with code and
# run the classifier on test files.

from numpy import log
#from nltk import *
import os
import re
import math
import sys
import glob
import pickle
from collections import defaultdict

# In the documentation and variable names below "class" is the same
# as "category"

priors = {}
domain_vocab = defaultdict(int)
money_vocab = defaultdict(int)
alldomains = defaultdict(int)
allmoney = defaultdict(int)
wm = 0.0
wt = 1.0
wd = 0.0

def naivebayes (dirs):
    """Train and return a naive Bayes classifier.  
    The datastructure returned is an array of tuples, one tuple per
    class; each tuple contains the class name (same as dir name)
    and the multinomial distribution over words associated with
    the class"""
    # Set up the vocabulary for all files in the training set
    global priors
    vocab = defaultdict(int)
    count_class = {}
    totalN = 0
    for dir in dirs:
        vocab.update(files2countdict(glob.glob(dir+"/*")))
        totalN += len(glob.glob(dir+"/*"))
        count_class[dir] = len(glob.glob(dir+"/*"))
    # Set all counts to 0
    for key in count_class:
        priors[key] = 1 / float(sum(vocab.values()) + 2)  # WRONG
    vocab = defaultdict(int, zip(vocab.iterkeys(), [0 for i in vocab.values()]))
    classes = []
    domain_classes = []
    for dir in dirs:
        print dir
        # Initialize to zero counts
        countdict = defaultdict(int, vocab)
        # Add in counts from this class
        countdict.update(files2countdict(glob.glob(dir+"/*")))
        #***
        # Here turn the "countdict" dictionary of word counts into
        # into a dictionary of smoothed word probabilities
        #***
        total_count = float(sum(countdict.values()))
        for key in countdict:
            countdict[key] = (countdict[key] + 1/100.0) / (total_count  + (1+len(vocab))/100.0)
        countdict["\/unknown\/"]  = (1/100.0) / (total_count + (1+len(vocab))/100.0)

        priors[dir] = priors[dir] * total_count

        total_count = float(sum(alldomains.values()) + 1.0)
        for key in alldomains:
            alldomains[key] = (alldomains[key] + 1/100.0) / (total_count  + (1+len(domain_vocab))/100.0)
        alldomains["\/unknown\/"]  = (1/100.0) / (total_count + (1+len(domain_vocab))/100.0)

        total_count = float(sum(allmoney.values()) )
        for key in allmoney:
            allmoney[key] = (allmoney[key] + 1/100.0) / (total_count  + (len(money_vocab))/100.0)
        #allmoney["\/unknown\/"]  = (1/100.0) / (total_count + (1+len(money_vocab))/100.0)
        
        classes.append((dir,countdict,alldomains, allmoney))
    return classes

def classify (classes, filename):
    """Given a trained naive Bayes classifier returned by naivebayes(), and
    the filename of a test document, d, return an array of tuples, each
    containing a class label; the array is sorted by log-probability 
    of the class, log p(c|d)"""
    answers = []
    print 'Classifying', filename
    moneytag = re.compile('($)|(%)|(\d+.\d{2})|(\d+)')
    for c in classes:
        score = 0
        #***
        # Here, compute the naive bayes score for a file for a given class by:
        # 1. Reading in each word, and converting it to lower case (see code below)
        # 2. Adding  the log probability of that word for that class
        #***
        likelihood = (c[1])
        domain_likelihood = c[2]
        money_likelihood = c[3]
        header = True
        for line in open(filename, 'r'):
            if line == "\n":
                header = False
            ip = re.compile('Received:.*\[(\d{,3}.\d{,3}.\d{,3}.\d{,3})\]')
            from_email = re.compile('From:.*<(.*@(.*))>')
            subject = re.compile('Subject: (.*)')

            m= ip.match(line)
            domain = None
            if m is None:
                m = from_email.match(line)
                if m is None:
                    m = subject.match(line)
                else:
                    domain = m.group(2)
            if m is not None:
                line = m.group(1)
                if domain is not None:
                    if domain not in domain_likelihood:
                        domain = "\/unknown\/"
                    score += wd*log(domain_likelihood[domain.lower()])
                    if log(domain_likelihood[domain.lower()]) == float('nan'):
                        with open("output.err", "a") as myfile:
                            myfile.write(filename + "\t" +str(domain.lower())+"\t"+str(domain_likelihood)+"\t"+ str("domain") + "\n")
            if True: # do we want to use else here?
                for m in moneytag.findall(line):
                    for i in range(4):
                        if m[i] is not '':
                            score += wm*log(money_likelihood[i])
                            if log(money_likelihood[i]) == float('nan'):
                                with open("output.err", "a") as myfile:
                                    myfile.write(filename + "\t" +str(money_likelihood[i])+"\t"+str(money_likelihood)+"\t"+ str("money") + "\n") 
                for token in tokenize(line):
                    if token not in likelihood:
                        token = "\/unknown\/"
                    score += wt*log(likelihood[token.lower()])
                    if log(likelihood[token.lower()]) == float('nan'):
                        with open("output.err", "a") as myfile:
                            myfile.write(filename + "\t" +str(token.lower())+"\t"+str(likelihood)+"\t"+ str("likelihood") + "\n")

            score += log(priors[c[0]])
            if log(priors[c[0]]) == float('nan'):
                with open("output.err", "a") as myfile:
                    myfile.write(filename + "\t" +str(c[0])+"\t"+str(priors)+"\t"+ str("priors") + "\n")

        answers.append((score, c[0]))
    answers.sort(reverse=True)
    with open("output.out2", "a") as myfile:
        myfile.write(filename + "\t" + str(answers[0][1]) + "\n")
    print answers
    return answers


def files2countdict (files):
    """Given an array of filenames, return a dictionary with keys
    being the space-separated, lower-cased words, and the values being
    the number of times that word occurred in the files."""
    global domain_vocab
    global money_vocab
    global alldomains 
    global allmoney
    d = defaultdict(int)
    moneytag = re.compile('($)|(%)|(\d+.\d{2})|(\d+)')
    alldomains = defaultdict(int)
    allmoney = defaultdict(int)
    for file in files:
        header = True
        for line in open(file):
            if line == "\n":
                header = False
            if header is True:
                #regex and only keep relevant stuff in headers
                ip = re.compile('Received:.*\[(\d{,3}.\d{,3}.\d{,3}.\d{,3})\]')
                from_email = re.compile('From:.*<(.*@(.*))>')
                subject = re.compile('Subject: (.*)')

                m= ip.match(line)
                domain = None
                if m is None:
                    m = from_email.match(line)
                    if m is None:
                        m = subject.match(line)
                    else:
                        domain = m.group(2)
                if m is not None:
                    line = m.group(1)
                if domain is not None:
                    alldomains[domain] += 1
                    domain_vocab[domain] = 0
            if True: # do we want to use else here?
                for m in moneytag.findall(line):
                    for i in range(4):
                        if m[i] is not '':
                            allmoney[i] += 1
                            money_vocab[i] = 0
                tokens = tokenize(line)
                for word in tokens:
                    d[word.lower()] += 1
    return d


CONTRACTIONS2 = [re.compile(r"(?i)(.)('ll|'re|'ve|n't|'s|'m|'d)\b"),
    re.compile(r"(?i)\b(can)(not)\b"),
    re.compile(r"(?i)\b(D)('ye)\b"),
    re.compile(r"(?i)\b(Gim)(me)\b"),
    re.compile(r"(?i)\b(Gon)(na)\b"),
    re.compile(r"(?i)\b(Got)(ta)\b"),
    re.compile(r"(?i)\b(Lem)(me)\b"),
    re.compile(r"(?i)\b(Mor)('n)\b"),
    re.compile(r"(?i)\b(T)(is)\b"),
    re.compile(r"(?i)\b(T)(was)\b"),
    re.compile(r"(?i)\b(Wan)(na)\b")]
CONTRACTIONS3 = [re.compile(r"(?i)\b(Whad)(dd)(ya)\b"),
    re.compile(r"(?i)\b(Wha)(t)(cha)\b")]
 
def tokenize(text):
    for regexp in CONTRACTIONS2:
        text = regexp.sub(r'\1 \2', text)
    for regexp in CONTRACTIONS3:
        text = regexp.sub(r'\1 \2 \3', text)
 
    # Separate most punctuation
    text = re.sub(r"([^\w\.\'\-\/,&])", r' \1 ', text)
 
    # Separate commas if they're followed by space.
    # (E.g., don't separate 2,500)
    text = re.sub(r"(,\s)", r' \1', text)
 
    # Separate single quotes if they're followed by a space.
    text = re.sub(r"('\s)", r' \1', text)
 
    # Separate periods that come before newline or end of string.
    text = re.sub('\. *(\n|$)', ' . ', text)
 
    return text.split()
 

if __name__ == '__main__':
    #print 'argv', sys.argv
    #print "Usage:", sys.argv[0], "classdir1 classdir2 [classdir3...] testfile"
    try:
        os.remove("output.out")
    except OSError:
        pass
    wt = float(sys.argv[-3])
    wd = float(sys.argv[-2])
    wm = float(sys.argv[-1])
    wd *= 1/10
    wt *= 1/10
    wm *= 1/10
    dirs = sys.argv[1:-4]
    testfile = sys.argv[-4]
    nb = naivebayes (dirs)
    #print classify(nb, testfile)
    for file in glob.glob(testfile+"/*"):
        classify(nb, file)
    #classify(nb, testfile)
    pickle.dump(nb, open("classifier.pickle",'w'))
