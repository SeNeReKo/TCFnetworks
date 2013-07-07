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
This annotator implements dependency networks as a TCF compatible service.

"""

import sys
import logging
from itertools import combinations

from tcflib import tcf
from tcflib.service import AddingWorker, run_as_cli
from tcflib.tagsets import TagSet
ISOcat = TagSet('DC-1345')
PUNCT = ISOcat['punctuation']


class DependencyWorker(AddingWorker):

    def add_annotations(self):
        graph = None
        for parse in self.corpus.xpath('text:depparsing/text:parse',
                                       namespaces=tcf.NS):
            graph = self.parse_to_graph(parse, graph=graph)
        logging.info('Graph has {} nodes and {} edges.'.format(
                len(graph.find(tcf.P_TEXT + 'nodes')),
                len(graph.find(tcf.P_TEXT + 'edges'))))
        self.corpus.append(graph)

    def parse_to_graph(self, parse, graph=None,
                       method='semantic', node_label_attrib='semantic_unit'):
        logging.debug('Use token test method "{}" and node label "{}".'.format(
                      method, node_label_attrib))
        # Create graph or append to given graph.
        if graph == None:
            graph = tcf.Element(tcf.P_TEXT + 'graph')
            nodes = tcf.SubElement(graph, tcf.P_TEXT + 'nodes')
            edges = tcf.SubElement(graph, tcf.P_TEXT + 'edges')
        else:
            nodes = graph.find(tcf.P_TEXT + 'nodes')
            edges = graph.find(tcf.P_TEXT + 'edges')
        # Add edges
        try:
            self.test_token = getattr(self, 'test_token_{}'.format(method))
        except AttributeError:
            logging.error('Method "{}" is not supported.'.format(method))
            sys.exit(-1)
        for a, b in self.find_edges(parse, parse.root):
            # Find or add nodes
            edgenodes = []
            for token_id in a, b:
                token = self.corpus.find_token(token_id)
                node_label = getattr(token, node_label_attrib)
                node = nodes.find_node(node_label)
                if node is None:
                    node = nodes.add_node(node_label)
                node.get_value_set('tokenIDs').add(token.get('ID'))
                edgenodes.append(node)
            # add edge or increment weight
            if edgenodes[0] == edgenodes[1]:
                # Loop, skip this edge.
                # Loops stem from multi-token named entities.
                continue
            edge = edges.find_edge(edgenodes[0].get('ID'),
                                   edgenodes[1].get('ID'))
            if edge is None:
                # add edge
                edge = edges.add_edge(edgenodes[0].get('ID'),
                                      edgenodes[1].get('ID'),
                                      weight='1')
            else:
                # edge exists, increment weight
                edge.set('weight', str(int(edge.get('weight')) + 1))
            # TODO: Add edge instances
        return graph

    def test_token(self):
        logging.warn('No token test method set.')

    def test_token_full(self, token):
        return not token.postag.is_a(PUNCT)

    def test_token_nonclosed(self, token):
        return not token.postag.is_closed

    def test_token_semantic(self, token):
        if not token.postag.is_closed:
            return True
        if token.named_entity is not None:
            return True
        if token.reference is not None:
            return True
        return False

    def find_edges(self, parse, head):
        """
        Generator method to find edges based on a dependency parse.

        The method determines if a token is included. If a dependency contains
        an excluded token, the dependent's dependents are searched for tokens.

        :parameters:
            - `parse`: A parse element.
            - `head`: The ID of the head element.
        :returns:
            - yields pairs of (head, dependent) IDs.

        """
        head_token = self.corpus.find_token(head)
        if self.test_token(head_token):
            for dependent in self.find_dependents(parse, head):
                yield (head, dependent)
                # Recursively get the nonclosed edges where the dependent is
                # the head.
                for dependent_edge in self.find_edges(
                        parse, dependent):
                    yield dependent_edge
        else:
            # Since we have no nonclosed head, we use direct edges between all
            # nonclosed dependents of head, and then go from there.
            dependents = list(self.find_dependents(parse, head))
            for combination in combinations(dependents, 2):
                yield combination
            for dependent in dependents:
                for dependent_edge in self.find_edges(
                        parse, dependent):
                    yield dependent_edge

    def find_dependents(self, parse, head):
        """
        Generator method that returns all filtered dependents of a given head.

        If the direct dependents of a head are filtered out, it looks for
        their dependents until it finds valid ones.

        :parameters:
            - `parse`: A parse element.
            - `head`: The ID of the head element.
        :returns:
            - yields dependent's IDs.

        """
        for dependent in parse.find_dependents(head):
            dependent_token = self.corpus.find_token(dependent)
            if self.test_token(dependent_token):
                yield dependent
            else:
                for dependent2 in self.find_dependents(parse, dependent):
                    yield dependent2


if __name__ == '__main__':
    run_as_cli(DependencyWorker)
