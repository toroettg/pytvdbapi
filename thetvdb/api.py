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

"""
"""

import logging
import tempfile
import os
import sys
from thetvdb import error
from thetvdb.__init__ import __NAME__ as name
from thetvdb.language import LanguageList
from thetvdb.loader import Loader
from thetvdb.mirror import MirrorList, TypeMask
from thetvdb.xmlhelpers import parse_xml, generate_tree

__all__ = ['Episode', 'Season', 'Show', 'Search', 'tvdb']

#Module logger object
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# List the URLs that we need
urls = dict(mirrors="http://www.thetvdb.com/api/%(api_key)s/mirrors.xml",
    time="http://www.thetvdb.com/api/Updates.php?type=none",
    languages="http://www.thetvdb.com/api/%(api_key)s/languages.xml",
    search="http://www.thetvdb.com/api/GetSeries.php?seriesname=%(series)s",
    series=("%(mirror)s/api/%(api_key)s/series/%(seriesid)s/all/%(language)s.xml"))


class Episode(object):
    def __init__(self, data, season):
        self.data, self.season = data, season

    def __getattr__(self, item):
        try:
            return self.data[item]
        except IndexError:
            logger.error("Episode has no attribute {0}".format(item))
            raise error.TVDBAttributeError

    def __repr__(self):
        try:
            return "<Episode {0}>".format(self.EpisodeName)
        except error.TVDBAttributeError:
            return "<Episode>"

class Season(object):
    def __init__(self, season_number, show):
        self.show, self.season_number = show, season_number
        self.episodes = dict()

    def __getitem__(self, item):
        try:
            return self.episodes[item]
        except IndexError:
            logger.error("Episode {0} not found".format(item))
            raise error.TVDBIndexError()

    def __iter__(self):
        return iter(sorted(self.episodes.items(),
            cmp=lambda lhs, rhs: cmp(int(lhs[1].EpisodeNumber),
                                     int(rhs[1].EpisodeNumber))))

    def __repr__(self):
        return "<Season {0}>".format( self.season_number )

    def append(self, episode):
        assert type(episode) in (Episode,)
        logger.debug("{0} adding episode {1}".
                    format(self, episode))

        self.episodes[int(episode.EpisodeNumber)] = episode


class Show(object):
    """Holds data about a show in thetvdb"""
    def __init__(self, data, api, language):
        self.api, self.data, self.language = api, data, language
        self.seasons = dict()

    def __getattr__(self, item):
        try:
            return self.data[item]
        except KeyError:
            logger.debug( "Attribute not found" )
            raise error.TVDBAttributeError("Show has no attribute names %s" %
                                           item)

    def __iter__(self):
        if not self.seasons:
            self._populate_seasons()

        return iter(sorted(self.seasons.items(),
            cmp=lambda lhs, rhs: cmp(int(lhs[1].season_number),
                                     int(rhs[1].season_number))))


    def __len__(self):
        if not len(self.seasons):
            self._populate_seasons()
        return len(self.seasons)

    def __getitem__(self, item):
        if not item in self.seasons:
            logger.debug("Season data missing, will load from url")
            self._populate_seasons()
        try:
            return self.seasons[item]
        except IndexError:
            logger.error("Season {0} not found".format(item))
            raise error.TVDBIndexError()


    def _populate_seasons(self):
        context = {'mirror':self.api.mirrors.get_mirror(TypeMask.XML).url,
                       'api_key':self.api.config['api_key'],
                       'seriesid':self.id,
                       'language':self.language}

        data = generate_tree(self.api.loader.load(urls['series'] % context))
        episodes = [d for d in parse_xml( data, "Episode")]

        for episode in episodes:
            season_nr = int(episode['SeasonNumber'])
            if not season_nr in self.seasons:
                self.seasons[ season_nr ] = Season(season_nr, self)

            ep = Episode( episode, self.seasons[season_nr] )
            self.seasons[season_nr].append(ep)

    
class Search(object):
    def __init__(self, result, search, language):
        self.result, self.search, self.language = result, search, language

    def __len__(self):
        return len( self.result )

    def __getitem__(self, item):
        try:
            return self.result[item]
        except IndexError:
            logger.warning("Index out of range")
            raise error.TVDBIndexError("Index out of range")

    def __iter__(self):
        return iter( self.result )


class tvdb(object):
    """ """
    def __init__(self, api_key, **kwargs):
        self.config = dict()

        #cache old searches to avoid hitting the server
        self.search_buffer = dict()

        #Store the path to where we are
        self.path = os.path.abspath(os.path.dirname(__file__))

        #extract all argument and store for later use
        self.config['force_lang'] = getattr(kwargs, 'force_lang', False)
        # TODO: Apply for a new api key for the new name??
        self.config['api_key'] = api_key
        self.config['cache_dir'] = getattr(kwargs, 'cache_dir',
                os.path.join(tempfile.gettempdir(), name))

        #Create the loader object to use
        self.loader = Loader(self.config['cache_dir'])

        #If requested, update the local language file from the server
        if self.config['force_lang']:
            logger.debug("updating Language file from server")
            with open(os.path.join(self.path, '../data/languages.xml'),
                                   'wt') as f:
                f.write(self.loader.load(urls['languages'] % self.config))

        #Setup the list of supported languages
        self.languages = LanguageList(
            generate_tree(open(os.path.join(self.path,
                                    '../data/languages.xml'), 'rt').read()))

        #Create the list of available mirrors
        self.mirrors = MirrorList(
            generate_tree(self.loader.load(urls['mirrors'] % self.config)))

    def search(self, show, language, cache=True):
        logger.debug("Searching for {0} using language {1}"
            .format(show, language))

        if (show, language) not in self.search_buffer:
            data = generate_tree(self.loader.load( urls['search']
                           % {'series': show }, cache ))
            shows = [Show(d, self, language)
                     for d in parse_xml(data, "Series")]

            self.search_buffer[(show, language)] = shows

        return Search(self.search_buffer[(show, language)], show, language)


#A small sample usage
if __name__ == '__main__':
    def main():
        logger.addHandler(logging.StreamHandler(stream=sys.stdout))
        logger.setLevel(logging.DEBUG)

        api = tvdb("B43FF87DE395DF56")
        search = api.search( "Dexter", "en" )

        for s in search:
            print s


    sys.exit(main())