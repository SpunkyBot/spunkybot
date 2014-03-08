"""
Library for Spunky Bot
http://www.spunkybot.de
Author: Alexander Kress

This program is released under the MIT License.
"""

__version__ = '1.0.0'


### IMPORTS
import urllib
import urllib2
import platform


### CLASS HeartBeat ###
class HeartBeat(object):
    """
    Send heartbeat to master server
    """

    def __init__(self, bot_version, server_port):
        """
        create a new instance of HeartBeat

        @param bot_version: Version of Spunky Bot
        @type  bot_version: String
        @param server_port: Port of the game server
        @type  server_port: String
        """
        data = {'v': bot_version, 'p': server_port, 'o': platform.platform()}
        values = urllib.urlencode(data)
        url = 'http://master.spunkybot.de/ping.php'
        self.full_url = '%s?%s' % (url, values)

    def process(self):
        """
        start process
        """
        try:
            urllib2.urlopen(self.full_url)
        except urllib2.URLError:
            pass
