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
import os
import logging
from itertools import combinations

import igraph
from tcflib import tcf
from tcflib.service import run_as_cli
from tcflib.tagsets import TagSet

from tcfnetworks.annotators.base import TokenTestingWorker

ISOcat = TagSet('DC-1345')
PUNCT = ISOcat['punctuation']
NOUN = ISOcat['noun']
VERB = ISOcat['verb']
ADVERB = ISOcat['adverb']


class DependencyWorker(TokenTestingWorker):

    __options__ = TokenTestingWorker.__options__.copy()
    __options__.update({
        'edges': 'dependency',
        'distance': 1,
    })

    def __init__(self, **options):
        super().__init__(**options)
        try:
            self.find_edges = getattr(self,
                    'find_edges_{}'.format(self.options.edges))
            if self.options.edges == 'verbs_nouns':
                self.test_token = lambda token: token.postag.is_a(VERB)
        except AttributeError:
            logging.error('Method "{}" is not supported.'.format(
                    self.options.edges))
            sys.exit(-1)

    def add_annotations(self):
        # Create igraph.Graph.
        graph = self.build_graph()
        logging.info('Graph has {} nodes and {} edges.'.format(
                len(graph.nodes),
                len(graph.edges)))
        self.corpus.add_layer(graph)

    def build_graph(self):
        graph = None
        for parse in self.corpus.depparsing:
            graph = self.parse_to_graph(parse, graph=graph)
        return graph

    def parse_to_graph(self, parse, graph=None):
        if graph is None:
            graph = tcf.Graph(label=self.options.label)
        # Store edges added for this parse, so we can build a subgraph.
        # This is required for adding edges if distance > 1.
        parse_edges = []
        # Also store all tokens. Required for checking token distance if
        # distance > 1.
        parse_tokens = set()
        # Walk the parse tree.
        for tokens in self.find_edges(parse, parse.root):
            # Add nodes.
            for i, token in enumerate(tokens):
                parse_tokens.add(token)
                node = graph.node_for_token(token)
                if self.options.edges == 'verbs_nouns':
                    # We have a bipartite graph. Since i enumerates
                    # source and target, it is 0 or 1. Since the verb
                    # is always source, we can use the boolean value of i
                    # to specify the type.
                    vertex['type'] = bool(i)
            # Add edges.
            try:
                edge = graph.edge_for_tokens(*tokens)
            except tcf.LoopError:
                continue
            else:
                parse_edges.append(edge)
        if self.options.distance > 1:
            # Add additional edges for each pair of nodes with path length <
            # distance.
            # Do not alter the graph while iteration. Store additional edges.
            additional_edges = []
            parse_graph = graph._graph.subgraph_edges(
                    [e._edge for e in parse_edges])
            for source, target in combinations(parse_tokens, 2):
                source_node = graph.node_for_token(source)
                target_node = graph.node_for_token(target)
                try:
                    distance = parse_graph.shortest_paths(source_node['name'],
                                target_node['name'])[0][0]
                except ValueError:
                    # Token is not in the subgraph
                    continue
                if distance <= self.options.distance:
                    additional_edges.append((source, target))
            # Now add additional edges.
            for source, target in additional_edges:
                try:
                    graph.edge_for_tokens(source, target)
                except tcf.LoopError:
                    continue
        return graph

    def find_edges(self, parse, head):
        logging.warn('No edge detection method set.')

    def find_edges_dependency(self, parse, head):
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
        dependents = list(self.find_dependents(parse, head))
        # head-dependent edges
        if self.test_token(head):
            for dependent in dependents:
                yield (head, dependent)
        # search child edges
        for dependent in dependents:
            for dependent_edge in self.find_edges(
                    parse, dependent):
                yield dependent_edge

    def find_edges_extended_dependency(self, parse, head):
        """
        Generator method to find edges based on a dependency parse.

        The method determines if a token is included. If a dependency contains
        an excluded token, the dependent's dependents are searched for tokens.
        
        This method extends dependency based relations by indirect relations
        between the dependents of a verb.

        :parameters:
            - `parse`: A parse element.
            - `head`: The ID of the head element.
        :returns:
            - yields pairs of (head, dependent) IDs.

        """
        head
        dependents = list(self.find_dependents(parse, head))
        # Store to avoid duplicate test.
        token_is_valid = self.test_token(head)
        # head-dependent edges
        if token_is_valid:
            for dependent in dependents:
                yield (head, dependent)
        # dependent-dependent edges
        dep_combinations = []
        if not token_is_valid or head_token.postag.is_a(VERB):
            dep_combinations = list(combinations(dependents, 2))
            for combination in dep_combinations:
                yield combination
        # Search dependents for invalid verbs (like copula). They are
        # particularly relevant for edges (think of "be"), but they get lost
        # when only handling valid dependents. We relate their dependents
        # explicitly.
        for dependent in parse.find_dependents(head):
            if dependent not in dependents:
                if dependent.postag.is_a(VERB):
                    depdeps = self.find_dependents(parse, dependent, False)
                    for combination in combinations(depdeps, 2):
                        if not combination in dep_combinations:
                            yield combination
        # search child edges
        for dependent in dependents:
            for dependent_edge in self.find_edges(
                    parse, dependent):
                yield dependent_edge

    def find_edges_semantic(self, parse, head):
        """
        Generator method to find edges based on a dependency parse.
        
        In this method, verbs are excluded as nodes, but used to find edges.
        It is advised to use the token method `semantic`, as it includes all
        verbs, even closed verb forms.

        The method determines if a token is included. If a dependency contains
        an excluded token, the dependent's dependents are searched for tokens.

        :parameters:
            - `parse`: A parse element.
            - `head`: The ID of the head element.
        :returns:
            - yields pairs of (head, dependent) IDs.

        """
        dependents = list(self.find_dependents(parse, head))
        nonverb_dependents = []
        for dependent in dependents:
            if not dependent.postag.is_a(VERB):
                nonverb_dependents.append(dependent)
        # Store to avoid duplicate test.
        token_is_valid = self.test_token(head)
        # head-dependent edges
        if token_is_valid and not head.postag.is_a(VERB):
            for dependent in nonverb_dependents:
                yield (head, dependent)
                # TODO: Add relation as edge label
        # dependent-dependent edges
        else:
            for combination in combinations(nonverb_dependents, 2):
                yield combination
                # TODO: Add verbs as edge label
        # search child edges
        for dependent in dependents:
            for dependent_edge in self.find_edges(
                    parse, dependent):
                yield dependent_edge

    def find_edges_verbs_nouns(self, parse, head):
        """
        Generator method to find edges based on verbs.

        This method only links verbs and nouns.

        :parameters:
            - `parse`: A parse element.
            - `head`: The ID of the head element.
        :returns:
            - yields pairs of (head, dependent) IDs.

        """
        if head.postag.is_a(VERB):
            for dependent in parse.find_dependents(head):
                if dependent.postag.is_a(NOUN):
                    yield (head, dependent)
        for dependent in self.find_dependents(parse, head):
            for dependent_edge in self.find_edges(
                    parse, dependent):
                yield dependent_edge

    def find_dependents(self, parse, head, descend=True):
        """
        Generator method that returns all filtered dependents of a given head.

        If the direct dependents of a head are filtered out and `descend` is
        True, it looks for their dependents until it finds valid ones.

        :parameters:
            - `parse`: A parse element.
            - `head`: The ID of the head element.
            - `descend`: Descend the parse tree to find valid tokens.
        :returns:
            - yields dependent's IDs.

        """
        for dependent in parse.find_dependents(head):
            if self.test_token(dependent):
                yield dependent
            elif descend:
                for dependent2 in self.find_dependents(parse, dependent):
                    yield dependent2


if __name__ == '__main__':
    run_as_cli(DependencyWorker)