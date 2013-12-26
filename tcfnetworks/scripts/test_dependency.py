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
This annotator helps test the dependency network service.

"""

import os

import igraph
from tcflib import tcf
from tcflib.service import run_as_cli

from tcfnetworks.annotators.extended_dependency import DependencyWorker
from tcfnetworks.utils import tcf_to_graph


class ComparingWorker(DependencyWorker):

    # Little trick to upate the options dict.
    __options__ = dict(list(DependencyWorker.__options__.items()) + 
        list({
        'first': 1,
        'number': 5,
        'methods': ['dependency_tree',
                    'lexical:dependency:lemma',
                    'semantic:semantic:semantic_unit'],
        'output': ['svg', 'graphml']
    }.items()))

    def add_annotations(self):
        outdir = 'output'
        if not os.path.isdir(outdir):
            os.mkdir(outdir)
        for i, parse in enumerate(
                self.corpus.xpath('text:depparsing/text:parse['
                'position() >= $start and position() < $end]',
                start=self.options.first,
                end=self.options.first + self.options.number,
                namespaces=tcf.NS), start=1):
            for method, graph in self.iter_graphs(parse):
                # Easiest way to get the graph into iGraph: save it as GraphML
                # and load it.
                if method == 'dependency_tree':
                    graph = tcf_to_graph(graph)
                    layout_method = 'tree'
                else:
                    graph.vs['label'] = graph.vs['name']
                    layout_method = 'kamada_kawai'
                label = method.replace(':', '_')
                filebase = os.path.join(outdir, '{count:03d}_{label}'.format(
                                                count=i, label=label))
                if 'graphml' in self.options.output:
                    graph.write_graphml(filebase + '.graphml')
                if 'svg' in self.options.output:
                    # Draw
                    if layout_method == 'tree':
                        root_token = self.corpus.find_token(parse.root)
                        root = graph.vs.find(label=root_token.text)
                        layout = graph.layout_reingold_tilford(
                                                            root=[root.index])
                    else:
                        layout = graph.layout(layout_method)
                    igraph.plot(graph, filebase + '.svg', layout=layout,
                                vertex_color='#1f77b4', edge_color='#999',
                                vertex_frame_color='#fff', label_size=14)

    def iter_graphs(self, parse):
        for method in self.options.methods:
            if method == 'dependency_tree':
                yield (method, self.parse_to_tree(parse))
                continue
            self.options.nodes, self.options.edges, self.options.label = \
                    method.split(':')
            yield (method, self.parse_to_graph(parse))

    def parse_to_tree(self, parse):
        graph = tcf.Element(tcf.P_TEXT + 'graph')
        nodes = tcf.SubElement(graph, tcf.P_TEXT + 'nodes')
        edges = tcf.SubElement(graph, tcf.P_TEXT + 'edges')
        for a_id, b_id in self.find_dependency_edges(parse, parse.root):
            # Find or add nodes.
            # Since we want single token instances, not lemmas, we use the
            # token ID as node label for now. We replace it with the token text
            # later.
            node_a = nodes.find_node(a_id)
            if node_a is None:
                node_a = nodes.add_node(a_id)
            node_b = nodes.find_node(b_id)
            if node_b is None:
                node_b = nodes.add_node(b_id)
            # add edge or increment weight
            edge = edges.find_edge(node_a.get('ID'), node_b.get('ID'))
            if edge is None:
                # add edge
                edge = edges.add_edge(node_a.get('ID'), node_b.get('ID'))
        # Replace token IDs with token text now.
        for node in nodes.findall(tcf.P_TEXT + 'node'):
            token_id = node.text
            token = self.corpus.find_token(token_id)
            node.text = token.text
        return graph

    def find_dependency_edges(self, parse, head):
        for dependent in parse.find_dependents(head):
            yield (head, dependent)
            for dependency_edge in self.find_dependency_edges(
                    parse, dependent):
                yield dependency_edge


if __name__ == '__main__':
    run_as_cli(ComparingWorker)
