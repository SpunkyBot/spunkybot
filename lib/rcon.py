"""
Library for Spunky Bot
http://www.spunkybot.de
Author: Alexander Kress

This program is released under the MIT License.
"""

__version__ = '1.0.2'


### IMPORTS
import time

from lib.pyquake3 import PyQuake3
from Queue import Queue
from threading import Thread
from threading import RLock


### CLASS Rcon ###
class Rcon(object):
    """
    RCON class
    """

    def __init__(self, host, port, passwd):
        """
        create a new instance of Rcon

        @param host: The server IP address
        @type  host: String
        @param port: The server port
        @type  port: String
        @param passwd: The RCON password
        @type  passwd: String
        """
        self.live = False
        self.quake = PyQuake3(host + ":" + port, passwd)
        self.queue = Queue()
        self.rcon_lock = RLock()
        # start Thread
        self.processor = Thread(target=self.process)
        self.processor.setDaemon(True)
        self.processor.start()

    def push(self, msg):
        """
        execute RCON command

        @param msg: The RCON command
        @type  msg: String
        """
        if self.live:
            with self.rcon_lock:
                self.queue.put(msg)

    def go_live(self):
        """
        go live
        """
        self.live = True

    def get_status(self):
        """
        get RCON status
        """
        if self.live:
            with self.rcon_lock:
                self.push('status')

    def get_quake_value(self, value):
        """
        get Quake3 value
        """
        if self.live:
            with self.rcon_lock:
                self.quake.update()
                return self.quake.values[value]

    def get_rcon_output(self, value):
        """
        get RCON output for value
        """
        if self.live:
            with self.rcon_lock:
                return self.quake.rcon(value)

    def get_cvar(self, value):
        """
        get CVAR value
        """
        if self.live:
            with self.rcon_lock:
                return self.quake.rcon(value)[1].split().split(':')[1].split('^7')[0].lstrip('"')

    def process(self):
        """
        Thread process
        """
        while 1:
            if not self.queue.empty():
                if self.live:
                    with self.rcon_lock:
                        try:
                            command = self.queue.get()
                            if command != 'status':
                                self.quake.rcon(command)
                            else:
                                self.quake.rcon_update()
                        except Exception:
                            pass
            time.sleep(1)

    def clear(self):
        """
        clear RCON queue
        """
        self.queue.queue.clear()