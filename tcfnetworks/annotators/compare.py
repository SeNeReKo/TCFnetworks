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

import logging

from tcflib import tcf
from tcflib.service import run_as_cli
from extended_dependency import DependencyWorker
from cooccurrence import CooccurrenceWorker
from tcfnetworks.utils import graph_to_tcf


class ComparingWorker(DependencyWorker):

    def add_annotations(self):
        # 1: Dependency graph
        graph = None
        for parse in self.corpus.xpath('text:depparsing/text:parse',
                                       namespaces=tcf.NS):
            graph = self.parse_to_graph(parse, graph=graph)
        graph = graph_to_tcf(graph)
        for edge in graph.find(tcf.P_TEXT + 'edges'):
            edge.set('label', 'Dependency')
        # 2: Extended dependency graph
        graph1 = None
        self.options.distance = 2
        for parse in self.corpus.xpath('text:depparsing/text:parse',
                                       namespaces=tcf.NS):
            graph1 = self.parse_to_graph(parse, graph=graph1)
        graph1 = graph_to_tcf(graph1)
        for edge in graph1.find(tcf.P_TEXT + 'edges'):
            edge.set('label', 'Extended')
        # 3: Cooccurrence graph
        # TODO: Take paragraph structure into account
        tokens = [token for token in self.corpus.tokens
                  if not token.postag.is_closed]
        graph2 = CooccurrenceWorker.build_graph(self, tokens)
        graph2 = CooccurrenceWorker.build_graph(self, tokens,
                                                gap=5, graph=graph2)
        for edge in graph2.find(tcf.P_TEXT + 'edges'):
            edge.set('label', 'Cooccurrence')
        # Merge graphs
        graph = self.merge_graphs(graph, graph1, graph2)
        # Finish
        logging.info('Graph has {} nodes and {} edges.'.format(
                len(graph.find(tcf.P_TEXT + 'nodes')),
                len(graph.find(tcf.P_TEXT + 'edges'))))
        self.corpus.append(graph)

    def merge_graphs(self, *graphs):
        graphs = list(graphs)
        base_graph = graphs.pop(0)
        base_nodes = base_graph.find(tcf.P_TEXT + 'nodes')
        base_edges = base_graph.find(tcf.P_TEXT + 'edges')
        for graph in graphs:
            new_nodes = graph.find(tcf.P_TEXT + 'nodes')
            new_edges = graph.find(tcf.P_TEXT + 'edges')
            for new_node in new_nodes:
                base_node = base_nodes.find_node(new_node.text)
                if base_node is None:
                    base_nodes.add_node(new_node.text)
            for new_edge in new_edges:
                node_a_id = new_edge.get('source')
                node_b_id = new_edge.get('target')
                # TODO: Factor out into XPath object
                node_a_label = new_nodes.xpath('string(text:node[@ID = $nid])',
                                               namespaces=tcf.NS,
                                               nid=node_a_id)
                node_b_label = new_nodes.xpath('string(text:node[@ID = $nid])',
                                               namespaces=tcf.NS,
                                               nid=node_b_id)

                node_a = base_nodes.find_node(node_a_label)
                node_b = base_nodes.find_node(node_b_label)
                base_edge = base_edges.find_edge(node_a.get('ID'),
                                                 node_b.get('ID'))
                if base_edge is None:
                    base_edge = base_edges.add_edge(node_a.get('ID'),
                                                    node_b.get('ID'))
                    base_edge.set('label', new_edge.get('label'))
                    base_edge.set('weight', new_edge.get('weight'))
                else:
                    base_edge.set('weight', str(int(base_edge.get('weight')) +
                                                int(new_edge.get('weight'))))
                    base_labels = base_edge.get_value_set('label')
                    for label in new_edge.get_value_set('label'):
                        if not label in base_labels:
                            base_labels.add(label)
        return base_graph


if __name__ == '__main__':
    run_as_cli(ComparingWorker)
