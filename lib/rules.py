"""
Library for Spunky Bot
http://www.spunkybot.de
Author: Alexander Kress

This program is released under the MIT License.
"""

__version__ = '1.0.1'


### IMPORTS
import time
from threading import Thread
from threading import RLock


### CLASS Rules ###
class Rules(object):
    """
    Display the rules
    """

    def __init__(self, rules_file, rules_frequency, rcon_handle):
        """
        create a new instance of Rules

        @param rules_file: The full path of the rules.conf file
        @type  rules_file: String
        @param rules_frequency: The frequency of rules iteration in seconds
        @type  rules_frequency: Integer
        @param rcon_handle: RCON handler instance
        @type  rcon_handle: Instance
        """
        self.rules_file = rules_file
        if rules_frequency < 5:
            # avoid flooding with too less delay
            self.rules_frequency = 5
        else:
            self.rules_frequency = rules_frequency
        self.rcon_handle = rcon_handle
        self.rcon_lock = RLock()
        # start Thread
        self.processor = Thread(target=self.process)
        self.processor.setDaemon(True)
        self.processor.start()

    def process(self):
        """
        Thread process
        """
        # initial wait
        time.sleep(30)
        while 1:
            filehandle = open(self.rules_file, 'r+')
            for line in filehandle.readlines():
                # display rule
                with self.rcon_lock:
                    self.rcon_handle.push("say ^2%s" % line)
                # wait for given delay in the config file
                time.sleep(self.rules_frequency)
            filehandle.close()
