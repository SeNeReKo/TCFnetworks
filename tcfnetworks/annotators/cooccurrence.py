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
This annotator implements cooccurrence networks as a TCF compatible service.

"""

import sys
import os
import logging
from itertools import combinations
from collections import Counter
from math import log

from tcflib import tcf
from tcflib.service import run_as_cli

from tcfnetworks.annotators.base import TokenTestingWorker


class CooccurrenceWorker(TokenTestingWorker):

    __options__ = TokenTestingWorker.__options__.copy()
    __options__.update({
        'method': 'window',  # 'window', 'sentence' or 'textspan'
        'spantype': '',
        'window': [2, 5],  # for method='window'
        'weight': 'count',  # 'count' or 'loglikelihood'
        'type': 'postag',  # 'postag' (possibly other options in the future)
    })

    def __init__(self, **options):
        super().__init__(**options)
        try:
            self.build_graph = getattr(self,
                    'build_graph_{}'.format(self.options.method))
        except AttributeError:
            logging.error('Method "{}" is not supported.'.format(
                    self.options.method))
            sys.exit(-1)

    def add_annotations(self):
        graph = self.build_graph()
        logging.info('Graph has {} nodes and {} edges.'.format(
                len(graph.nodes),
                len(graph.edges)))
        self.corpus.graph = graph

    def build_graph(self):
        logging.warn('No graph building method set.')

    def build_graph_window(self):
        """
        This method implements a word-window based cooccurrence network.

        This implementation is based on the method and algorithm described in:
        Paranyushkin, Dmitry. 2011. „Identifying the Pathways for Meaning 
        Circulation using Text Network Analysis“. Nodus Labs.
        <http://noduslabs.com/research/
        pathways-meaning-circulation-text-network-analysis/>.

        """
        graph = None
        for window in self.options.window:
            logging.info('Building network with window {}.'.format(window))
            if self.options.spantype:
                # When passing the spantype parameter, the network is built for
                # each span (e.g., paragraph) separately.
                textspans = [span for span in self.corpus.textstructure
                             if span.type == self.options.spantype]
                for span in textspans:
                    tokens = [token for token in span.tokens
                                  if self.test_token(token)]
                    graph = self.build_graph_window_real(tokens, window, graph)
            else:
                tokens = [token for token in self.corpus.tokens
                              if self.test_token(token)]
                graph = self.build_graph_window_real(tokens, window, graph)
        return graph

    def build_graph_window_real(self, tokens, window=2, graph=None):
        """
        This function does all the heavy-lifting of creating a graph from
        a list of words in a paragraph. It expects to get a list of tokens.

        :parameters:
            - `tokens`: A list of tokens.
            - `window`: The word window for detecting edges.
            - `graph`: A graph node to which the edges will be added.
        :returns:
            - The graph node.

        """
        if graph == None:
            graph = tcf.Graph(label=self.options.label,
                              weight=self.options.weight,
                              type=self.options.type)
        for token in tokens:
            graph.node_for_token(token)
        for i in range(len(tokens) - (window - 1)):
            # try all combinations of words within window
            for combo in combinations(tokens[i:i + window], 2):
                graph.edge_for_tokens(*combo)
        return graph

    def build_graph_textspan(self):
        if self.options.spantype:
            textspans = [span for span in self.corpus.textstructure
                         if span.type == self.options.spantype]
        else:
            textspans = self.corpus.textstructure
        return self.build_graph_textspan_real(textspans)

    def build_graph_sentence(self):
        return self.build_graph_textspan_real(self.corpus.sentences)

    def build_graph_textspan_real(self, textspans):
        graph = tcf.Graph(label=self.options.label, weight=self.options.weight,
                          type=self.options.type)
        n = len(textspans)
        for i, span in enumerate(textspans, start=1):
            logging.debug('Creating network for textspan {}/{}.'.format(i, n))
            tokens = set([token for token in span.tokens
                          if self.test_token(token)])
            logging.debug('Using {} tokens.'.format(len(tokens)))
            for token in tokens:
                graph.node_for_token(token)
            for combo in combinations(tokens, 2):
                graph.edge_for_tokens(*combo)
        if self.options.weight == 'loglikelihood':
            # Re-calculate weight to use loglikelihood instead of simple 
            # cooccurrence counts.
            c = Counter([getattr(token, self.options.label)
                         for token in self.corpus.tokens])
            n = len(self.corpus.tokens)
            for edge in graph.edges:
                c1 = c[edge.source['name']]
                c2 = c[edge.target['name']]
                c12 = edge['weight']
                p = c2/n
                ll = log(p ** c12 * (1 - p) ** (c1-c12))
                edge['weight'] = ll * -2
        return graph

if __name__ == '__main__':
    run_as_cli(CooccurrenceWorker)
