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
Utility functions for working with networks.

"""

import os
from tempfile import NamedTemporaryFile

import igraph
from lxml import etree
from tcflib import tcf

from tcfnetworks.exporters.graphml import GraphMLWorker


def graph_to_tcf(graph):
    """Transforms an igraph.Graph into a tcf.GraphElement."""
    tgraph = tcf.Element(tcf.P_TEXT + 'graph')
    tcf.SubElement(tgraph, tcf.P_TEXT + 'nodes')
    tcf.SubElement(tgraph, tcf.P_TEXT + 'edges')
    nid = 'n_{}'
    for vertex in graph.vs:
        tnode = tgraph.add_node(vertex['name'])
        tnode.set('ID', nid.format(vertex.index))
        for key, value in vertex.attributes().items():
            if key == 'name':
                continue
            if isinstance(value, (list, tuple)):
                tnode.set_value_list(key, value)
            else:
                tnode.set(key, str(value))
    for edge in graph.es:
        source = nid.format(edge.source)
        target = nid.format(edge.target)
        tedge = tgraph.add_edge(source, target)
        for key, value in edge.attributes().items():
            if isinstance(value, (list, tuple)):
                tedge.set_value_list(key, value)
            else:
                tedge.set(key, str(value))
    return tgraph


def tcf_to_graph(graph_element):
    graph_content = etree.tostring(graph_element, encoding='utf8')
    graphml = GraphMLWorker(graph_content).run()
    with NamedTemporaryFile(delete=False) as outfile:
        outfile.write(graphml)
    graph = igraph.Graph.Read_GraphML(outfile.name)
    os.unlink(outfile.name)
    return graph


def merge_graphs(*graphs):
    graphs = list(graphs)
    graph = graphs.pop(0)
    graph = graph.copy()
    for graph2 in graphs:
        for vertex2 in graph2.vs:
            try:
                vertex = graph.vs.find(vertex2['name'])
            except ValueError:
                graph.add_vertex(**vertex2.attributes())
            else:
                for key, value in vertex2.attributes().items():
                    if key not in vertex.attribute_names():
                        vertex[key] = value
                    elif isinstance(value, str):
                        if vertex[key] != value:
                            vertex[key] += ' {}'.format(value)
                    elif isinstance(value, (int, float)):
                        vertex[key] += value
                    elif isinstance(value, (list, tuple)):
                        vertex[key].extend(value)
                    elif isinstance(value, (dict, set)):
                        vertex[key].update(value)
        for edge2 in graph2.es:
            try:
                # TODO: Multipled graphs can have multiple edges between two
                # vertices.
                source = graph.vs.find(graph2.vs[edge2.source]['name'])
                target = graph.vs.find(graph2.vs[edge2.target]['name'])
                edge_id = graph.get_eid(source.index, target.index)
                edge = graph.es[edge_id]
            except igraph.InternalError:
                graph.add_edge(graph2.vs[edge2.source]['name'],
                               graph2.vs[edge2.target]['name'],
                               **edge2.attributes())
            else:
                for key, value in edge2.attributes().items():
                    if key not in edge.attribute_names():
                        edge[key] = value
                    elif isinstance(value, str):
                        if edge[key] != value:
                            edge[key] += ' {}'.format(value)
                    elif isinstance(value, (int, float)):
                        edge[key] += value
                    elif isinstance(value, (list, tuple)):
                        edge[key].extend(value)
                    elif isinstance(value, (dict, set)):
                        edge[key].update(value)
    return graph
