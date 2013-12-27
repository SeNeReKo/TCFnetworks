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

from tcflib import tcf
from tcflib.service import run_as_cli

from base import TokenTestingWorker


class CooccurrenceWorker(TokenTestingWorker):

    __options__ = TokenTestingWorker.__options__.copy()
    __options__.update({
        'method': 'words',
        'gap': [2, 5],
    })

    def __init__(self, input_data, **options):
        super().__init__(input_data, **options)
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
                len(graph.find(tcf.P_TEXT + 'nodes')),
                len(graph.find(tcf.P_TEXT + 'edges'))))
        self.corpus.append(graph)

    def build_graph(self):
        logging.warn('No graph building method set.')

    def build_graph_words(self):
        """
        This method implements a word-gap based cooccurrence network.

        This implementation is based on the method and algorithm described in:
        Paranyushkin, Dmitry. 2011. „Identifying the Pathways for Meaning 
        Circulation using Text Network Analysis“. Nodus Labs.
        <http://noduslabs.com/research/
        pathways-meaning-circulation-text-network-analysis/>.
        
        """
        # TODO: Take paragraphs into account.
        tokens = []
        for token in self.corpus.tokens:
            if self.test_token(token):
                entity = token.named_entity
                if entity is not None:
                    # We only want an entity once, so we only use the first token
                    # of an entity.
                    if entity.get_value_list('tokenIDs')[0] != token.get('ID'):
                        continue
                tokens.append(token)
        graph = None
        for gap in self.options.gap:
            logging.info('Building network with gap {}.'.format(gap))
            graph = self.build_graph_words_real(tokens, gap, graph)
        return graph

    def build_graph_words_real(self, tokens, gap=2, graph=None):
        """
        This function does all the heavy-lifting of creating a graph from
        a list of words in a paragraph. It expects to get a list of tokens.

        :parameters:
            - `tokens`: A list of tokens.
            - `gap`: The word gap for detecting edges.
            - `graph`: A graph node to which the edges will be added.
        :returns:
            - The graph node.

        """
        if graph == None:
            graph = tcf.Element(tcf.P_TEXT + 'graph')
            nodes = tcf.SubElement(graph, tcf.P_TEXT + 'nodes')
            edges = tcf.SubElement(graph, tcf.P_TEXT + 'edges')
        else:
            nodes = graph.find(tcf.P_TEXT + 'nodes')
            edges = graph.find(tcf.P_TEXT + 'edges')
        # test if words are already nodes in the graph
        for token in tokens:
            semantic_unit = token.semantic_unit
            node = nodes.find_node(str(semantic_unit))
            if node is None:
                node = nodes.add_node(str(semantic_unit))
                if semantic_unit.tag == tcf.P_TEXT + 'lemma':
                    node.set('class', 'lemma')
                elif semantic_unit.tag == tcf.P_TEXT + 'entity':
                    node.set('class', semantic_unit.get('class'))
            node.get_value_list('tokenIDs').append(token.get('ID'))
        for i in range(len(tokens) - (gap - 1)):
            # try all combinations of words within gap
            for a, b in combinations(tokens[i:i + gap], 2):
                # add edge or increment weight
                node_a = nodes.find_node(a.semantic_unit)
                node_b = nodes.find_node(b.semantic_unit)
                edge = edges.find_edge(node_a.get('ID'), node_b.get('ID'))
                if edge is None:
                    # add edge
                    edge = edges.add_edge(node_a.get('ID'), node_b.get('ID'),
                                          weight='1')
                else:
                    # edge exists, increment weight
                    edge.set('weight', str(int(edge.get('weight')) + 1))
                # TODO: Add edge instances
        return graph

if __name__ == '__main__':
    run_as_cli(CooccurrenceWorker)
