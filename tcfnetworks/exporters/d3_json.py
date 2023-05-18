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
JSON exporter for TCF graphs.

"""

import json

from tcflib import tcf
from tcflib.service import ExportingWorker, run_as_cli


class JSONWorker(ExportingWorker):

    def _node2json(self, node):
        node_data = {
            "id": node.get('ID'),
            "name": node.text,
            "tokens": node.get('tokenIDs').split()
        }
        if "class" in node.attrib:
            node_data["class"] = node.get('class')
        return node_data

    def _edge2json(self, edge, nodes_map):
        edge_data = {
            "source": nodes_map[edge.get("source")],
            "target": nodes_map[edge.get("target")],
        }
        if "weight" in edge.attrib:
            edge_data["weight"] = edge.get("weight")
        if "label" in edge.attrib:
            edge_data["label"] = edge.get("label")
        return edge_data

    def _sentence2json(self, sentence, tokens_map):
        token_ids = sentence.get("tokenIDs").split()
        sentence_data = {
            "tokens": [token.lower() for token in token_ids],
            "words": [{"id": id_, "text": tokens_map[id_]}
                      for id_ in token_ids]
        }
        return sentence_data

    def export(self):
        input_tree = self.corpus.tree
        nodes = input_tree.xpath("//text:graph/text:nodes/text:node",
                                 namespaces=tcf.NS)
        edges = input_tree.xpath("//text:graph/text:edges/text:edge",
                                 namespaces=tcf.NS)
        sentences = input_tree.xpath("//text:sentences/text:sentence",
                                     namespaces=tcf.NS)
        tokens = input_tree.xpath("//text:tokens/text:token",
                                  namespaces=tcf.NS)
        tokens_map = {token.get("ID"): token.text for token in tokens}
        nodes_data = [self._node2json(node) for node in nodes]
        nodes_map = {node["id"]: i for i, node in enumerate(nodes_data)}
        links_data = [self._edge2json(edge, nodes_map) for edge in edges]
        text_data = [self._sentence2json(sentence, tokens_map)
                     for sentence in sentences]
        output = {
            "nodes": nodes_data,
            "links": links_data,
            "text": text_data
        }
        return json.dumps(output, indent=2)


if __name__ == '__main__':
    run_as_cli(JSONWorker)
