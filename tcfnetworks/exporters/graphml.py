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
GraphML exporter for TCF graphs.

"""

import os.path

from lxml import etree
from tcflib import tcf
from tcflib.service import ExportingWorker, run_as_cli


class GraphMLWorker(ExportingWorker):

    def export(self):
        input_tree = self.corpus.tree
        xslt_file = os.path.join(os.path.dirname(__file__),
                                 'data', 'tcf2graphml.xsl')
        xslt_tree = etree.parse(xslt_file)
        transform = etree.XSLT(xslt_tree)
        output_tree = transform(input_tree)
        return etree.tostring(output_tree, encoding='utf8', pretty_print=True)


if __name__ == '__main__':
    run_as_cli(GraphMLWorker)
