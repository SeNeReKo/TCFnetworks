#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 Frederik Elwert <frederik.elwert@web.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This annotator base class implements common token tests.

This class does not work as a worker by itself, but rather works as a base class
for implementing workers.

"""

import sys
import os
import logging
from types import MethodType

from tcflib.service import AddingWorker
from tcflib.tagsets import TagSet

ISOcat = TagSet('DC-1345')
PUNCT = ISOcat['punctuation']
VERB = ISOcat['verb']
ADVERB = ISOcat['adverb']


class TokenTestingWorker(AddingWorker):

    __options__ = {
        'nodes': 'lexical',
        'label': 'semantic_unit',
        'stopwords': [''],
        'stopwords_preset': '',
        'stopwords_feature': 'text',
        'postag': [''],
    }

    def __init__(self, **options):
        super().__init__(**options)
        # Set up stop-words
        self.stopwords = []
        if self.options.stopwords and self.options.stopwords[0]:
            self.stopwords.extend(self.options.stopwords)
        if self.options.stopwords_preset:
            stopwordspath = os.path.join(os.path.dirname(__file__),
                                         'data', 'stopwords',
                                         self.options.stopwords_preset)
            try:
                with open(stopwordspath) as stopwordsfile:
                    stopwords = [token.strip() for token
                                 in stopwordsfile.readlines() if token]
                    self.stopwords.extend(stopwords)
            except FileNotFoundError:
                logging.error('No stopwords list "{}".'.format(
                        self.options.stopwords_preset))
                sys.exit(-1)
        # Set up filtering.
        # First, check hard-coded variants
        if self.options.nodes == 'postag':
            # The `postag` filter method allows to specify a PoS tag directly
            # through the `postag` option, e.g.: --nodes postag --postag noun
            if not self.options.postag or not self.options.postag[0]:
                logging.error('Method "postag" requires specifying option '
                              '"postag" as well.')
                sys.exit(-1)
            try:
                POS = [ISOcat[postag] for postag in self.options.postag]
            except KeyError:
                logging.error('No postag "{}" in tagset.'.format(
                              self.options.postag))
                sys.exit(-1)
            def test_token_postag(self, token, resolve=True):
                has_pos = False
                for postag in POS:
                    if token.postag.is_a(postag):
                        has_pos = True
                        break
                if has_pos:
                    return self.test_token_stopwords(token)
                if resolve and token.reference is not None:
                    for reftoken in token.reference.tokens:
                        if test_token_postag(self, reftoken, False):
                            return self.test_token_stopwords(reftoken)
                return False
            self.test_token = MethodType(test_token_postag, self)
        # Then, check dynamic variants
        else:
            try:
                self.test_token = getattr(self,
                        'test_token_{}'.format(self.options.nodes))
            except AttributeError:
                logging.error('Method "{}" is not supported.'.format(
                        self.options.nodes))
                sys.exit(-1)

    def test_token(self):
        logging.warn('No token test method set.')

    def test_token_stopwords(self, token):
        if getattr(token, self.options.stopwords_feature) in self.stopwords:
                return False
        return True

    def test_token_full(self, token):
        if token.postag.is_a(PUNCT):
            return False
        return self.test_token_stopwords(token)

    def test_token_nonclosed(self, token):
        if token.postag.is_closed:
            return False
        return self.test_token_stopwords(token)

    def test_token_lexical(self, token):
        if not token.postag.is_closed and not token.postag.is_a(ADVERB):
            return self.test_token_stopwords(token)
        if token.entity is not None:
            return True
        if token.reference is not None:
            return True
        return False

    def test_token_semantic(self, token):
        if token.postag.is_a(VERB):
            return True
        if not token.postag.is_closed and not token.postag.is_a(ADVERB):
            return self.test_token_stopwords(token)
        if token.entity is not None:
            return True
        if token.reference is not None:
            return True
        return False

    def test_token_concept(self, token):
        if not self.test_token_semantic(token):
            return False
        if token.postag.is_a(VERB):
            return False
        return True

    def test_token_entity(self, token, resolve=True):
        if token.entity is not None:
            return True
        if resolve and token.reference is not None:
            for reftoken in token.reference.tokens:
                if self.test_token_entity(reftoken, False):
                    return True
        return False

    def test_token_actor(self, token, resolve=True):
        if token.entity is not None:
            if token.entity.class_ in ('PER', 'ORG'):
                # FIXME: Use proper tags instead of hardcoded CoNLL2002 tags.
                return True
        if resolve and token.reference is not None:
            for reftoken in token.reference.tokens:
                if self.test_token_actor(reftoken, False):
                    return True
        return False
