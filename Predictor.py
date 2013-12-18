import time
import glob
import random

import math
import sys
from collections import defaultdict
from treebank import TreebankWordTokenizer

class Predictor:
    '''
    Predictor which will do prediction on emails
    '''
    def __init__(self, spamFolder, hamFolder):
        self.__createdAt = time.strftime("%d %b %H:%M:%S", time.gmtime())
        self.__spamFolder = spamFolder
        self.__hamFolder = hamFolder
        self.__categories = {spamFolder: 0, hamFolder: 0}
        self.__tokenizer = TreebankWordTokenizer()
        # do training on spam and ham
        self.__train__()

    def __train__(self):
        '''train model on spam and ham'''
        # Set up the vocabulary for all files in the training set
        vocab = defaultdict(int)
        vocab.update(self.files2countdict(glob.glob(self.__spamFolder+"/*")))
        vocab.update(self.files2countdict(glob.glob(self.__hamFolder+"/*")))

        self.__total_num_words = sum(vocab.values())
        # Set all counts to 0
        vocab = defaultdict(int, zip(vocab.iterkeys(), [0 for i in vocab.values()]))

        for category in self.__categories:
            # Initialize to zero counts
            countdict = defaultdict(int, vocab)
            # Add in counts from this class
            countdict.update(self.files2countdict(glob.glob(category+"/*")))
            # Here turn the "countdict" dictionary of word counts into
            # into a dictionary of smoothed word probabilities
            m = 1000.0
            x = len(countdict) + 1 # add 1 for the 'unknown' key
            num_unique_words = sum(countdict.values()) + (x/m)
            for key in countdict:
                val = (countdict[key] + 1/m)/num_unique_words
                countdict[key] = val
            countdict['\/unknown\/'] = (1/m)/num_unique_words

            self.__categories[category] = countdict

    def predict(self, filename):
        '''Take in a filename, return whether this file is spam
        return value:
        True - filename is spam
        False - filename is not spam (is ham)
        '''
        # do prediction on filename
        print 'Classifying', filename
        answers = []
        for category in self.__categories:
            # ***
            # Here, compute the naive bayes score for a file for a given class by:
            # 1. Reading in each word, and converting it to lower case (see code below)
            # 2. Adding  the log probability of that word for that class
            # ***
            score = 0
            countdict = self.__categories[category]
            tokens = self.files2countdict([filename])
            x = len(countdict)
            for token in tokens:
                key = token
                if token not in countdict:
                    key = '\/unknown\/'
                score += (math.log(countdict[key])*tokens[token])
            score += math.log(sum(countdict.values())/self.__total_num_words)
            answers.append((score, category))
        answers.sort()
        if answers[1][1] == self.__spamFolder:
            return True
        else:
            return False

    def files2countdict (self, files, to_lower=True, has_alphanum=True):
        """Given an array of filenames, return a dictionary with keys
        being the space-separated, lower-cased words, and the values being
        the number of times that word occurred in the files."""
        d = defaultdict(int)
        d['num_capitalized_words'] = 0
        for file in files:
            for word in self.__tokenizer.tokenize_everything(open(file).read()):
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
    print "Usage:", sys.argv[0], "spamdirectory hamdirectory testdirectory"
    dirs = sys.argv[1:-1]
    testfiles = glob.glob(sys.argv[-1]+"/*")

    predictor = Predictor(sys.argv[1], sys.argv[2])

    wrong = 0.0
    for testfile in testfiles:
        s = predictor.predict(testfile)
        # true if it's spam, false if not
        if s:
            print testfile + ' is spam'
        else:
            print testfile + ' is ham'
            wrong += 1
    print wrong
    print wrong/len(testfiles)