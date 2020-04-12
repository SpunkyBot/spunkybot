"""
Python Quake 3 Library
http://misc.slowchop.com/misc/wiki/pyquake3
Copyright (C) 2006-2007 Gerald Kaszuba

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import socket
import re


class Player(object):
    """
    Player class
    """
    def __init__(self, num, name, frags, ping, address=None, bot=-1):
        """
        create a new instance of Player
        """
        self.num = num
        self.name = name
        self.frags = frags
        self.ping = ping
        self.address = address
        self.bot = bot

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)


class PyQuake3(object):
    """
    PyQuake3 class
    """
    packet_prefix = '\xff' * 4
    player_reo = re.compile(r'^(\d+) (\d+) "(.*)"')

    rcon_password = None
    port = None
    address = None
    players = None
    values = None

    def __init__(self, server, rcon_password=''):
        """
        create a new instance of PyQuake3
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.set_server(server)
        self.set_rcon_password(rcon_password)

    def set_server(self, server):
        """
        set IP address and port and connect to socket
        """
        try:
            self.address, self.port = server.split(':')
        except ValueError:
            raise ValueError('Server address format must be: "address:port"')
        self.port = int(self.port)
        self.sock.connect((self.address, self.port))

    def get_address(self):
        """
        get IP address and port
        """
        return '%s:%s' % (self.address, self.port)

    def set_rcon_password(self, rcon_password):
        """
        set RCON password
        """
        self.rcon_password = rcon_password

    def send_packet(self, data):
        """
        send packet
        """
        self.sock.send('%s%s\n' % (self.packet_prefix, data))

    def recv(self, timeout=1):
        """
        receive packets
        """
        self.sock.settimeout(timeout)
        try:
            return self.sock.recv(8192)
        except socket.error as err:
            raise Exception('Error receiving the packet: %s' % err[1])

    def command(self, cmd, timeout=1, retries=5):
        """
        send command and receive response
        """
        while retries:
            self.send_packet(cmd)
            try:
                data = self.recv(timeout)
            except Exception:
                data = None
            if data:
                return self.parse_packet(data)
            retries -= 1
        raise Exception('Server response timed out')

    def rcon(self, cmd):
        """
        send RCON command
        """
        r_cmd = self.command('rcon "%s" %s' % (self.rcon_password, cmd))
        if r_cmd[1] == 'No rconpassword set on the server.\n' or r_cmd[1] == 'Bad rconpassword.\n':
            raise Exception(r_cmd[1][:-1])
        return r_cmd

    def parse_packet(self, data):
        """
        parse the received packet
        """
        if data.find(self.packet_prefix) != 0:
            raise Exception('Malformed packet')

        first_line_length = data.find('\n')
        if first_line_length == -1:
            raise Exception('Malformed packet')

        response_type = data[len(self.packet_prefix):first_line_length]
        response_data = data[first_line_length + 1:]
        return response_type, response_data

    def parse_status(self, data):
        """
        parse the response message and return a list
        """
        split = data[1:].split('\\')
        values = dict(zip(split[::2], split[1::2]))
        # if there are \n's in one of the values, it's the list of players
        for var, val in values.items():
            pos = val.find('\n')
            if pos == -1:
                continue
            split = val.split('\n', 1)
            values[var] = split[0]
            self.parse_players(split[1])
        return values

    def parse_players(self, data):
        """
        parse player information - name, frags and ping
        """
        self.players = []
        for player in data.split('\n'):
            if not player:
                continue
            match = self.player_reo.match(player)
            if not match:
                continue
            frags, ping, name = match.groups()
            self.players.append(Player(1, name, frags, ping))

    def update(self):
        """
        get status
        """
        data = self.command('getstatus')[1]
        self.values = self.parse_status(data)

    def rcon_update(self):
        """
        perform RCON status update
        """
        status, data = self.rcon('status')
        if status == 'print' and data.startswith('map'):
            lines = data.split('\n')

            players = lines[3:]
            self.players = []
            for ply in players:
                while ply.find('  ') != -1:
                    ply = ply.replace('  ', ' ')
                while ply.find(' ') == 0:
                    ply = ply[1:]
                if ply == '':
                    continue
                ply = ply.split(' ')
                try:
                    self.players.append(Player(int(ply[0]), ply[3], int(ply[1]), int(ply[2]), ply[5]))
                except (IndexError, ValueError):
                    continue


if __name__ == '__main__':

    QUAKE = PyQuake3(server='localhost:27960', rcon_password='secret')

    QUAKE.update()

    print("The server name of '%s' is %s, running map %s with %s player(s)." % (QUAKE.get_address(), QUAKE.values['sv_hostname'], QUAKE.values['mapname'], len(QUAKE.players)))

    for gamer in QUAKE.players:
        print("%s with %s frags and a %s ms ping" % (gamer.name, gamer.frags, gamer.ping))

    QUAKE.rcon_update()

    for gamer in QUAKE.players:
        print("%s (%s) has IP address of %s" % (gamer.name, gamer.num, gamer.address))

    QUAKE.rcon('bigtext "pyquake3 is great"')
