# -*- coding: utf-8 -*-

# Copyright 2011 Björn Larsson

# This file is part of thetvdb.
#
# thetvdb is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# thetvdb is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with thetvdb.  If not, see <http://www.gnu.org/licenses/>.

import logging
import random

from thetvdb import error
from thetvdb.xmlhelpers import parse_xml

__all__ = ['TypeMask', 'Mirror', 'MirrorList']

#Module logger object
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class TypeMask(object):
    """An enum like class with the mask flags for the mirrors"""
    XML = 1
    BANNER = 2
    ZIP = 4

class Mirror(object):
    """Stores data about a thetvdb.com mirror server"""

    def __init__(self, id, url, type_mask):
        self.id, self.url, self.type_mask = id, url, type_mask

    def __repr__(self):
        return "<{0} ({1}:{{2}})>".format(
            "Mirror", self.url, self.type_mask )


class MirrorList(object):
    """Managing a list available mirrors"""
    def __init__(self, etree):
        self.data = [
            Mirror(m['id'], m['mirrorpath'], m['typemask'])
            for m in parse_xml( etree, 'Mirror' )
        ]

    def get_mirror(self, type_mask):
        try:
            return random.choice(
                [m for m in self.data if
                 int(m.type_mask) & int(type_mask) ==  int(type_mask)])
        except IndexError:
            raise error.TheTvDBError("No Mirror matching {0} found".
                format(type_mask))