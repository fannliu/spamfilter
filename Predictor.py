import time
import glob
import random

import math
import sys
import re
from collections import defaultdict

# tokenizer class given on piazza, with additional tokenization methods
class TreebankWordTokenizer():
    # List of contractions adapted from Robert MacIntyre's tokenizer.
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

    def tokenize(self, text):
        for regexp in self.CONTRACTIONS2:
            text = regexp.sub(r'\1 \2', text)
        for regexp in self.CONTRACTIONS3:
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

    def tokenize_by_web(self, text):
        new_text = self.tokenize(text)
        # find all tokenized html tags
        # this is <word> should have no other words in there
        # </word> should work too
        ret_text = []
        count = 0
        for i in range(len(new_text)):
            if i+2 < len(new_text):
                if new_text[i] == '<' and new_text[i+2] == '>':
                    # then add this as an html tag (potentially make specific tags)
                    count += 1
                    ret_text.append(new_text[i] + new_text[i+1] + new_text[i+2])
                elif count != 0 and count < 2:
                    count += 1
                elif count == 2:
                    count = 0
                else:
                    ret_text.append(new_text[i])
        return ret_text

    def tokenize_by_web_with_overpunc(self, text):
        ret_text = self.tokenize_by_web(text)
        # overpunctuation tokenization (don't split up ===)
        curr_exclaimed = []
        has_exclaimed = False
        punc = ['=']
        next_text = []
        for i in range(len(ret_text)):
            for p in punc:
                if ret_text[i] == p and not has_exclaimed:
                    has_exclaimed = True
                    curr_exclaimed.append(p)
                elif ret_text[i] == p and has_exclaimed:
                    curr_exclaimed.append(p)
                elif ret_text[i] != p and has_exclaimed:
                    has_exclaimed = False
                    new_exclaim = ''.join(curr_exclaimed)
                    next_text.append(new_exclaim)
                else:
                    next_text.append(ret_text[i])
        return next_text

    def tokenize_money(self, text):
        # moneytag = re.compile('($)|(%)|(\d+.\d{2})|(\d+)')
        # try just leaving in digits with their % or $, then
        # count how many tokens are digits with % and $
        digits = re.compile('\.*\d+')
        ret_text = []
        count = 0
        new_text = self.tokenize_by_web_with_overpunc(text)
        num_money_tokens = 0
        for i in range(len(new_text)):
            if i+2 < len(new_text):
                if (new_text[i] == '$' and digits.match(new_text[i+1])) \
                        or (digits.match(new_text[i]) and new_text[i+1] == '%') \
                        or ((new_text[i].lower() == 'click' or \
                                 new_text[i].lower() == 'order') and \
                            (new_text[i+1].lower() == 'here' or \
                                 new_text[i+1].lower() == 'me' or \
                                 new_text[i+1].lower() == 'this' or \
                                 new_text[i+1].lower() == 'now')):
                    # then add this as a whole either $1.00, or 40% etc.
                    count += 1
                    ret_text.append(new_text[i] + new_text[i+1])
                    num_money_tokens += 1
                elif count == 1:
                    count = 0
                else:
                    ret_text.append(new_text[i])
        return (ret_text, num_money_tokens)

    def tokenize_header_strip(self, text):
        r = re.compile("\r*\n\r*\n")
        new_text = r.split(text)
        header = new_text[0]
        hlines = header.split("\r\n")
        h_to_b = []
        hinfo = {}
        hinfo['domains'] = []
        hinfo['subjects'] = []
        hinfo['ips'] = []
        hinfo['from'] = []
        hinfo['content'] = []
        ip = re.compile('Received:.*\[(\d{,3}.\d{,3}.\d{,3}.\d{,3})\]')
        from_email = re.compile('From:.* [<]?(.*@([^>]*))')
        subject = re.compile('Subject: (.*)')
        content_type = re.compile('Content-Type: ([^;]*)')
        for line in hlines:
            m= ip.match(line)
            if m is None:
                m = from_email.match(line)
                if m is None:
                    m = subject.match(line)
                    if m is not None:
                        hinfo['subjects'] += [m.group(1)]
                    else:
                        m = content_type.match(line)
                        if m is not None:
                            hinfo['content'] += [m.group(1)]
                else:
                    hinfo['from'] += [m.group(1)]
                    hinfo['domains'] += [m.group(2)]
            else:
                hinfo['ips'] += [m.group(1)]
        h_keep = []
        for a in hinfo.values():
            h_keep.extend(a)
        hbody = "\r\n".join(h_keep)
        body = "\r\n".join(new_text[1:])
        body += hbody  # keep retained header info in the body
        (tokens, num_money_tokens) = self.tokenize_money(body)
        return [tokens, hinfo, num_money_tokens]

    def tokenize_everything(self, text):
        tokens = self.tokenize_header_strip(text)
        return tokens

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
        self.__punctuation = ['!', '$']

        # additional keys in the countdict:
        self.unknown_key = '\/unknown\/'
        self.punc_key = '\/punc\/'
        self.domain_key = '\/domain\/'
        self.from_key = '\/from\/'
        self.content_key = '\/content\/'

        # do training on spam and ham
        self.__train__()

    def __train__(self):
        '''train model on spam and ham'''
        # Set up the vocabulary for all files in the training set
        vocab = defaultdict(int)
        vocab.update(self.files2countdict(glob.glob(self.__spamFolder+"/*")))
        vocab.update(self.files2countdict(glob.glob(self.__hamFolder+"/*")))

        # vocab for non alphanum characters
        punc_vocab = defaultdict(int)
        punc_vocab.update(self.files2countdict(
                glob.glob(self.__spamFolder+"/*"), punc_only=True))
        punc_vocab.update(self.files2countdict(
                glob.glob(self.__hamFolder+"/*"), punc_only=True))

        # vocab for domains
        domain_vocab = defaultdict(int)
        domain_vocab.update(self.files2countdict(
                glob.glob(self.__spamFolder+"/*"), domain_only=True))
        domain_vocab.update(self.files2countdict(
                glob.glob(self.__hamFolder+"/*"), domain_only=True))

        # vocab for content-type
        content_vocab = defaultdict(int)
        content_vocab.update(self.files2countdict(
                glob.glob(self.__spamFolder+"/*"), content_only=True))
        content_vocab.update(self.files2countdict(
                glob.glob(self.__hamFolder+"/*"), content_only=True))

        # vocab for from emails
        from_vocab = defaultdict(int)
        from_vocab.update(self.files2countdict(
                glob.glob(self.__spamFolder+"/*"), from_only=True))
        from_vocab.update(self.files2countdict(
                glob.glob(self.__hamFolder+"/*"), from_only=True))

        self.__total_num_words = sum(vocab.values())

        # Set all counts to 0
        vocab = defaultdict(int, zip(vocab.iterkeys(), [0 for i in vocab.values()]))
        punc_vocab = defaultdict(int, zip(punc_vocab.iterkeys(),
                                          [0 for i in punc_vocab.values()]))
        domain_vocab = defaultdict(int, zip(domain_vocab.iterkeys(),
                                            [0 for i in domain_vocab.values()]))
        content_vocab = defaultdict(int, zip(content_vocab.iterkeys(),
                                            [0 for i in content_vocab.values()]))
        from_vocab = defaultdict(int, zip(content_vocab.iterkeys(),
                                            [0 for i in from_vocab.values()]))

        for category in self.__categories:
            # Initialize to zero counts
            countdict = defaultdict(int, vocab)
            countdict_punc = defaultdict(int, punc_vocab)
            countdict_domain = defaultdict(int, domain_vocab)
            countdict_content = defaultdict(int, content_vocab)
            countdict_from = defaultdict(int, from_vocab)
            # Add in counts from this class
            tokens = self.files2countdict(glob.glob(category+"/*"))
            countdict.update(tokens)
            countdict_punc.update(self.files2countdict(
                    glob.glob(category+"/*"), punc_only=True))
            countdict_domain.update(self.files2countdict(
                    glob.glob(category+"/*"), domain_only=True))
            countdict_content.update(self.files2countdict(
                    glob.glob(category+"/*"), content_only=True))
            countdict_from.update(self.files2countdict(
                    glob.glob(category+"/*"), from_only=True))
            # Here turn the "countdict" dictionary of word counts into
            # into a dictionary of smoothed word probabilities
            m = 1000.0

            x = len(countdict) + 1 # add 1 for the 'unknown' key
            x_d = len(countdict_domain) + 1
            x_c = len(countdict_content) + 1
            x_f = len(countdict_from) + 1

            category_num_words = sum(countdict.values()) + (x/m)
            category_num_punc = sum(countdict_punc.values()) # NO smoothing?
            for key in countdict:
                val = (countdict[key] + 1/m)/category_num_words
                countdict[key] = val
            countdict[self.unknown_key] = (1/m)/category_num_words


            # punctuation step, same punctuation is included in words
            for p in self.__punctuation:
                if p in countdict:
                    countdict[self.punc_key+p] = float(countdict_punc[p])/category_num_punc

            # stripped header step
            # domains
            category_num_domains = sum(countdict_domain.values()) + (x_d/m)
            for key in countdict_domain:
                countdict[self.domain_key + key] = (countdict_domain[key] + 1/m)/category_num_domains
            # smooth domains
            countdict[self.domain_key + self.unknown_key] = (1/m)/category_num_domains

            # from
            category_num_from = sum(countdict_from.values()) + (x_d/m)
            for key in countdict_from:
                countdict[self.from_key + key] = (countdict_from[key] + 1/m)/category_num_from
            # smooth from emails
            countdict[self.from_key + self.unknown_key] = (1/m)/category_num_from

            # content type
            category_num_content = sum(countdict_content.values()) + (x_c/m)
            for key in countdict_content:
                countdict[self.content_key + key] = (countdict_content[key] + 1/m)/category_num_content
            # smooth content types
            countdict[self.content_key + self.unknown_key] = (1/m)/category_num_content

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
            domains = self.files2countdict([filename], domain_only=True)
            content_types = self.files2countdict([filename], content_only=True)

            for token in tokens:
                key = token

                # punctuation step
                if token in self.__punctuation:
                    p_key = self.punc_key + key
                    score += (math.log(countdict[p_key])*tokens[token])

                if token not in countdict:
                    key = self.unknown_key
                score += (math.log(countdict[key])*tokens[token])

            # domain step
            for domain in domains:
                key = self.domain_key + domain
                if key not in countdict:
                    key = self.domain_key + self.unknown_key
                score += (math.log(countdict[key])*domains[domain])

            # content type step
            for content in content_types:
                key = self.content_key + content
                if key not in countdict:
                    key = self.content_key + self.unknown_key
                score += (math.log(countdict[key])*content_types[content])

            # remove any non float values from the countdict
            score += math.log(sum(countdict.values())/self.__total_num_words)
            answers.append((score, category))


        answers.sort()
        print answers
        if answers[1][1] == self.__spamFolder:
            return True
        else:
            return False

    def files2countdict (self, files, punc_only=False, domain_only=False, content_only=False,
                         from_only=False):
        """Given an array of filenames, return a dictionary with keys
        being the space-separated, lower-cased words, and the values being
        the number of times that word occurred in the files."""
        d = defaultdict(int)
        for file in files:
            [tokens, hinfo, num_money_tokens] = self.__tokenizer.tokenize_everything(open(file).read())
            if domain_only:
                for domain in hinfo['domains']:
                    d[domain.lower()] += 1
            elif content_only:
                for content in hinfo['content']:
                    d[content.lower()] += 1
            elif from_only:
                for content in hinfo['from']:
                    d[content.lower()] += 1
            else:
                d['num_capitalized_words'] = 0 # for some reason this is higher for ham?
                for word in tokens:
                    if not punc_only:
                        if word.isupper(): # only completely capitalized words
                            d['num_capitalized_words'] += 1
                    d[word.lower()] += 1
                else:
                    if not word.isalnum():
                        for char in word:
                            if not char.isalnum():
                                d[char] += 1
                if num_money_tokens != -1:
                    d['num_money_tokens'] = num_money_tokens
        return d

if __name__ == '__main__':
    print 'argv', sys.argv
    print "Usage:", sys.argv[0], "spamdirectory hamdirectory testdirectory"
    dirs = sys.argv[1:-1]
    testfiles = glob.glob(sys.argv[-1]+"/*")

    predictor = Predictor(sys.argv[1], sys.argv[2])

    num_ham = 0.0
    num_spam = 0.0

    for testfile in testfiles:
        s = predictor.predict(testfile, r)
        # true if it's spam, false if not
        if not s:
            num_ham += 1
        else:
            num_spam += 1

    print 'spam: ' + str(num_spam/len(testfiles))
    print 'ham: ' + str(num_ham/len(testfiles))
