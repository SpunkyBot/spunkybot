"""
Library for Spunky Bot
http://urthub.github.io/spunkybot
Author: Alexander Kress

This program is released under the MIT License.
"""

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

    def process(self):
        """
        Thread process
        """
        while True:
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
