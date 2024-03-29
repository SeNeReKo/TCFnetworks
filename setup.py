#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.core import setup
from glob import glob

setup(name='TCFnetworks',
      version='0.3.0',
      description='Python TCF network services',
      author='Frederik Elwert',
      author_email='frederik.elwert@web.de',
      url='https://github.com/SeNeReKo/TCFnetworks',
      packages=['tcfnetworks', 'tcfnetworks.annotators',
                'tcfnetworks.exporters'],
      package_data={'tcfnetworks.exporters': ['data/tcf2graphml.xsl',
                                              'data/d3.v3.min.js',
                                              'data/d3.html']},
      )
