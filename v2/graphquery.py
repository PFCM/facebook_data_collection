"""
Deals with making a graph query &
fully populating it.
"""
import urllib.request
import urllib
import datetime
import json
import logging
logger = logging.getLogger(name='graphquery')
import time
import sys
import os

class GraphQuery(object):
    """Base class for graph queries.
    Provides methods to execute a query and helpers to fully populate
    edges.
    Subclasses are basically just wrappers for this
    """
    def __init__(self, access_token, endpoint='/me',
                 version='2.5'):
        """
        Initialises the graph query in the most basic way possible.
        All it requires is an access token (use None or '' if not necessary)
        and an endpoint, which is a Node or Edge in graph api speak.
        """
        self.access_token = access_token
        self.endpoint = endpoint

    @staticmethod
    def request_until_success(url, max_attempts=5, wait=5,
                              fail_max=True):
        """
        Make a request to the given url. In the event of a 500 error,
        wait `wait` seconds and keep trying up to `max_attempts` times.
        If fail_max is True then raise an error on failure due to max
        attempts otherwise just return None.
        """
        req = urllib.request.Request(url)
        success = False
        num_tries = 0
        while not success:
            try:
                num_tries += 1
                response = urllib.request.urlopen(req)
                success = response.getcode() == 200
            except urllib.request.HTTPError as e:
                logger.error('e')
                logger.error('Error url: {}'.format(e))
                if e.code == 500 and num_tries < max_attempts:
                    logger.info('trying again soon')
                    time.sleep(wait)
                else:
                    logger.error(e.reason)
                    raise e

        if not success:
            raise Error('Failed to make request')
        return json.loads(response.read().decode('utf-8'))

    def _make_url(self):
        """generates the url."""
        url = 'https://graph.facebook.com/'
        url += 'v{}'.format(self.version)
        url += self.endpoint
        url += '?access_token={}'.format(self.access_token)
        q = self.get_query_string()
        if q:
            url += '&{}'.format(q)
        return url

    def get_query_string(self):
        """Returns the query string. This is key for subclasses"""
        pass

    def execute(self, shallow=False):
        """
        Executes the query represented by this object.
        If shallow is False (default) will recursively attempt
        to fill fields that contain a 'next' cursor, apart from
        the top level one. It is up to subclasses to deal with paged
        results in that context.
        """
        # start by constructing the url
        url = self._make_url()
        # now make the request
        logger.info('querying {}'.format(url))
        result = GraphQuery.request_until_success(url)
        # now we will go through and try and expand anything that needs it
        if 'data' in result:
            result = {'lol':result} # yeah this seems odd
        for key in result:
            GraphQuery.expand(result[key])
        return result

    @staticmethod
    def expand(obj):
        """Begins the expansion. If obj is a dict, then
        looks for obj['paging']['next'] and if present loops, appending
        results['data'] to obj['data'] until there is no moer next cursor.

        If obj is a list, recurses the process on each element,
        replacing each object with the result of this function.
        """
        if isinstance(obj, list):
            for i,o in enumerate(obj):
                obj[i] = expand(o)
        elif isinstance(obj, dict):
            if 'paging' in obj:
                current = obj
                i = 0
                while 'next' in current['paging']:
                    i += 1
                    logger.info('...{}'.format(i))
                    current = GraphQuery.request_until_success(
                        current['paging']['next']
                    )
                    obj['data'].extend(current['data'])
                return obj
