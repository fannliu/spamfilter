# Natural Language Toolkit: Tokenizers
#
# Copyright (C) 2001-2011 NLTK Project
# Author: Edward Loper <edloper@gradient.cis.upenn.edu>
# URL: <http://nltk.sourceforge.net>
# For license information, see LICENSE.TXT

"""
A regular-expression based word tokenizer that tokenizes sentences
using the conventions used by the Penn Treebank.
"""

import re
#from api import *

######################################################################
#{ Regexp-based treebank tokenizer
######################################################################
# (n.b., this isn't derived from RegexpTokenizer)

class TreebankWordTokenizer():
    """
    A word tokenizer that tokenizes sentences using the conventions
    used by the Penn Treebank.  Contractions, such as "can't", are
    split in to two tokens.  E.g.:

      - can't S{->} ca n't
      - he'll S{->} he 'll
      - weren't S{-} were n't

    This tokenizer assumes that the text has already been segmented into
    sentences.  Any periods -- apart from those at the end of a string --
    are assumed to be part of the word they are attached to (e.g. for
    abbreviations, etc), and are not separately tokenized.
    """
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
        # may find an issue with /
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
        new_text = self.tokenize_by_web(text)
        # do not split up exclamation points
        curr_exclaimed = []
        ret_text = []
        has_exclaimed = False
        for i in range(len(new_text)):
            if new_text[i] == '!' and not has_exclaimed:
                has_exclaimed = True
                curr_exclaimed.append('!')
            elif new_text[i] == '!' and has_exclaimed:
                curr_exclaimed.append('!')
            elif new_text[i] != '!' and has_exclaimed:
                has_exclaimed = False
                new_exclaim = ''.join(curr_exclaimed)
                ret_text.append(new_exclaim)
            else:
                ret_text.append(new_text[i])
        return ret_text
