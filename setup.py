#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.core import setup
from glob import glob

setup(name='TCFnetworks',
      version='0.1',
      description='Python TCF network services',
      author='Frederik Elwert',
      author_email='frederik.elwert@web.de',
#      url='',
      packages=['tcfnetworks'],
#      package_data={'tcfnetworks.exporters': glob('data/*.xsl')},
     )
