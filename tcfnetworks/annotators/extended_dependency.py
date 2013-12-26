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
from tcflib.service import AddingWorker, run_as_cli
from tcflib.tagsets import TagSet

from tcfnetworks.utils import graph_to_tcf, merge_graphs

ISOcat = TagSet('DC-1345')
PUNCT = ISOcat['punctuation']
NOUN = ISOcat['noun']
VERB = ISOcat['verb']
ADVERB = ISOcat['adverb']


class DependencyWorker(AddingWorker):

    __options__ = {
        'nodes': 'lexical',
        'label': 'semantic_unit',
        'edges': 'dependency',
        'distance': 1,
        'stopwords': '',
    }

    def add_annotations(self):
        # Create igraph.Graph.
        graph = None
        for parse in self.corpus.xpath('text:depparsing/text:parse',
                                       namespaces=tcf.NS):
            graph = self.parse_to_graph(parse, graph=graph)
        # Convert igraph.Graph to TCF graph.
        graph = graph_to_tcf(graph)
        # Save
        logging.info('Graph has {} nodes and {} edges.'.format(
                len(graph.find(tcf.P_TEXT + 'nodes')),
                len(graph.find(tcf.P_TEXT + 'edges'))))
        self.corpus.append(graph)

    def parse_to_graph(self, parse, graph=None):
        parse_graph = igraph.Graph()
        # Set up filtering
        if self.options.stopwords:
            stopwordspath = os.path.join(os.path.dirname(__file__),
                                         'data', 'stopwords',
                                         self.options.stopwords)
            try:
                with open(stopwordspath) as stopwordsfile:
                    self.stopwords = [token.strip() for token
                                      in stopwordsfile.readlines() if token]
            except FileNotFoundError:
                logging.error('No stopwords list "{}".'.format(
                        self.options.stopwords))
                sys.exit(-1)
        try:
            self.test_token = getattr(self,
                    'test_token_{}'.format(self.options.nodes))
        except AttributeError:
            logging.error('Method "{}" is not supported.'.format(
                    self.options.nodes))
            sys.exit(-1)
        try:
            self.find_edges = getattr(self,
                    'find_edges_{}'.format(self.options.edges))
            if self.options.edges == 'verbs_nouns':
                self.test_token = lambda token: token.postag.is_a(VERB)
        except AttributeError:
            logging.error('Method "{}" is not supported.'.format(
                    self.options.edges))
            sys.exit(-1)
        # Add edges
        for a, b in self.find_edges(parse, parse.root):
            # Find or add nodes
            vertices = []
            for i, token_id in enumerate((a, b)):
                token = self.corpus.find_token(token_id)
                vertex_label = str(getattr(token, self.options.label))
                try:
                    vertex = parse_graph.vs.find(vertex_label)
                except ValueError:
                    parse_graph.add_vertex(name=vertex_label,
                                           tokenIDs=[token.get('ID')])
                    vertex = parse_graph.vs.find(vertex_label)
                    if self.options.edges == 'verbs_nouns':
                        # We have a bipartite graph. Since i enumerates
                        # source and target, it is 0 or 1. Since the verb
                        # is always source, we can use the boolean value of i
                        # to specify the type.
                        vertex['type'] = bool(i)
                else:
                    if not token.get('ID') in vertex['tokenIDs']:
                        vertex['tokenIDs'].append(token.get('ID'))
                vertices.append(vertex)
            # Add or increment edges
            self.add_or_increment_edge(parse_graph, *vertices)
        if self.options.distance > 1:
            # Add additional edges for each pair of nodes with path length <
            # distance.
            # Do not alter the graph while iteration. Store additional edges.
            additional_edges = []
            for source, target in combinations(parse_graph.vs, 2):
                distance = parse_graph.shortest_paths(source, target)[0][0]
                if distance <= self.options.distance:
                    additional_edges.append((source, target))
            # Now add additional edges.
            for source, target in additional_edges:
                self.add_or_increment_edge(parse_graph, source, target)
        # Create graph or append to given graph.
        if graph == None:
            return parse_graph
        else:
            return merge_graphs(graph, parse_graph)

    def add_or_increment_edge(self, graph, source, target):
        """Add edge to graph or increment weight."""
        if isinstance(source, igraph.Vertex):
            source = source.index
        if isinstance(target, igraph.Vertex):
            target = target.index
        if source == target:
            # Loop, skip this edge.
            # Loops stem from multi-token named entities.
            return
        try:
            edge_id = graph.get_eid(source, target)
            edge = graph.es[edge_id]
        except igraph.InternalError:
            # Edge does not exist, create
            graph.add_edge(source, target, weight=1)
        else:
            # edge exists, increment weight
            edge['weight'] += 1
        # TODO: Add edge instances
        # TODO: Allow multi-edges (take label into account)

    def test_token(self):
        logging.warn('No token test method set.')

    def test_token_stopwords(self, token):
        if self.options.stopwords:
            token_label = str(getattr(token, self.options.label))
            if token_label in self.stopwords:
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
        if token.named_entity is not None:
            return True
        if token.reference is not None:
            return True
        return False

    def test_token_semantic(self, token):
        if token.postag.is_a(VERB):
            return True
        if not token.postag.is_closed and not token.postag.is_a(ADVERB):
            return self.test_token_stopwords(token)
        if token.named_entity is not None:
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
        if token.named_entity is not None:
            return True
        if resolve and token.reference is not None:
            for reftoken in token.reference.tokens:
                if self.test_token_entity(reftoken, False):
                    return True
        return False

    def test_token_actor(self, token, resolve=True):
        if token.named_entity is not None:
            if token.named_entity.get('class') in ('PER', 'ORG'):
                # FIXME: Use proper tags instead of hardcoded CoNLL2002 tags.
                return True
        if resolve and token.reference is not None:
            for reftoken in token.reference.tokens:
                if self.test_token_actor(reftoken, False):
                    return True
        return False

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
        head_token = self.corpus.find_token(head)
        dependents = list(self.find_dependents(parse, head))
        # head-dependent edges
        if self.test_token(head_token):
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
        head_token = self.corpus.find_token(head)
        dependents = list(self.find_dependents(parse, head))
        # Store to avoid duplicate test.
        token_is_valid = self.test_token(head_token)
        # head-dependent edges
        if token_is_valid:
            for dependent in dependents:
                yield (head, dependent)
        # dependent-dependent edges
        dep_combinations = ()
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
                dep_token = self.corpus.find_token(dependent)
                if dep_token.postag.is_a(VERB):
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
        head_token = self.corpus.find_token(head)
        dependents = list(self.find_dependents(parse, head))
        nonverb_dependents = []
        for dependent in dependents:
            dep_token = self.corpus.find_token(dependent)
            if not dep_token.postag.is_a(VERB):
                nonverb_dependents.append(dependent)
        # Store to avoid duplicate test.
        token_is_valid = self.test_token(head_token)
        # head-dependent edges
        if token_is_valid and not head_token.postag.is_a(VERB):
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
        head_token = self.corpus.find_token(head)
        if head_token.postag.is_a(VERB):
            for dependent in parse.find_dependents(head):
                dep_token = self.corpus.find_token(dependent)
                if dep_token.postag.is_a(NOUN):
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
            dependent_token = self.corpus.find_token(dependent)
            if self.test_token(dependent_token):
                yield dependent
            elif descend:
                for dependent2 in self.find_dependents(parse, dependent):
                    yield dependent2


if __name__ == '__main__':
    run_as_cli(DependencyWorker)
