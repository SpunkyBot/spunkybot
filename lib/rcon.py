"""
Library for Spunky Bot
http://www.spunkybot.de
Author: Alexander Kress

This program is released under the MIT License.
"""

__version__ = '1.0.10'


### IMPORTS
import time
import os.path

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
        self.quake = PyQuake3("%s:%s" % (host, port), passwd)
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
                try:
                    ret_val = self.quake.rcon(value)[1].split(':')[1].split('^7')[0].lstrip('"')
                except IndexError:
                    ret_val = None
                time.sleep(.33)
                return ret_val

    def get_mapcycle_path(self):
        """
        get the full path of mapcycle.txt file
        """
        maplist = []
        self.quake.rcon_update()
        # get path of fs_homepath and fs_basepath
        fs_homepath = self.get_cvar('fs_homepath')
        fs_basepath = self.get_cvar('fs_basepath')
        fs_game = self.get_cvar('fs_game')
        # get file name of mapcycle.txt
        mapcycle_file = self.get_cvar('g_mapcycle')
        try:
            # set full path of mapcycle.txt
            mc_home_path = os.path.join(fs_homepath, fs_game, mapcycle_file) if fs_homepath else ""
            mc_base_path = os.path.join(fs_basepath, fs_game, mapcycle_file) if fs_basepath else ""
        except TypeError:
            raise Exception('Server did not respond to mapcycle path request, please restart the Bot')
        if os.path.isfile(mc_home_path):
            mapcycle_path = mc_home_path
        elif os.path.isfile(mc_base_path):
            mapcycle_path = mc_base_path
        else:
            mapcycle_path = None
        if mapcycle_path:
            with open(mapcycle_path, 'r') as file_handle:
                lines = [line for line in file_handle if line != '\n']
            try:
                while 1:
                    tmp = lines.pop(0).strip()
                    if tmp[0] == '{':
                        while tmp[0] != '}':
                            tmp = lines.pop(0).strip()
                        tmp = lines.pop(0).strip()
                    maplist.append(tmp)
            except IndexError:
                pass
        return maplist

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
            time.sleep(.33)

    def clear(self):
        """
        clear RCON queue
        """
        self.queue.queue.clear()
