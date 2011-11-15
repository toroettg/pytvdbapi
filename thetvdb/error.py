# -*- coding: utf-8 -*-

# This file is part of thetvdb.
#
# thetvdb is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# thetvdb is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with thetvdb.  If not, see <http://www.gnu.org/licenses/>.

"""
A module containing all the errors raised by thetvdb
"""

import logging

#Module level logger
logger = logging.getLogger(__name__)
logger.addHandler( logging.NullHandler() )

class TheTvDBError(Exception):
    """Base exception for all exceptions raised by thetvdb"""


class BadData(TheTvDBError):
    pass

class ConnectionError(TheTvDBError):
    pass