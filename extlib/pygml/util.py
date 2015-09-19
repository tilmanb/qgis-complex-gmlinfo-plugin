# -*- coding: utf-8 -*-

"""
pygml for parsing GML files (ISO19136)
"""

__title__ = 'pygml'
__author__ = 'Jürgen Weichand'
__version__ = '0.3.0'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2015 Jürgen Weichand'


import os
import tempfile

def getTempfile(filename):
    tmpdir = tempfile.gettempdir()
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
    tmpfile= os.path.join(tmpdir, filename)
    return tmpfile