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

This implementation is based on the method and algorithm described in:
Paranyushkin, Dmitry. 2011. „Identifying the Pathways for Meaning Circulation
using Text Network Analysis“. Nodus Labs. <http://noduslabs.com/research/
pathways-meaning-circulation-text-network-analysis/>.

"""

import logging
from itertools import combinations

from tcflib import tcf
from tcflib.service import AddingWorker, run_as_cli


class CooccurrenceWorker(AddingWorker):

    def add_annotations(self):
        # TODO: Take paragraphs into account.
        tokens = []
        for token in self.corpus.tokens:
            entity = token.named_entity
            if entity is not None:
                # We only want an entity once, so we only use the first token
                # of an entity.
                if entity.get_value_list('tokenIDs')[0] == token.get('ID'):
                    # first token
                    tokens.append(token)
                else:
                    continue
            elif not token.postag.is_closed:
                tokens.append(token)
        graph = self.build_graph(tokens, gap=2)
        graph = self.build_graph(tokens, gap=5, graph=graph)
        logging.info('Graph has {} nodes and {} edges.'.format(
                len(graph.find(tcf.P_TEXT + 'nodes')),
                len(graph.find(tcf.P_TEXT + 'edges'))))
        self.corpus.append(graph)

    def build_graph(self, tokens, gap=2, graph=None):
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
