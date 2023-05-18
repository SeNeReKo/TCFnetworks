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

from pathlib import Path
from string import Template

from lxml import etree
from tcflib import tcf
from tcflib.service import ExportingWorker, run_as_cli
from tcfnetworks.exporters.d3_json import JSONWorker


class D3HTMLWorker(JSONWorker):

    def export(self):
        data = super().export()
        d3 = (Path(__file__).parent / 'data' / 'd3.v3.min.js').read_text()
        template_str = (Path(__file__).parent / 'data' / 'd3.html').read_text()
        template = Template(template_str)
        output = template.substitute(data=data, d3=d3)
        return output


if __name__ == '__main__':
    run_as_cli(D3HTMLWorker)
