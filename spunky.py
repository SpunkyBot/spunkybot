#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Spunky Bot - An automated game server bot
http://www.spunkybot.de
Author: Alexander Kress

This program is released under the MIT License. See LICENSE for more details.

## About ##
Spunky Bot is a lightweight game server administration bot and RCON tool,
inspired by the eb2k9 bot by Shawn Haggard.
The purpose of Spunky Bot is to administrate an Urban Terror 4.1 / 4.2 server
and provide statistical data for players.

## Configuration ##
Modify the UrT server config as follows:
 * seta g_logsync "1"
 * seta g_loghits "1"
Modify the files '/conf/settings.conf' and '/conf/rules.conf'
Run the bot: python spunky.py
"""

__version__ = '1.2.1'


### IMPORTS
import re
import time
import sqlite3
import math
import textwrap
import urllib
import urllib2
import platform
import ConfigParser
import lib.pygeoip as pygeoip
import lib.schedule as schedule

from lib.rcon import Rcon
from lib.rules import Rules
from threading import RLock


### CLASS Log Parser ###
class LogParser(object):
    """
    log file parser
    """
    def __init__(self, config_file):
        """
        create a new instance of LogParser

        @param config_file: The full path of the bot configuration file
        @type  config_file: String
        """
        # hit zone support for UrT > 4.2.013
        self.hit_points = {0: "HEAD", 1: "HEAD", 2: "HELMET", 3: "TORSO", 4: "VEST", 5: "LEFT_ARM", 6: "RIGHT_ARM", 7: "GROIN", 8: "BUTT", 9: "LEFT_UPPER_LEG", 10: "RIGHT_UPPER_LEG", 11: "LEFT_LOWER_LEG", 12: "RIGHT_LOWER_LEG", 13: "LEFT_FOOT", 14: "RIGHT_FOOT"}
        self.hit_item = {1: "UT_MOD_KNIFE", 2: "UT_MOD_BERETTA", 3: "UT_MOD_DEAGLE", 4: "UT_MOD_SPAS", 5: "UT_MOD_MP5K", 6: "UT_MOD_UMP45", 8: "UT_MOD_LR300", 9: "UT_MOD_G36", 10: "UT_MOD_PSG1", 14: "UT_MOD_SR8", 15: "UT_MOD_AK103", 17: "UT_MOD_NEGEV", 19: "UT_MOD_M4", 20: "UT_MOD_GLOCK", 21: "UT_MOD_COLT1911", 22: "UT_MOD_MAC11", 23: "UT_MOD_BLED", 24: "UT_MOD_KICKED", 25: "UT_MOD_KNIFE_THROWN"}
        self.death_cause = {1: "MOD_WATER", 3: "MOD_LAVA", 5: "UT_MOD_TELEFRAG", 6: "MOD_FALLING", 7: "UT_MOD_SUICIDE", 9: "MOD_TRIGGER_HURT", 10: "MOD_CHANGE_TEAM", 12: "UT_MOD_KNIFE", 13: "UT_MOD_KNIFE_THROWN", 14: "UT_MOD_BERETTA", 15: "UT_MOD_DEAGLE", 16: "UT_MOD_SPAS", 17: "UT_MOD_UMP45", 18: "UT_MOD_MP5K", 19: "UT_MOD_LR300", 20: "UT_MOD_G36", 21: "UT_MOD_PSG1", 22: "UT_MOD_HK69", 23: "UT_MOD_BLED", 24: "UT_MOD_KICKED", 25: "UT_MOD_HEGRENADE", 28: "UT_MOD_SR8", 30: "UT_MOD_AK103", 31: "UT_MOD_SPLODED", 32: "UT_MOD_SLAPPED", 33: "UT_MOD_SMITED", 34: "UT_MOD_BOMBED", 35: "UT_MOD_NUKED", 36: "UT_MOD_NEGEV", 37: "UT_MOD_HK69_HIT", 38: "UT_MOD_M4", 39: "UT_MOD_GLOCK", 40: "UT_MOD_COLT1911", 41: "UT_MOD_MAC11", 42: "UT_MOD_FLAG", 43: "UT_MOD_GOOMBA"}

        # RCON commands for the different admin roles
        self.user_cmds = ['bombstats', 'forgiveall, forgiveprev', 'hs', 'register', 'spree', 'stats', 'teams', 'time', 'xlrstats']
        self.mod_cmds = self.user_cmds + ['country', 'leveltest', 'list', 'nextmap', 'mute', 'seen', 'shuffleteams', 'warn']
        self.admin_cmds = self.mod_cmds + ['admins', 'aliases', 'bigtext', 'force', 'kick', 'nuke', 'say', 'tempban', 'warnclear']
        self.fulladmin_cmds = self.admin_cmds + ['ban', 'baninfo', 'ci', 'scream', 'slap', 'swap', 'version', 'veto']
        self.senioradmin_cmds = self.fulladmin_cmds + ['banlist', 'cyclemap', 'kill', 'kiss', 'lookup', 'map', 'maps', 'maprestart', 'moon', 'permban', 'putgroup', 'setnextmap', 'unban', 'ungroup']
        # alphabetic sort of the commands
        self.mod_cmds.sort()
        self.admin_cmds.sort()
        self.fulladmin_cmds.sort()
        self.senioradmin_cmds.sort()

        self.config_file = config_file
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        print "- Imported config file '%s' successful." % config_file

        games_log = config.get('server', 'log_file')
        # open game log file
        self.log_file = open(games_log, 'r')
        # go to the end of the file
        self.log_file.seek(0, 2)
        print "- Parsing games log file '%s' successful." % games_log

        self.ffa_lms_gametype = False
        self.ctf_gametype = False
        self.ts_gametype = False
        self.bomb_gametype = False
        self.freeze_gametype = False
        self.ts_do_team_balance = False
        self.allow_cmd_teams = True
        self.urt42_modversion = True
        self.game = None
        self.players_lock = RLock()

        # enable/disable debug output
        self.verbose = config.getboolean('bot', 'verbose')
        # enable/disable autokick for team killing
        self.tk_autokick = config.getboolean('bot', 'teamkill_autokick')
        # set the maximum allowed ping
        self.max_ping = config.getint('bot', 'max_ping')
        # kick spectator on full server
        self.num_kick_specs = config.getint('bot', 'kick_spec_full_server')
        # set task frequency
        self.task_frequency = config.getint('bot', 'task_frequency')
        # enable/disable message 'Player connected from...'
        self.show_country_on_connect = config.getboolean('bot', 'show_country_on_connect')
        # set teams autobalancer
        self.teams_autobalancer = config.getboolean('bot', 'autobalancer')
        self.allow_cmd_teams_round_end = config.getboolean('bot', 'allow_teams_round_end')
        # support for low gravity server
        if config.has_section('lowgrav'):
            self.support_lowgravity = config.getboolean('lowgrav', 'support_lowgravity')
            self.gravity = config.getint('lowgrav', 'gravity')
        # enable/disable option to get Head Admin by checking existence of head admin in database
        curs.execute("SELECT COUNT(*) FROM `xlrstats` WHERE `admin_role` = 100")
        self.iamgod = True if curs.fetchone()[0] < 1 else False
        # Master Server
        self.base_url = 'http://master.spunkybot.de'
        # Heartbeat packet
        data = {'v': __version__, 'p': config.get('server', 'server_port'), 'o': platform.platform()}
        values = urllib.urlencode(data)
        self.ping_url = '%s/ping.php?%s' % (self.base_url, values)

        # start parsing the games logfile
        self.read_log()

    def find_game_start(self):
        """
        find InitGame start
        """
        seek_amount = 768
        # search within the specified range for the InitGame message
        start_pos = self.log_file.tell() - seek_amount
        end_pos = start_pos + seek_amount
        self.log_file.seek(start_pos)
        game_start = False
        while not game_start:
            while self.log_file:
                line = self.log_file.readline()
                msg = re.search(r"(\d+:\d+)\s([A-Za-z]+:)", line)
                if msg is not None and msg.group(2) == 'InitGame:':
                    game_start = True
                    if 'g_modversion\\4.1' in line:
                        # hit zone support for UrT 4.1
                        self.hit_points = {0: "HEAD", 1: "HELMET", 2: "TORSO", 3: "KEVLAR", 4: "ARMS", 5: "LEGS", 6: "BODY"}
                        self.hit_item = {1: "UT_MOD_KNIFE", 2: "UT_MOD_BERETTA", 3: "UT_MOD_DEAGLE", 4: "UT_MOD_SPAS", 5: "UT_MOD_MP5K", 6: "UT_MOD_UMP45", 8: "UT_MOD_LR300", 9: "UT_MOD_G36", 10: "UT_MOD_PSG1", 14: "UT_MOD_SR8", 15: "UT_MOD_AK103", 17: "UT_MOD_NEGEV", 19: "UT_MOD_M4", 21: "UT_MOD_KICKED", 22: "UT_MOD_KNIFE_THROWN"}
                        self.death_cause = {1: "MOD_WATER", 3: "MOD_LAVA", 5: "UT_MOD_TELEFRAG", 6: "MOD_FALLING", 7: "UT_MOD_SUICIDE", 9: "MOD_TRIGGER_HURT", 10: "MOD_CHANGE_TEAM", 12: "UT_MOD_KNIFE", 13: "UT_MOD_KNIFE_THROWN", 14: "UT_MOD_BERETTA", 15: "UT_MOD_DEAGLE", 16: "UT_MOD_SPAS", 17: "UT_MOD_UMP45", 18: "UT_MOD_MP5K", 19: "UT_MOD_LR300", 20: "UT_MOD_G36", 21: "UT_MOD_PSG1", 22: "UT_MOD_HK69", 23: "UT_MOD_BLED", 24: "UT_MOD_KICKED", 25: "UT_MOD_HEGRENADE", 28: "UT_MOD_SR8", 30: "UT_MOD_AK103", 31: "UT_MOD_SPLODED", 32: "UT_MOD_SLAPPED", 33: "UT_MOD_BOMBED", 34: "UT_MOD_NUKED", 35: "UT_MOD_NEGEV", 37: "UT_MOD_HK69_HIT", 38: "UT_MOD_M4", 39: "UT_MOD_FLAG", 40: "UT_MOD_GOOMBA"}
                        self.urt42_modversion = False
                        self.debug("Game modversion 4.1 detected")
                    if 'g_gametype\\0' in line or 'g_gametype\\1' in line or 'g_gametype\\9' in line:
                        # disable teamkill event and some commands for FFA (0), LMS (1) and Jump (9) mode
                        self.ffa_lms_gametype = True
                    elif 'g_gametype\\7' in line:
                        self.ctf_gametype = True
                    elif 'g_gametype\\4' in line:
                        self.ts_gametype = True
                    elif 'g_gametype\\8' in line:
                        self.bomb_gametype = True
                    elif 'g_gametype\\10' in line:
                        self.freeze_gametype = True
                if self.log_file.tell() > end_pos:
                    break
                elif len(line) == 0:
                    break
            if self.log_file.tell() < seek_amount:
                self.log_file.seek(0, 0)
            else:
                cur_pos = start_pos - seek_amount
                end_pos = start_pos
                start_pos = cur_pos
                if start_pos < 0:
                    start_pos = 0
                self.log_file.seek(start_pos)

    def read_log(self):
        """
        read the logfile
        """
        if self.task_frequency > 0:
            # schedule the task
            if self.task_frequency < 10:
                # avoid flooding with too less delay
                schedule.every(10).seconds.do(self.taskmanager)
            else:
                schedule.every(self.task_frequency).seconds.do(self.taskmanager)
        # schedule the task
        schedule.every(12).hours.do(self.send_heartbeat)
        # schedule the task
        schedule.every(2).hours.do(self.remove_expired_db_entries)

        self.find_game_start()

        # create instance of Game
        self.game = Game(self.config_file, self.urt42_modversion)

        self.log_file.seek(0, 2)
        while self.log_file:
            schedule.run_pending()
            line = self.log_file.readline()
            if len(line) != 0:
                self.parse_line(line)
            else:
                if not self.game.live:
                    self.game.go_live()
                time.sleep(.125)

    def send_heartbeat(self):
        """
        send heartbeat packet
        """
        try:
            urllib2.urlopen(self.ping_url)
        except urllib2.URLError:
            pass

    def remove_expired_db_entries(self):
        """
        delete expired ban points
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        values = (timestamp,)
        # remove expired ban_points
        curs.execute("DELETE FROM `ban_points` WHERE `expires` < ?", values)
        conn.commit()

    def taskmanager(self):
        """
        - check warnings and kick players with too many warnings
        - check for spectators and set warning
        - check ping of all players and set warning for high ping user
        """
        try:
            # get rcon status
            self.game.get_rcon_handle().get_status()
            with self.players_lock:
                # get number of connected players
                counter = len(self.game.players) - 1  # bot is counted as player

                # check amount of warnings and kick player if needed
                for player in self.game.players.itervalues():
                    player_name = player.get_name()
                    player_num = player.get_player_num()
                    player_admin_role = player.get_admin_role()
                    # kick player with 3 or more warnings, Admins will never get kicked
                    if player.get_warning() > 2 and player_admin_role < 40:
                        self.game.rcon_say("^2%s ^7was kicked, too many warnings" % player_name)
                        self.game.kick_player(player_num, reason='too many warnings')
                        continue
                    # kick player with high ping after 3 warnings, Admins will never get kicked
                    elif player.get_high_ping() > 2 and player_admin_role < 40:
                        self.game.rcon_say("^2%s ^7was kicked, ping too high for this server ^7[^4%s^7]" % (player_name, player.get_ping_value()))
                        self.game.kick_player(player_num, reason='fix your ping')
                        continue
                    # kick spectator after 3 warnings, Moderator or higher levels will not get kicked
                    elif player.get_spec_warning() > 2 and player_admin_role < 20:
                        self.game.rcon_say("^2%s ^7was kicked, spectator too long on full server" % player_name)
                        self.game.kick_player(player_num, reason='spectator too long on full server')
                        continue

                    # check for spectators and set warning
                    if self.num_kick_specs > 0:
                        # ignore player with name prefix GTV-
                        if 'GTV-' in player_name:
                            continue
                        # if player is spectator on full server, inform player and increase warn counter
                        # GTV or Moderator or higher levels will not get the warning
                        elif counter > self.num_kick_specs and player.get_team() == 3 and player_admin_role < 20 and player.get_time_joined() < (time.time() - 30) and player_num != 1022:
                            player.add_spec_warning()
                            self.game.rcon_tell(player_num, "^1WARNING ^7[^3%d^7]: ^7You are spectator too long on full server" % player.get_spec_warning(), False)
                        # reset spec warning
                        else:
                            player.clear_spec_warning()

                    # warn player with 3 warnings, Admins will never get the alert warning
                    if (player.get_warning() == 3 or player.get_spec_warning() == 3) and player_admin_role < 40:
                        self.game.rcon_say("^1ALERT: ^2%s ^7auto-kick from warnings if not cleared" % player_name)

                # check for player with high ping
                if self.max_ping > 0:
                    # rcon update status
                    self.game.get_rcon_handle().quake.rcon_update()
                    for player in self.game.get_rcon_handle().quake.players:
                        # if ping is too high, increase warn counter, Admins or higher levels will not get the warning
                        try:
                            ping_value = player.ping
                            gameplayer = self.game.players[player.num]
                        except KeyError:
                            continue
                        else:
                            if self.max_ping < ping_value < 999 and gameplayer.get_admin_role() < 40:
                                gameplayer.add_high_ping(ping_value)
                                self.game.rcon_tell(player.num, "^1WARNING ^7[^3%d^7]: ^7Your ping is too high [^4%d^7]. ^3The maximum allowed ping is %d." % (gameplayer.get_high_ping(), ping_value, self.max_ping), False)
                            else:
                                gameplayer.clear_high_ping()
        except Exception, err:
            print "%s: %s" % (err.__class__.__name__, err)

    def parse_line(self, string):
        """
        parse the logfile and search for specific action
        """
        line = string[7:]
        tmp = line.split(":", 1)
        if len(tmp) > 1:
            line = tmp[1].strip()
        else:
            line = tmp[0].strip()
        try:
            if tmp is not None:
                if tmp[0].lstrip() == 'InitGame':
                    self.new_game(line)
                elif tmp[0].lstrip() == 'Warmup':
                    self.handle_warmup()
                elif tmp[0].lstrip() == 'InitRound':
                    self.handle_initround()
                elif tmp[0].lstrip() == 'ClientUserinfo':
                    self.handle_userinfo(line)
                elif tmp[0].lstrip() == 'ClientUserinfoChanged':
                    self.handle_userinfo_changed(line)
                elif tmp[0].lstrip() == 'ClientBegin':
                    self.handle_begin(line)
                elif tmp[0].lstrip() == 'ClientDisconnect':
                    self.handle_disconnect(line)
                elif tmp[0].lstrip() == 'Kill':
                    self.handle_kill(line)
                elif tmp[0].lstrip() == 'Hit':
                    self.handle_hit(line)
                elif tmp[0].lstrip() == 'Freeze':
                    self.handle_freeze(line)
                elif tmp[0].lstrip() == 'ThawOutFinished':
                    self.handle_thawout(line)
                elif tmp[0].lstrip() == 'ShutdownGame':
                    self.debug("Shutting down game...")
                    self.game.rcon_clear()
                elif tmp[0].lstrip() == 'say':
                    self.handle_say(line)
                elif tmp[0].lstrip() == 'Flag':
                    self.handle_flag(line)
                elif tmp[0].lstrip() == 'Exit':
                    self.handle_exit()
                elif tmp[0].lstrip() == 'SurvivorWinner':
                    self.handle_teams_ts_mode()
                elif 'Bomb' in tmp[0]:
                    self.handle_bomb(line)
                elif 'Pop' in tmp[0]:
                    self.debug("Bomb exploded!")
                    self.handle_teams_ts_mode()
        except (IndexError, KeyError):
            pass
        except Exception, err:
            print "%s: %s" % (err.__class__.__name__, err)

    def explode_line(self, line):
        """
        explode line
        """
        arr = line.lstrip().lstrip('\\').split('\\')
        key = True
        key_val = None
        values = {}
        for item in arr:
            if key:
                key_val = item
                key = False
            else:
                values[key_val.rstrip()] = item.rstrip()
                key_val = None
                key = True
        return values

    def new_game(self, line):
        """
        set-up a new game
        """
        self.ffa_lms_gametype = True if ('g_gametype\\0' in line or 'g_gametype\\1' in line or 'g_gametype\\9' in line) else False
        self.ctf_gametype = True if 'g_gametype\\7' in line else False
        self.ts_gametype = True if 'g_gametype\\4' in line else False
        self.bomb_gametype = True if 'g_gametype\\8' in line else False
        self.freeze_gametype = True if 'g_gametype\\10' in line else False
        self.debug("Starting game...")
        self.game.rcon_clear()

        # wait for server loading the new map
        time.sleep(4)

        # set the current map
        self.game.set_current_map()
        # load all available maps
        self.game.set_all_maps()

        # support for low gravity server
        if self.support_lowgravity:
            self.game.send_rcon("set g_gravity %d" % self.gravity)

    def handle_warmup(self):
        """
        handle warmup
        """
        with self.players_lock:
            for player in self.game.players.itervalues():
                player.reset()
        self.allow_cmd_teams = True
        self.autobalancer()

    def handle_initround(self):
        """
        handle Init Round
        """
        self.debug("Round started...")
        if self.ctf_gametype:
            with self.players_lock:
                for player in self.game.players.itervalues():
                    player.reset_flag_stats()
        elif self.ts_gametype or self.bomb_gametype or self.freeze_gametype:
            if self.allow_cmd_teams_round_end:
                self.allow_cmd_teams = False

    def handle_exit(self):
        """
        handle Exit of a match, show Awards, store user score in database
        """
        self.debug("Match ended!")
        self.handle_awards()
        self.allow_cmd_teams = True
        with self.players_lock:
            for player in self.game.players.itervalues():
                # store score in database
                player.save_info()
                # reset team lock
                player.set_team_lock(None)

    def handle_userinfo(self, line):
        """
        handle player user information, auto-kick known cheater ports or guids
        """
        with self.players_lock:
            player_num = int(line[:2].strip())
            line = line[2:].lstrip("\\").lstrip()
            values = self.explode_line(line)
            challenge = True if 'challenge' in values else False
            try:
                guid = values['cl_guid'].rstrip('\n')
                name = re.sub(r"\s+", "", values['name'])
                ip_port = values['ip']
            except KeyError:
                if 'cl_guid' in values:
                    guid = values['cl_guid']
                elif 'skill' in values:
                    # bot connecting
                    guid = "BOT%d" % player_num
                else:
                    guid = "None"
                    self.game.send_rcon("Player with invalid GUID kicked")
                    self.game.send_rcon("kick %d" % player_num)
                if 'name' in values:
                    name = re.sub(r"\s+", "", values['name'])
                else:
                    name = "UnnamedPlayer"
                    self.game.send_rcon("Player with invalid name kicked")
                    self.game.send_rcon("kick %d" % player_num)
                if 'ip' in values:
                    ip_port = values['ip']
                else:
                    ip_port = "0.0.0.0:0"

            ip_address = ip_port.split(":")[0].strip()
            port = ip_port.split(":")[1].strip()

            if player_num not in self.game.players:
                player = Player(player_num, ip_address, guid, name)
                self.game.add_player(player)
                # kick banned player
                player_ban_id = self.game.players[player_num].get_ban_id()
                if player_ban_id:
                    self.game.send_rcon("kick %d" % player_num)
                    self.game.send_rcon("^7%s ^1banned ^7(ID @%d)" % (name, player_ban_id))
                else:
                    if self.show_country_on_connect:
                        self.game.rcon_say("^7%s ^7connected from %s" % (name, self.game.players[player_num].get_country()))

            if self.game.players[player_num].get_guid() != guid:
                self.game.players[player_num].set_guid(guid)
            if self.game.players[player_num].get_name() != name:
                self.game.players[player_num].set_name(name)

            # kick player with hax guid 'kemfew'
            if "KEMFEW" in guid.upper():
                self.game.send_rcon("Cheater GUID detected for %s -> Player kicked" % name)
                self.game.send_rcon("kick %d" % player_num)
            if "WORLD" in guid.upper() or "UNKNOWN" in guid.upper():
                self.game.send_rcon("Invalid GUID detected for %s -> Player kicked" % name)
                self.game.send_rcon("kick %d" % player_num)

            if challenge:
                self.debug("Player %d %s is challenging the server and has the guid %s" % (player_num, name, guid))
                # kick player with hax port 1337 or 1024
                if port == "1337" or port == "1024":
                    self.game.send_rcon("Cheater Port detected for %s -> Player kicked" % name)
                    self.game.send_rcon("kick %d" % player_num)
            else:
                if 'name' in values and values['name'] != self.game.players[player_num].get_name():
                    self.game.players[player_num].set_name(values['name'])

    def handle_userinfo_changed(self, line):
        """
        handle player changes
        """
        with self.players_lock:
            player_num = int(line[:2].strip())
            player = self.game.players[player_num]
            line = line[2:].lstrip("\\")
            try:
                values = self.explode_line(line)
                team_num = int(values['t'])
                player.set_team(team_num)
                name = re.sub(r"\s+", "", values['n'])
            except KeyError:
                team_num = 3
                player.set_team(team_num)
                name = self.game.players[player_num].get_name()

            # set new name, if player changed name
            if not(self.game.players[player_num].get_name() == name):
                self.game.players[player_num].set_name(name)

            # move locked player to the defined team, if player tries to change teams
            team_lock = self.game.players[player_num].get_team_lock()
            if team_lock and Player.teams[team_num] != team_lock:
                self.game.rcon_forceteam(player_num, team_lock)
                self.game.rcon_tell(player_num, "^3You are forced to: ^7%s" % team_lock)
            self.debug("Player %d %s joined team %s" % (player_num, name, Player.teams[team_num]))

    def handle_begin(self, line):
        """
        handle player entering game
        """
        with self.players_lock:
            player_num = int(line[:2].strip())
            player = self.game.players[player_num]
            player_name = player.get_name()
            # Welcome message for registered players
            if player.get_registered_user() and player.get_welcome_msg():
                self.game.rcon_tell(player_num, "^7[^2Authed^7] Welcome back %s, you are ^2%s^7, last visit %s, you played %s times" % (player_name, player.roles[player.get_admin_role()], player.get_last_visit(), player.get_num_played()), False)
                # disable welcome message for next rounds
                player.disable_welcome_msg()
            self.debug("Player %d %s has entered the game" % (player_num, player_name))

    def handle_disconnect(self, line):
        """
        handle player disconnect
        """
        with self.players_lock:
            player_num = int(line[:2].strip())
            player = self.game.players[player_num]
            player.save_info()
            player.reset()
            del self.game.players[player_num]
            self.debug("Player %d %s has left the game" % (player_num, player.get_name()))

    def handle_hit(self, line):
        """
        handle all kind of hits
        """
        with self.players_lock:
            parts = line.split(":", 1)
            info = parts[0].split(" ")
            hitter_id = int(info[1])
            victim_id = int(info[0])
            hitter = self.game.players[hitter_id]
            victim = self.game.players[victim_id]
            hitter_name = hitter.get_name()
            victim_name = victim.get_name()
            hitpoint = int(info[2])
            hit_item = int(info[3])
            # increase summary of all hits
            hitter.set_all_hits()

            if hitpoint in self.hit_points:
                if self.hit_points[hitpoint] == 'HEAD' or self.hit_points[hitpoint] == 'HELMET':
                    hitter.headshot()
                    hitter_hs_count = hitter.get_headshots()
                    player_color = "^1" if (hitter.get_team() == 1) else "^4"
                    hs_plural = "headshots" if hitter_hs_count > 1 else "headshot"
                    percentage = int(round(float(hitter_hs_count) / float(hitter.get_all_hits()), 2) * 100)
                    self.game.send_rcon("%s%s ^7has %d %s (%d percent)" % (player_color, hitter_name, hitter_hs_count, hs_plural, percentage))
                self.debug("Player %d %s hit %d %s in the %s with %s" % (hitter_id, hitter_name, victim_id, victim_name, self.hit_points[hitpoint], self.hit_item[hit_item]))

    def handle_kill(self, line):
        """
        handle kills
        """
        with self.players_lock:
            parts = line.split(":", 1)
            info = parts[0].split(" ")
            k_name = parts[1].strip().split(" ")[0]
            killer_id = int(info[0])
            victim_id = int(info[1])
            death_cause = self.death_cause[int(info[2])]
            victim = self.game.players[victim_id]

            if k_name != "<non-client>":
                killer = self.game.players[killer_id]
            else:
                # killed by World
                killer = self.game.players[1022]
                killer_id = 1022

            killer_name = killer.get_name()
            victim_name = victim.get_name()
            tk_event = False

            # teamkill event - disabled for FFA, LMS, Jump, for all other game modes team kills are counted and punished
            if not self.ffa_lms_gametype:
                if (victim.get_team() == killer.get_team() and victim_id != killer_id) and death_cause != "UT_MOD_BOMBED":
                    tk_event = True
                    # increase team kill counter for killer and kick for too many team kills
                    killer.team_kill()
                    # increase team death counter for victim
                    victim.team_death()
                    # Regular and higher will not get punished
                    if killer.get_admin_role() < 2 and self.tk_autokick:
                        # list of players of TK victim
                        killer.add_tk_victims(victim_id)
                        # list of players who killed victim
                        victim.add_killed_me(killer_id)
                        self.game.rcon_tell(killer_id, "^7Do not attack teammates, you ^1killed ^7%s" % victim_name)
                        self.game.rcon_tell(victim_id, "^7Type ^3!fp ^7to forgive ^3%s" % killer_name)
                        if len(killer.get_tk_victim_names()) >= 5:
                            # add TK ban points - 15 minutes
                            duration = killer.add_ban_point('tk, auto-kick', 900)
                            if duration > 0:
                                self.game.rcon_say("%s ^7banned for ^1%d minutes ^7for team killing" % (killer_name, duration))
                            else:
                                self.game.rcon_say("^7Player ^2%s ^7kicked for team killing" % killer_name)
                            self.game.kick_player(killer_id, reason='stop team killing')
                        elif len(killer.get_tk_victim_names()) == 2:
                            self.game.rcon_tell(killer_id, "^1WARNING ^7[^31^7]: ^7For team killing you will get kicked")
                        elif len(killer.get_tk_victim_names()) == 3:
                            self.game.rcon_tell(killer_id, "^1WARNING ^7[^32^7]: ^7For team killing you will get kicked")
                        elif len(killer.get_tk_victim_names()) == 4:
                            self.game.rcon_tell(killer_id, "^1WARNING ^7[^33^7]: ^7For team killing you will get kicked")

            suicide_reason = ['UT_MOD_SUICIDE', 'MOD_FALLING', 'MOD_WATER', 'MOD_LAVA', 'MOD_TRIGGER_HURT', 'UT_MOD_SPLODED', 'UT_MOD_SLAPPED', 'UT_MOD_SMITED']
            suicide_weapon = ['UT_MOD_HEGRENADE', 'UT_MOD_HK69', 'UT_MOD_NUKED', 'UT_MOD_BOMBED']
            # suicide counter
            if death_cause in suicide_reason or (killer_id == victim_id and death_cause in suicide_weapon):
                victim.suicide()
                victim.die()
                self.debug("Player %d %s committed suicide with %s" % (victim_id, victim_name, death_cause))
            # kill counter
            elif not tk_event and int(info[2]) != 10:  # 10: MOD_CHANGE_TEAM
                killer.kill()
                if self.bomb_gametype:
                    # bomb carrier killed
                    if victim.get_bombholder():
                        killer.kill_bomb_carrier()
                    # killed with bomb
                    if death_cause == 'UT_MOD_BOMBED':
                        killer.kills_with_bomb()
                killer_color = "^1" if (killer.get_team() == 1) else "^4"
                killer_killing_streak = killer.get_killing_streak()
                kill_streak_msg = {5: "is on a killing spree (^15 ^7kills in a row)",
                                   10: "is on a rampage (^110 ^7kills in a row)",
                                   15: "is unstoppable (^115 ^7kills in a row)",
                                   20: "is godlike (^120 ^7kills in a row)"}
                if killer_killing_streak in kill_streak_msg and killer_id != 1022:
                    self.game.rcon_say("%s%s ^7%s" % (killer_color, killer_name, kill_streak_msg[killer_killing_streak]))

                victim_color = "^1" if (victim.get_team() == 1) else "^4"
                if victim.get_killing_streak() >= 20 and killer_name != victim_name and killer_id != 1022:
                    self.game.rcon_say("%s%s's ^7godlike was ended by %s%s!" % (victim_color, victim_name, killer_color, killer_name))
                elif victim.get_killing_streak() >= 15 and killer_name != victim_name and killer_id != 1022:
                    self.game.rcon_say("%s%s's ^7unstoppable was ended by %s%s!" % (victim_color, victim_name, killer_color, killer_name))
                elif victim.get_killing_streak() >= 10 and killer_name != victim_name and killer_id != 1022:
                    self.game.rcon_say("%s%s's ^7rampage was ended by %s%s!" % (victim_color, victim_name, killer_color, killer_name))
                elif victim.get_killing_streak() >= 5 and killer_name != victim_name and killer_id != 1022:
                    self.game.rcon_say("%s%s's ^7killing spree was ended by %s%s!" % (victim_color, victim_name, killer_color, killer_name))
                # death counter
                victim.die()
                self.debug("Player %d %s killed %d %s with %s" % (killer_id, killer_name, victim_id, victim_name, death_cause))

    def player_found(self, user):
        """
        return True and instance of player or False and message text
        """
        victim = None
        name_list = []
        append = name_list.append
        for player in self.game.players.itervalues():
            player_name = player.get_name()
            player_num = player.get_player_num()
            player_id = "@%d" % player.get_player_id()
            if (user.upper() == player_name.upper() or user == str(player_num) or user == player_id) and player_num != 1022:
                victim = player
                name_list = ["^3%s [^2%d^3]" % (player_name, player_num)]
                break
            elif user.upper() in player_name.upper() and player_num != 1022:
                victim = player
                append("^3%s [^2%d^3]" % (player_name, player_num))
        if len(name_list) == 0:
            if user.startswith('@'):
                return self.offline_player(user)
            else:
                return False, None, "No Player found"
        elif len(name_list) > 1:
            return False, None, "^7Players matching %s: ^3%s" % (user, ', '.join(name_list))
        else:
            return True, victim, None

    def offline_player(self, user_id):
        player_id = user_id.lstrip('@')
        if player_id.isdigit():
            if int(player_id) > 1:
                values = (player_id,)
                curs.execute("SELECT `guid`,`name`,`ip_address` FROM `player` WHERE `id` = ?", values)
                result = curs.fetchone()
                if result:
                    victim = Player(player_num=1023, ip_address=str(result[2]), guid=str(result[0]), name=str(result[1]))
                    victim.define_offline_player(player_id=int(player_id))
                    return True, victim, None
                else:
                    return False, None, "No Player found"
            else:
                return False, None, "No Player found"
        else:
            return False, None, "No Player found"

    def map_found(self, map_name):
        """
        return True and map name or False and message text
        """
        map_list = []
        append = map_list.append
        for maps in self.game.get_all_maps():
            if map_name.lower() == maps or ('ut4_%s' % map_name.lower()) == maps:
                append(maps)
                break
            elif map_name.lower() in maps:
                append(maps)
        if len(map_list) == 0:
            return False, None, "Map not found"
        elif len(map_list) > 1:
            return False, None, "^7Maps matching %s: ^3%s" % (map_name, ', '.join(map_list))
        else:
            return True, map_list[0], None

    def handle_say(self, line):
        """
        handle say commands
        """
        reason_dict = {'obj': 'go for objective', 'camp': 'stop camping', 'spam': 'do not spam, shut-up!', 'lang': 'bad language', 'racism': 'racism is not tolerated',
                       'ping': 'fix your ping', 'afk': 'away from keyboard', 'tk': 'stop team killing', 'spec': 'spectator too long on full server', 'ci': 'connection interrupted'}

        with self.players_lock:
            line = line.strip()
            try:
                tmp = line.split(" ")
                sar = {'player_num': int(tmp[0]), 'name': tmp[1], 'command': tmp[2]}
            except IndexError:
                sar = {'player_num': None, 'name': None, 'command': None}

            if sar['command'] == '!mapstats':
                self.game.rcon_tell(sar['player_num'], "^2%d ^7kills - ^2%d ^7deaths" % (self.game.players[sar['player_num']].get_kills(), self.game.players[sar['player_num']].get_deaths()))
                self.game.rcon_tell(sar['player_num'], "^2%d ^7kills in a row - ^2%d ^7teamkills" % (self.game.players[sar['player_num']].get_killing_streak(), self.game.players[sar['player_num']].get_team_kill_count()))
                self.game.rcon_tell(sar['player_num'], "^2%d ^7total hits - ^2%d ^7headshots" % (self.game.players[sar['player_num']].get_all_hits(), self.game.players[sar['player_num']].get_headshots()))
                if self.ctf_gametype:
                    self.game.rcon_tell(sar['player_num'], "^2%d ^7flags captured - ^2%d ^7flags returned" % (self.game.players[sar['player_num']].get_flags_captured(), self.game.players[sar['player_num']].get_flags_returned()))
                elif self.bomb_gametype:
                    self.game.rcon_tell(sar['player_num'], "^7planted: ^2%d ^7- defused: ^2%d" % (self.game.players[sar['player_num']].get_planted_bomb(), self.game.players[sar['player_num']].get_defused_bomb()))
                    self.game.rcon_tell(sar['player_num'], "^7bomb carrier killed: ^2%d ^7- enemies bombed: ^2%d" % (self.game.players[sar['player_num']].get_bomb_carrier_kills(), self.game.players[sar['player_num']].get_kills_with_bomb()))
                elif self.freeze_gametype:
                    self.game.rcon_tell(sar['player_num'], "^freeze: ^2%d ^7- thaw out: ^2%d" % (self.game.players[sar['player_num']].get_freeze(), self.game.players[sar['player_num']].get_thawout()))

            elif sar['command'] == '!help' or sar['command'] == '!h':
                ## TO DO - specific help for each command
                if self.game.players[sar['player_num']].get_admin_role() < 20:
                    self.game.rcon_tell(sar['player_num'], "^7Available commands:")
                    self.game.rcon_tell(sar['player_num'], ", ".join(self.user_cmds), False)
                # help for mods - additional commands
                elif self.game.players[sar['player_num']].get_admin_role() == 20:
                    self.game.rcon_tell(sar['player_num'], "^7Moderator commands:")
                    self.game.rcon_tell(sar['player_num'], ", ".join(self.mod_cmds), False)
                # help for admins - additional commands
                elif self.game.players[sar['player_num']].get_admin_role() == 40:
                    self.game.rcon_tell(sar['player_num'], "^7Admin commands:")
                    self.game.rcon_tell(sar['player_num'], ", ".join(self.admin_cmds), False)
                elif self.game.players[sar['player_num']].get_admin_role() == 60:
                    self.game.rcon_tell(sar['player_num'], "^7Full Admin commands:")
                    self.game.rcon_tell(sar['player_num'], ", ".join(self.fulladmin_cmds), False)
                elif self.game.players[sar['player_num']].get_admin_role() >= 80:
                    self.game.rcon_tell(sar['player_num'], "^7Senior Admin commands:")
                    self.game.rcon_tell(sar['player_num'], ", ".join(self.senioradmin_cmds), False)

## player commands
            # register - register yourself as a basic user
            elif sar['command'] == '!register':
                if not self.game.players[sar['player_num']].get_registered_user():
                    self.game.players[sar['player_num']].register_user_db(role=1)
                    self.game.rcon_tell(sar['player_num'], "%s ^7put in group User" % self.game.players[sar['player_num']].get_name())
                else:
                    self.game.rcon_tell(sar['player_num'], "%s ^7is already in a higher level group" % self.game.players[sar['player_num']].get_name())

            # hs - display headshot counter
            elif sar['command'] == '!hs':
                hs_count = self.game.players[sar['player_num']].get_headshots()
                if hs_count > 0:
                    self.game.rcon_tell(sar['player_num'], "^7You made ^2%d ^7headshot%s" % (hs_count, 's' if hs_count > 1 else ''))
                else:
                    self.game.rcon_tell(sar['player_num'], "^7You made no headshot")

            # spree - display kill streak counter
            elif sar['command'] == '!spree':
                spree_count = self.game.players[sar['player_num']].get_killing_streak()
                if spree_count > 0:
                    self.game.rcon_tell(sar['player_num'], "^7You have ^2%d ^7kill%s in a row" % (spree_count, 's' if spree_count > 1 else ''))
                else:
                    self.game.rcon_tell(sar['player_num'], "^7You are currently not having a killing spree")

            # bombstats - display bomb statistics
            elif sar['command'] == '!bombstats':
                if self.bomb_gametype:
                    self.game.rcon_tell(sar['player_num'], "^7planted: ^2%d ^7- defused: ^2%d" % (self.game.players[sar['player_num']].get_planted_bomb(), self.game.players[sar['player_num']].get_defused_bomb()))
                    self.game.rcon_tell(sar['player_num'], "^7bomb carrier killed: ^2%d ^7- enemies bombed: ^2%d" % (self.game.players[sar['player_num']].get_bomb_carrier_kills(), self.game.players[sar['player_num']].get_kills_with_bomb()))

            # freezestats - display freeze tag statistics
            elif sar['command'] == '!freezestats':
                if self.freeze_gametype:
                    self.game.rcon_tell(sar['player_num'], "^freeze: ^2%d ^7- thaw out: ^2%d" % (self.game.players[sar['player_num']].get_freeze(), self.game.players[sar['player_num']].get_thawout()))

            # time - display the servers current time
            elif sar['command'] == '!time' or sar['command'] == '@time':
                msg = "^7%s" % time.strftime("%H:%M", time.localtime(time.time()))
                self.tell_say_message(sar, msg)

            # teams - balance teams
            elif sar['command'] == '!teams':
                if not self.ffa_lms_gametype:
                    self.handle_team_balance()

            # stats - display current map stats
            elif sar['command'] == '!stats':
                if not self.freeze_gametype:
                    if self.game.players[sar['player_num']].get_deaths() == 0:
                        ratio = 1.0
                    else:
                        ratio = round(float(self.game.players[sar['player_num']].get_kills()) / float(self.game.players[sar['player_num']].get_deaths()), 2)
                    self.game.rcon_tell(sar['player_num'], "^7Map Stats %s: ^7K ^2%d ^7D ^3%d ^7TK ^1%d ^7Ratio ^5%s ^7HS ^2%d" % (self.game.players[sar['player_num']].get_name(), self.game.players[sar['player_num']].get_kills(), self.game.players[sar['player_num']].get_deaths(), self.game.players[sar['player_num']].get_team_kill_count(), ratio, self.game.players[sar['player_num']].get_headshots()))
                else:
                    # Freeze Tag
                    self.game.rcon_tell(sar['player_num'], "^7Freeze Stats %s: ^7F ^2%d ^7T ^3%d ^7TK ^1%d ^7HS ^2%d" % (self.game.players[sar['player_num']].get_name(), self.game.players[sar['player_num']].get_freeze(), self.game.players[sar['player_num']].get_thawout(), self.game.players[sar['player_num']].get_team_kill_count(), self.game.players[sar['player_num']].get_headshots()))

            # xlrstats - display full player stats
            elif sar['command'] == '!xlrstats':
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip()
                    for player in self.game.players.itervalues():
                        if (arg.upper() in (player.get_name()).upper()) or arg == str(player.get_player_num()):
                            if player.get_registered_user():
                                if player.get_db_deaths() == 0:
                                    ratio = 1.0
                                else:
                                    ratio = round(float(player.get_db_kills()) / float(player.get_db_deaths()), 2)
                                self.game.rcon_tell(sar['player_num'], "^7Stats %s: ^7K ^2%d ^7D ^3%d ^7TK ^1%d ^7Ratio ^5%s ^7HS ^2%d" % (player.get_name(), player.get_db_kills(), player.get_db_deaths(), player.get_db_tks(), ratio, player.get_db_headshots()))
                            else:
                                self.game.rcon_tell(sar['player_num'], "^7Sorry, this player is not registered")
                else:
                    if self.game.players[sar['player_num']].get_registered_user():
                        if self.game.players[sar['player_num']].get_db_deaths() == 0:
                            ratio = 1.0
                        else:
                            ratio = round(float(self.game.players[sar['player_num']].get_db_kills()) / float(self.game.players[sar['player_num']].get_db_deaths()), 2)
                        self.game.rcon_tell(sar['player_num'], "^7Stats %s: ^7K ^2%d ^7D ^3%d ^7TK ^1%d ^7Ratio ^5%s ^7HS ^2%d" % (self.game.players[sar['player_num']].get_name(), self.game.players[sar['player_num']].get_db_kills(), self.game.players[sar['player_num']].get_db_deaths(), self.game.players[sar['player_num']].get_db_tks(), ratio, self.game.players[sar['player_num']].get_db_headshots()))
                    else:
                        self.game.rcon_tell(sar['player_num'], "^7You need to ^2!register ^7first")

            # forgive last team kill
            elif sar['command'] == '!forgiveprev' or sar['command'] == '!fp' or sar['command'] == '!f':
                victim = self.game.players[sar['player_num']]
                if victim.get_killed_me():
                    forgive_player_num = victim.get_killed_me()[-1]
                    forgive_player = self.game.players[forgive_player_num]
                    victim.clear_tk(forgive_player_num)
                    forgive_player.clear_killed_me(victim.get_player_num())
                    self.game.rcon_say("^7%s has forgiven %s's attack" % (victim.get_name(), forgive_player.get_name()))
                else:
                    self.game.rcon_tell(sar['player_num'], "No one to forgive")

            # forgive all team kills
            elif sar['command'] == '!forgiveall' or sar['command'] == '!fa':
                victim = self.game.players[sar['player_num']]
                msg = []
                append = msg.append
                if victim.get_killed_me():
                    all_forgive_player_num_list = victim.get_killed_me()
                    forgive_player_num_list = list(set(all_forgive_player_num_list))
                    victim.clear_all_tk()
                    for forgive_player_num in forgive_player_num_list:
                        forgive_player = self.game.players[forgive_player_num]
                        forgive_player.clear_killed_me(victim.get_player_num())
                        append(forgive_player.get_name())
                if msg:
                    self.game.rcon_say("^7%s has forgiven: %s" % (victim.get_name(), ", ".join(msg)))
                else:
                    self.game.rcon_tell(sar['player_num'], "No one to forgive")

## mod level 20
            # country
            elif (sar['command'] == '!country' or sar['command'] == '@country') and self.game.players[sar['player_num']].get_admin_role() >= 20:
                if line.split(sar['command'])[1]:
                    user = line.split(sar['command'])[1].strip()
                    found, victim, msg = self.player_found(user)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        msg = "Country ^3%s: ^7%s" % (victim.get_name(), victim.get_country())
                        self.tell_say_message(sar, msg)
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !country <name>")

            # leveltest
            elif (sar['command'] == '!leveltest' or sar['command'] == '!lt') and self.game.players[sar['player_num']].get_admin_role() >= 20:
                if line.split(sar['command'])[1]:
                    user = line.split(sar['command'])[1].strip()
                    found, victim, msg = self.player_found(user)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        self.game.rcon_tell(sar['player_num'], "Level ^3%s [^2%d^3]: ^7%s" % (victim.get_name(), victim.get_admin_role(), victim.roles[victim.get_admin_role()]))
                else:
                    self.game.rcon_tell(sar['player_num'], "Level ^3%s [^2%d^3]: ^7%s" % (self.game.players[sar['player_num']].get_name(), self.game.players[sar['player_num']].get_admin_role(), self.game.players[sar['player_num']].roles[self.game.players[sar['player_num']].get_admin_role()]))

            # list - list all connected players
            elif sar['command'] == '!list' and self.game.players[sar['player_num']].get_admin_role() >= 20:
                msg = "^7Players online: %s" % ", ".join(["^3%s [^2%d^3]" % (player.get_name(), player.get_player_num()) for player in self.game.players.itervalues() if player.get_player_num() != 1022])
                self.game.rcon_tell(sar['player_num'], msg)

            # nextmap - display the next map in rotation
            elif (sar['command'] == '!nextmap' or sar['command'] == '@nextmap') and self.game.players[sar['player_num']].get_admin_role() >= 20:
                g_nextmap = self.game.get_rcon_handle().get_cvar('g_nextmap').split(" ")[0].strip()
                if g_nextmap in self.game.get_all_maps():
                    msg = "^7Next Map: ^3%s" % g_nextmap
                    self.game.next_mapname = g_nextmap
                else:
                    msg = "^7Next Map: ^3%s" % self.game.next_mapname
                self.tell_say_message(sar, msg)

            # mute - mute or unmute a player
            elif sar['command'] == '!mute' and self.game.players[sar['player_num']].get_admin_role() >= 20:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip().split(' ')
                    if len(arg) > 1:
                        user = arg[0]
                        duration = arg[1]
                        if not duration.isdigit():
                            duration = ''
                    else:
                        user = arg[0]
                        duration = ''
                    found, victim, msg = self.player_found(user)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        self.game.send_rcon("mute %d %s" % (victim.get_player_num(), duration))
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !mute <name> [<seconds>]")

            # seen - display when the player was last seen
            elif sar['command'] == '!seen' and self.game.players[sar['player_num']].get_admin_role() >= 20:
                if line.split(sar['command'])[1]:
                    user = line.split(sar['command'])[1].strip()
                    found, victim, msg = self.player_found(user)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        if victim.get_registered_user():
                            self.game.rcon_tell(sar['player_num'], "%s ^7was last seen on %s" % (victim.get_name(), victim.get_last_visit()))
                        else:
                            self.game.rcon_tell(sar['player_num'], "%s ^7is not a registered user" % victim.get_name())
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !seen <name>")

            # shuffleteams
            elif (sar['command'] == '!shuffleteams' or sar['command'] == '!shuffle') and self.game.players[sar['player_num']].get_admin_role() >= 20:
                if not self.ffa_lms_gametype:
                    self.game.send_rcon('shuffleteams')
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Command is disabled for this game mode")

            # warn - warn user
            elif (sar['command'] == '!warn' or sar['command'] == '!w') and self.game.players[sar['player_num']].get_admin_role() >= 20:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip().split(' ')
                    if len(arg) > 1:
                        user = arg[0]
                        reason = ' '.join(arg[1:])[:40].strip()
                        found, victim, msg = self.player_found(user)
                        if not found:
                            self.game.rcon_tell(sar['player_num'], msg)
                        else:
                            warn_delay = 15
                            if victim.get_admin_role() >= self.game.players[sar['player_num']].get_admin_role():
                                self.game.rcon_tell(sar['player_num'], "You cannot warn an admin")
                            elif victim.get_last_warn_time() + warn_delay > time.time():
                                self.game.rcon_tell(sar['player_num'], "Only one warning per %d seconds can be issued" % warn_delay)
                            else:
                                show_alert = False
                                ban_duration = 0
                                if victim.get_warning() > 2:
                                    self.game.kick_player(victim.get_player_num(), reason='too many warnings')
                                    msg = "^2%s ^7was kicked, too many warnings" % victim.get_name()
                                else:
                                    victim.add_warning()
                                    msg = "^1WARNING ^7[^3%d^7]: ^2%s^7:" % (victim.get_warning(), victim.get_name())
                                    if reason in reason_dict:
                                        msg = "%s %s" % (msg, reason_dict[reason])
                                        if reason == 'tk' and victim.get_warning() > 1:
                                            ban_duration = victim.add_ban_point('tk, ban by %s' % self.game.players[sar['player_num']].get_name(), 600)
                                        elif reason == 'lang' and victim.get_warning() > 1:
                                            ban_duration = victim.add_ban_point('lang', 300)
                                        elif reason == 'spam' and victim.get_warning() > 1:
                                            ban_duration = victim.add_ban_point('spam', 300)
                                        elif reason == 'racism' and victim.get_warning() > 1:
                                            ban_duration = victim.add_ban_point('racism', 300)
                                    else:
                                        msg = "%s %s" % (msg, reason)
                                    # ban player if needed
                                    if ban_duration > 0:
                                        msg = "^2%s ^7banned for ^1%d minutes ^7for too many warnings" % (victim.get_name(), ban_duration)
                                        self.game.kick_player(victim.get_player_num(), reason='too many warnings')
                                    # show alert message for player with 3 warnings
                                    elif victim.get_warning() == 3:
                                        show_alert = True
                                self.game.rcon_say(msg)
                                if show_alert:
                                    self.game.rcon_say("^1ALERT: ^2%s ^7auto-kick from warnings if not cleared" % victim.get_name())
                    else:
                        self.game.rcon_tell(sar['player_num'], "^7You need to enter a reason: ^3!warn <name> <reason>")
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !warn <name> <reason>")

## admin level 40
            # admins - list all the online admins
            elif (sar['command'] == '!admins' or sar['command'] == '@admins') and self.game.players[sar['player_num']].get_admin_role() >= 40:
                msg = "^7Admins online: %s" % ", ".join(["^3%s [^2%d^3]" % (player.get_name(), player.get_admin_role()) for player in self.game.players.itervalues() if player.get_admin_role() >= 20])
                self.tell_say_message(sar, msg)

            # aliases - list the aliases of the player
            elif (sar['command'] == '!aliases' or sar['command'] == '@aliases' or sar['command'] == '!alias' or sar['command'] == '@alias') and self.game.players[sar['player_num']].get_admin_role() >= 40:
                if line.split(sar['command'])[1]:
                    user = line.split(sar['command'])[1].strip()
                    found, victim, msg = self.player_found(user)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        msg = "^7Aliases of ^5%s: ^3%s" % (victim.get_name(), victim.get_aliases())
                        self.tell_say_message(sar, msg)
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !alias <name>")

            # bigtext - display big message on screen
            elif sar['command'] == '!bigtext' and self.game.players[sar['player_num']].get_admin_role() >= 40:
                if line.split(sar['command'])[1]:
                    self.game.rcon_bigtext("%s" % line.split(sar['command'])[1].strip())
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !bigtext <text>")

            # say - say a message to all players
            elif sar['command'] == '!say' and self.game.players[sar['player_num']].get_admin_role() >= 40:
                if line.split(sar['command'])[1]:
                    self.game.rcon_say("^4%s: ^7%s" % (self.game.players[sar['player_num']].get_name(), line.split(sar['command'])[1].strip()))
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !say <text>")

            # force - force a player to the given team
            elif sar['command'] == '!force' and self.game.players[sar['player_num']].get_admin_role() >= 40:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip().split(' ')
                    if len(arg) > 1:
                        user = arg[0]
                        team = arg[1]
                        lock = False
                        if len(arg) > 2:
                            lock = True if arg[2] == 'lock' else False
                        team_dict = {'red': 'red', 'r': 'red', 're': 'red',
                                     'blue': 'blue', 'b': 'blue', 'bl': 'blue', 'blu': 'blue',
                                     'spec': 'spectator', 'spectator': 'spectator', 's': 'spectator', 'sp': 'spectator', 'spe': 'spectator',
                                     'green': 'green'}
                        found, victim, msg = self.player_found(user)
                        if not found:
                            self.game.rcon_tell(sar['player_num'], msg)
                        else:
                            if team in team_dict:
                                victim_player_num = victim.get_player_num()
                                self.game.rcon_forceteam(victim_player_num, team_dict[team])
                                self.game.rcon_tell(victim_player_num, "^3You are forced to: ^7%s" % team_dict[team])
                                # set team lock if defined
                                if lock:
                                    victim.set_team_lock(team_dict[team])
                                else:
                                    victim.set_team_lock(None)
                            else:
                                self.game.rcon_tell(sar['player_num'], "^7Usage: !force <name> <blue/red/spec> [<lock>]")
                    else:
                        self.game.rcon_tell(sar['player_num'], "^7Usage: !force <name> <blue/red/spec> [<lock>]")
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !force <name> <blue/red/spec> [<lock>]")

            # nuke - nuke a player
            elif sar['command'] == '!nuke' and self.game.players[sar['player_num']].get_admin_role() >= 40:
                if line.split(sar['command'])[1]:
                    user = line.split(sar['command'])[1].strip()
                    found, victim, msg = self.player_found(user)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        if victim.get_admin_role() >= self.game.players[sar['player_num']].get_admin_role():
                            self.game.rcon_tell(sar['player_num'], "Insufficient privileges to nuke an admin")
                        else:
                            self.game.send_rcon("nuke %d" % victim.get_player_num())
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !nuke <name>")

            # kick - kick a player
            elif (sar['command'] == '!kick' or sar['command'] == '!k') and self.game.players[sar['player_num']].get_admin_role() >= 40:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip().split(' ')
                    if self.game.players[sar['player_num']].get_admin_role() >= 80 and len(arg) == 1:
                        user = arg[0]
                        reason = '.'
                    elif len(arg) > 1:
                        user = arg[0]
                        reason = ' '.join(arg[1:])[:40].strip()
                    else:
                        user = reason = None
                    if user and reason:
                        found, victim, msg = self.player_found(user)
                        if not found:
                            self.game.rcon_tell(sar['player_num'], msg)
                        else:
                            if victim.get_admin_role() >= self.game.players[sar['player_num']].get_admin_role():
                                self.game.rcon_tell(sar['player_num'], "Insufficient privileges to kick an admin")
                            else:
                                msg = "^2%s ^7was kicked by %s" % (victim.get_name(), self.game.players[sar['player_num']].get_name())
                                if reason in reason_dict:
                                    kick_reason = reason_dict[reason]
                                    msg = "%s: ^3%s" % (msg, kick_reason)
                                elif reason == '.':
                                    kick_reason = ''
                                else:
                                    kick_reason = reason
                                    msg = "%s: ^3%s" % (msg, kick_reason)
                                self.game.kick_player(victim.get_player_num(), reason=kick_reason)
                                self.game.rcon_say(msg)
                    else:
                        self.game.rcon_tell(sar['player_num'], "^7You need to enter a reason: ^3!kick <name> <reason>")
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !kick <name> <reason>")

            # warnclear - clear the user warnings
            elif (sar['command'] == '!warnclear' or sar['command'] == '!wc' or sar['command'] == '!wr') and self.game.players[sar['player_num']].get_admin_role() >= 40:
                if line.split(sar['command'])[1]:
                    user = line.split(sar['command'])[1].strip()
                    found, victim, msg = self.player_found(user)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        victim.clear_warning()
                        self.game.rcon_say("^1All warnings cleared for ^2%s" % victim.get_name())
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !warnclear <name>")

            # tempban - ban a player temporary for the given period (1 min to 24 hrs)
            elif (sar['command'] == '!tempban' or sar['command'] == '!tb') and self.game.players[sar['player_num']].get_admin_role() >= 40:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip().split(' ')
                    if len(arg) > 1:
                        user = arg[0]
                        duration, duration_output = self.convert_time(arg[1])
                        reason = ' '.join(arg[2:])[:40].strip() if len(arg) >= 2 else ''
                        kick_reason = reason_dict[reason] if reason in reason_dict else reason
                        found, victim, msg = self.player_found(user)
                        if not found:
                            self.game.rcon_tell(sar['player_num'], msg)
                        else:
                            if victim.get_admin_role() >= self.game.players[sar['player_num']].get_admin_role():
                                self.game.rcon_tell(sar['player_num'], "Insufficient privileges to ban an admin")
                            else:
                                if victim.ban(duration=duration, reason=reason, admin=self.game.players[sar['player_num']].get_name()):
                                    msg = "^2%s ^1banned ^7for ^3%s ^7by %s" % (victim.get_name(), duration_output, self.game.players[sar['player_num']].get_name())
                                    if kick_reason:
                                        msg = "%s: ^3%s" % (msg, kick_reason)
                                    self.game.rcon_say(msg)
                                else:
                                    self.game.rcon_tell(sar['player_num'], "^7This player has already a longer ban")
                                self.game.kick_player(player_num=victim.get_player_num(), reason=kick_reason)
                    else:
                        self.game.rcon_tell(sar['player_num'], "^7You need to enter a duration: ^3!tempban <name> <duration> [<reason>]")
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !tempban <name> <duration> [<reason>]")

## full admin level 60
            # scream - scream a message in different colors to all players
            elif sar['command'] == '!scream' and self.game.players[sar['player_num']].get_admin_role() >= 60:
                if line.split(sar['command'])[1]:
                    self.game.rcon_say("^1%s" % line.split(sar['command'])[1].strip())
                    self.game.rcon_say("^2%s" % line.split(sar['command'])[1].strip())
                    self.game.rcon_say("^3%s" % line.split(sar['command'])[1].strip())
                    self.game.rcon_say("^5%s" % line.split(sar['command'])[1].strip())
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !scream <text>")

            # slap - slap a player (a number of times); (1-10 times)
            elif sar['command'] == '!slap' and self.game.players[sar['player_num']].get_admin_role() >= 60:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip().split(' ')
                    if len(arg) > 1:
                        user = arg[0]
                        number = arg[1]
                        if not number.isdigit():
                            number = 1
                        else:
                            number = int(number)
                        if number > 10:
                            number = 10
                    else:
                        user = arg[0]
                        number = 1
                    found, victim, msg = self.player_found(user)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        if victim.get_admin_role() >= self.game.players[sar['player_num']].get_admin_role():
                            self.game.rcon_tell(sar['player_num'], "Insufficient privileges to slap an admin")
                        else:
                            for _ in xrange(0, number):
                                self.game.send_rcon("slap %d" % victim.get_player_num())
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !slap <name> [<amount>]")

            # swap - swap teams for player 1 and 2 (if in different teams)
            elif sar['command'] == '!swap' and self.game.players[sar['player_num']].get_admin_role() >= 60:
                if not self.ffa_lms_gametype:
                    if line.split(sar['command'])[1]:
                        arg = line.split(sar['command'])[1].strip().split(' ')
                        if len(arg) > 1:
                            player1 = arg[0]
                            player2 = arg[1]
                            found1, victim1, _ = self.player_found(player1)
                            found2, victim2, _ = self.player_found(player2)
                            if not found1 or not found2:
                                self.game.rcon_tell(sar['player_num'], 'Player not found')
                            else:
                                team1 = victim1.get_team()
                                team2 = victim2.get_team()
                                if team1 == team2:
                                    self.game.rcon_tell(sar['player_num'], "^7Cannot swap, both players are in the same team")
                                else:
                                    game_data = self.game.get_gamestats()
                                    # remove team lock
                                    victim1.set_team_lock(None)
                                    victim2.set_team_lock(None)
                                    if game_data[Player.teams[team1]] < game_data[Player.teams[team2]]:
                                        self.game.rcon_forceteam(victim2.get_player_num(), Player.teams[team1])
                                        self.game.rcon_forceteam(victim1.get_player_num(), Player.teams[team2])
                                    else:
                                        self.game.rcon_forceteam(victim1.get_player_num(), Player.teams[team2])
                                        self.game.rcon_forceteam(victim2.get_player_num(), Player.teams[team1])
                                    self.game.rcon_say('^7Swapped player ^3%s ^7with ^3%s' % (victim1.get_name(), victim2.get_name()))
                        else:
                            self.game.rcon_tell(sar['player_num'], "^7Usage: !swap <name1> <name2>")
                    else:
                        self.game.rcon_tell(sar['player_num'], "^7Usage: !swap <name1> <name2>")
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Command is disabled for this game mode")

            # version - display the version of the bot
            elif sar['command'] == '!version' and self.game.players[sar['player_num']].get_admin_role() >= 60:
                self.game.rcon_tell(sar['player_num'], "^7Spunky Bot ^2v%s" % __version__)
                try:
                    get_latest = urllib2.urlopen('%s/version.txt' % self.base_url).read().strip()
                except urllib2.URLError:
                    get_latest = __version__
                if __version__ < get_latest:
                    self.game.rcon_tell(sar['player_num'], "^7A newer release ^6%s ^7is available, check ^3www.spunkybot.de" % get_latest)

            # veto - stop voting process
            elif sar['command'] == '!veto' and self.game.players[sar['player_num']].get_admin_role() >= 60:
                self.game.send_rcon('veto')

            # ci - kick player with connection interrupted
            elif sar['command'] == '!ci' and self.game.players[sar['player_num']].get_admin_role() >= 60:
                if line.split(sar['command'])[1]:
                    user = line.split(sar['command'])[1].strip()
                    player_ping = 0
                    found, victim, msg = self.player_found(user)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        # update rcon status
                        self.game.get_rcon_handle().quake.rcon_update()
                        for player in self.game.get_rcon_handle().quake.players:
                            if victim.get_player_num() == player.num:
                                player_ping = player.ping
                        if player_ping == 999:
                            self.game.kick_player(victim.get_player_num(), reason='connection interrupted, try to reconnect')
                            self.game.rcon_say("^2%s ^7was kicked by %s: ^4connection interrupted" % (victim.get_name(), self.game.players[sar['player_num']].get_name()))
                        else:
                            self.game.rcon_tell(sar['player_num'], "%s has no connection interrupted" % victim.get_name())
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !ci <name>")

            # ban - ban a player for 7 days
            elif (sar['command'] == '!ban' or sar['command'] == '!b') and self.game.players[sar['player_num']].get_admin_role() >= 60:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip().split(' ')
                    if len(arg) > 1:
                        user = arg[0]
                        reason = ' '.join(arg[1:])[:40].strip()
                        found, victim, msg = self.player_found(user)
                        kick_reason = reason_dict[reason] if reason in reason_dict else reason
                        if not found:
                            self.game.rcon_tell(sar['player_num'], msg)
                        else:
                            if victim.get_admin_role() >= self.game.players[sar['player_num']].get_admin_role():
                                self.game.rcon_tell(sar['player_num'], "Insufficient privileges to ban an admin")
                            else:
                                # ban for 7 days
                                if victim.ban(duration=604800, reason=reason, admin=self.game.players[sar['player_num']].get_name()):
                                    self.game.rcon_say("^2%s ^1banned ^7for ^37 days ^7by %s: ^3%s" % (victim.get_name(), self.game.players[sar['player_num']].get_name(), kick_reason))
                                else:
                                    self.game.rcon_tell(sar['player_num'], "^7This player has already a longer ban")
                                self.game.kick_player(player_num=victim.get_player_num(), reason=kick_reason)
                    else:
                        self.game.rcon_tell(sar['player_num'], "^7You need to enter a reason: ^3!ban <name> <reason>")
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !ban <name> <reason>")

            # baninfo - display active bans of a player
            elif (sar['command'] == '!baninfo' or sar['command'] == '!bi') and self.game.players[sar['player_num']].get_admin_role() >= 60:
                if line.split(sar['command'])[1]:
                    user = line.split(sar['command'])[1].strip()
                    found, victim, msg = self.player_found(user)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                        guid = victim.get_guid()
                        values = (timestamp, guid)
                        curs.execute("SELECT `expires` FROM `ban_list` WHERE `expires` > ? AND `guid` = ?", values)
                        result = curs.fetchone()
                        if result:
                            self.game.rcon_tell(sar['player_num'], "%s ^7has an active ban until [^1%s^7]" % (victim.get_name(), str(result[0])))
                        else:
                            self.game.rcon_tell(sar['player_num'], "%s ^7has no active ban" % victim.get_name())
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !baninfo <name>")

## senior admin level 80
            # kiss - clear all player warnings
            elif (sar['command'] == '!kiss' or sar['command'] == '!clear') and self.game.players[sar['player_num']].get_admin_role() >= 80:
                for player in self.game.players.itervalues():
                    player.clear_warning()
                self.game.rcon_say("^1All player warnings cleared")

            # map - load given map
            elif sar['command'] == '!map' and self.game.players[sar['player_num']].get_admin_role() >= 80:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip()
                    found, newmap, msg = self.map_found(arg)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        self.game.send_rcon('g_nextmap %s' % newmap)
                        self.game.next_mapname = newmap
                        self.game.rcon_tell(sar['player_num'], "^7Changing Map to: ^3%s" % newmap)
                        self.game.send_rcon('cyclemap')
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !map <ut4_name>")

            # maps - display all available maps
            elif (sar['command'] == '!maps' or sar['command'] == '@maps') and self.game.players[sar['player_num']].get_admin_role() >= 80:
                msg = "^7Available Maps: ^3%s" % ', '.join(self.game.get_all_maps())
                self.tell_say_message(sar, msg)

            # maprestart - restart the map
            elif sar['command'] == '!maprestart' and self.game.players[sar['player_num']].get_admin_role() >= 80:
                self.game.send_rcon('restart')
                for player in self.game.players.itervalues():
                    # reset player statistics
                    player.reset()

            # moon - activate Moon mode (low gravity)
            elif sar['command'] == '!moon' and self.game.players[sar['player_num']].get_admin_role() >= 80:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip()
                    if arg == "off":
                        self.game.send_rcon('g_gravity 800')
                        self.game.rcon_tell(sar['player_num'], "^7Moon mode: ^1Off")
                    elif arg == "on":
                        self.game.send_rcon('g_gravity 100')
                        self.game.rcon_tell(sar['player_num'], "^7Moon mode: ^2On")
                    else:
                        self.game.rcon_tell(sar['player_num'], "^7Usage: !moon <on/off>")
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !moon <on/off>")

            # cyclemap - start next map in rotation
            elif sar['command'] == '!cyclemap' and self.game.players[sar['player_num']].get_admin_role() >= 80:
                self.game.send_rcon('cyclemap')

            # setnextmap - set the given map as nextmap
            elif sar['command'] == '!setnextmap' and self.game.players[sar['player_num']].get_admin_role() >= 80:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip()
                    found, nextmap, msg = self.map_found(arg)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        self.game.send_rcon('g_nextmap %s' % nextmap)
                        self.game.next_mapname = nextmap
                        self.game.rcon_tell(sar['player_num'], "^7Next Map set to: ^3%s" % nextmap)
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !setnextmap <ut4_name>")

            # kill - kill a player
            elif sar['command'] == '!kill' and self.urt42_modversion and self.game.players[sar['player_num']].get_admin_role() >= 80:
                if line.split(sar['command'])[1]:
                    user = line.split(sar['command'])[1].strip()
                    found, victim, msg = self.player_found(user)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        if victim.get_admin_role() >= self.game.players[sar['player_num']].get_admin_role():
                            self.game.rcon_tell(sar['player_num'], "Insufficient privileges to kill an admin")
                        else:
                            self.game.send_rcon("smite %d" % victim.get_player_num())
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !kill <name>")

            # lookup - search for player in database
            elif (sar['command'] == '!lookup' or sar['command'] == '!l') and self.game.players[sar['player_num']].get_admin_role() >= 80:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip()
                    search = '%' + arg + '%'
                    lookup = (search,)
                    curs.execute("SELECT * FROM `player` WHERE `name` like ? ORDER BY `time_joined` DESC LIMIT 8", lookup)
                    result = curs.fetchall()
                    for row in result:
                        self.game.rcon_tell(sar['player_num'], "^7[^2@%s^7] %s ^7[^1%s^7]" % (str(row[0]), str(row[2]), str(row[4])), False)  # 0=ID, 1=GUID, 2=Name, 3=IP, 4=Date
                    if not result:
                        self.game.rcon_tell(sar['player_num'], "No Player found matching %s" % arg)
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !lookup <name>")

            # permban - ban a player permanent
            elif (sar['command'] == '!permban' or sar['command'] == '!pb') and self.game.players[sar['player_num']].get_admin_role() >= 80:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip().split(' ')
                    if len(arg) > 1:
                        user = arg[0]
                        reason = ' '.join(arg[1:])[:40].strip()
                        found, victim, msg = self.player_found(user)
                        if not found:
                            self.game.rcon_tell(sar['player_num'], msg)
                        else:
                            if victim.get_admin_role() >= self.game.players[sar['player_num']].get_admin_role():
                                self.game.rcon_tell(sar['player_num'], "Insufficient privileges to ban an admin")
                            else:
                                # ban for 20 years
                                victim.ban(duration=630720000, reason=reason, admin=self.game.players[sar['player_num']].get_name())
                                self.game.rcon_say("^2%s ^1banned permanently ^7by %s: ^4%s" % (victim.get_name(), self.game.players[sar['player_num']].get_name(), reason))
                                self.game.kick_player(victim.get_player_num())
                                # add IP address to bot-banlist.txt
                                banlist = open('./bot-banlist.txt', 'a+')
                                banlist.write("%s:-1   // %s    banned on  %s, reason : %s\n" % (victim.get_ip_address(), victim.get_name(), time.strftime("%d/%m/%Y (%H:%M)", time.localtime(time.time())), reason))
                                banlist.close()
                    else:
                        self.game.rcon_tell(sar['player_num'], "^7You need to enter a reason: ^3!permban <name> <reason>")
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !permban <name> <reason>")

            # putgroup - add a client to a group
            elif sar['command'] == '!putgroup' and self.game.players[sar['player_num']].get_admin_role() >= 80:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip().split(' ')
                    if len(arg) > 1:
                        user = arg[0]
                        right = arg[1]
                        found, victim, msg = self.player_found(user)
                        if not found:
                            self.game.rcon_tell(sar['player_num'], msg)
                        else:
                            if victim.get_registered_user():
                                new_role = victim.get_admin_role()
                            else:
                                # register new user in DB and set role to 1
                                victim.register_user_db(role=1)
                                new_role = 1

                            if right == "user" and victim.get_admin_role() < 80:
                                self.game.rcon_tell(sar['player_num'], "%s put in group User" % victim.get_name())
                                new_role = 1
                            elif right == "regular" and victim.get_admin_role() < 80:
                                self.game.rcon_tell(sar['player_num'], "%s put in group Regular" % victim.get_name())
                                new_role = 2
                            elif (right == "mod" or right == "moderator") and victim.get_admin_role() < 80:
                                self.game.rcon_tell(sar['player_num'], "%s added as Moderator" % victim.get_name())
                                new_role = 20
                            elif right == "admin" and victim.get_admin_role() < 80:
                                self.game.rcon_tell(sar['player_num'], "%s added as Admin" % victim.get_name())
                                new_role = 40
                            elif right == "fulladmin" and victim.get_admin_role() < 80:
                                self.game.rcon_tell(sar['player_num'], "%s added as Full Admin" % victim.get_name())
                                new_role = 60
                            # Note: senioradmin level can only be set by head admin
                            elif right == "senioradmin" and self.game.players[sar['player_num']].get_admin_role() == 100 and victim.get_player_num() != sar['player_num']:
                                self.game.rcon_tell(sar['player_num'], "%s added as ^6Senior Admin" % victim.get_name())
                                new_role = 80
                            else:
                                self.game.rcon_tell(sar['player_num'], "Sorry, you cannot put %s in group <%s>" % (victim.get_name(), right))
                            victim.update_db_admin_role(role=new_role)
                    else:
                        self.game.rcon_tell(sar['player_num'], "^7Usage: !putgroup <name> <group>")
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !putgroup <name> <group>")

            # banlist - display the last 10 entries of the banlist
            elif sar['command'] == '!banlist' and self.game.players[sar['player_num']].get_admin_role() >= 80:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                values = (timestamp,)
                curs.execute("SELECT * FROM `ban_list` WHERE `expires` > ? ORDER BY `timestamp` DESC LIMIT 10", values)
                result = curs.fetchall()
                if len(result) > 10:
                    limit = 10
                elif len(result) == 0:
                    limit = 0
                else:
                    limit = len(result)
                banlist = ['^7[^2@%s^7] %s' % (result[item][0], result[item][2]) for item in xrange(limit)]  # 0=ID,2=Name
                msg = 'Currently no one is banned' if not banlist else str(", ".join(banlist))
                self.game.rcon_tell(sar['player_num'], "^7Banlist: %s" % msg)

            # unban - unban a player from the database via ID
            elif sar['command'] == '!unban' and self.game.players[sar['player_num']].get_admin_role() >= 80:
                if line.split(sar['command'])[1]:
                    arg = line.split(sar['command'])[1].strip().lstrip('@')
                    if arg.isdigit():
                        values = (int(arg),)
                        curs.execute("SELECT `guid`,`name`,`ip_address` FROM `ban_list` WHERE `id` = ?", values)
                        result = curs.fetchone()
                        if result:
                            guid = result[0]
                            name = str(result[1])
                            ip_addr = str(result[2])
                            curs.execute("DELETE FROM `ban_list` WHERE `id` = ?", values)
                            conn.commit()
                            self.game.rcon_tell(sar['player_num'], "^7Player ^2%s ^7unbanned" % name)
                            values = (guid, ip_addr)
                            curs.execute("DELETE FROM `ban_list` WHERE `guid` = ? OR ip_address = ?", values)
                            conn.commit()
                            self.game.rcon_tell(sar['player_num'], "^7Try to remove duplicates of [^1%s^7]" % ip_addr)
                        else:
                            self.game.rcon_tell(sar['player_num'], "^7Invalid ID, no Player found")
                    else:
                        self.game.rcon_tell(sar['player_num'], "^7Usage: !unban <@ID>")
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !unban <@ID>")

## head admin level 100
            # ungroup - remove the admin level from a player
            elif sar['command'] == '!ungroup' and self.game.players[sar['player_num']].get_admin_role() == 100:
                if line.split(sar['command'])[1]:
                    user = line.split(sar['command'])[1].strip()
                    found, victim, msg = self.player_found(user)
                    if not found:
                        self.game.rcon_tell(sar['player_num'], msg)
                    else:
                        if 1 < victim.get_admin_role() < 100:
                            self.game.rcon_tell(sar['player_num'], "%s put in group User" % victim.get_name())
                            victim.update_db_admin_role(role=1)
                        else:
                            self.game.rcon_tell(sar['player_num'], "Sorry, you cannot put %s in group User" % victim.get_name())
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Usage: !ungroup <name>")

## iamgod
            # iamgod - register user as Head Admin
            elif sar['command'] == '!iamgod':
                if self.iamgod:
                    if not self.game.players[sar['player_num']].get_registered_user():
                        # register new user in DB and set admin role to 100
                        self.game.players[sar['player_num']].register_user_db(role=100)
                    else:
                        self.game.players[sar['player_num']].update_db_admin_role(role=100)
                    self.iamgod = False
                    self.game.rcon_tell(sar['player_num'], "^7You are registered as ^6Head Admin")

## unknown command
            elif sar['command'].startswith('!') and self.game.players[sar['player_num']].get_admin_role() > 20:
                if sar['command'].lstrip('!') in self.senioradmin_cmds:
                    self.game.rcon_tell(sar['player_num'], "^7Insufficient privileges to use command ^3%s" % sar['command'])
                else:
                    self.game.rcon_tell(sar['player_num'], "^7Unknown command ^3%s" % sar['command'])

    def tell_say_message(self, sar, msg):
        """
        display message in private or global chat
        """
        if sar['command'].startswith('@'):
            self.game.rcon_say(msg)
        else:
            self.game.rcon_tell(sar['player_num'], msg)

    def convert_time(self, time_string):
        """
        convert time string in duration and time unit
        """
        if time_string.endswith('h'):
            duration_string = time_string.rstrip('h')
            duration = int(duration_string) * 3600 if duration_string.isdigit() else 3600
            duration_output = "1 hour" if duration == 3600 else "%s hours" % duration_string
        elif time_string.endswith('m'):
            duration_string = time_string.rstrip('m')
            duration = int(duration_string) * 60 if duration_string.isdigit() else 60
            duration_output = "1 minute" if duration == 60 else "%s minutes" % duration_string
            if duration > 3600:
                calc = int(round(duration / 3600))
                duration_output = "1 hour" if calc == 1 else "%s hours" % calc
        else:
            duration = 3600
            duration_output = "1 hour"
        # minimum ban duration = 1 hour
        if duration == 0:
            duration = 3600
            duration_output = "1 hour"
        # limit to max duration = 24 hours
        elif duration > 86400:
            duration = 86400
            duration_output = "24 hours"
        return duration, duration_output

    def handle_flag(self, line):
        """
        handle flag
        """
        tmp = line.split(" ")
        player_num = int(tmp[0].strip())
        action = tmp[1].strip()
        with self.players_lock:
            player = self.game.players[player_num]
            if action == '1:':
                player.return_flag()
                self.debug("Player %d returned the flag" % player_num)
            elif action == '2:':
                player.capture_flag()
                self.debug("Player %d captured the flag" % player_num)

    def handle_bomb(self, line):
        """
        handle bomb
        """
        if "Bombholder" in line:
            tmp = line.split("is")
        else:
            tmp = line.split("by")
        action = tmp[0].strip()
        player_num = int(tmp[1].rstrip('!').strip())
        with self.players_lock:
            player = self.game.players[player_num]
            if action == 'Bomb was defused':
                player.defused_bomb()
                self.debug("Player %d defused the bomb" % player_num)
                self.handle_teams_ts_mode()
            elif action == 'Bomb was planted':
                player.planted_bomb()
                self.debug("Player %d planted the bomb" % player_num)
            elif action == 'Bomb was tossed':
                player.bomb_tossed()
            elif action == 'Bomb has been collected':
                player.is_bombholder()
            elif action == 'Bombholder':
                player.is_bombholder()

    def handle_teams_ts_mode(self):
        """
        handle team balance in Team Survivor mode
        """
        self.autobalancer()
        if self.ts_do_team_balance:
            self.allow_cmd_teams = True
            self.handle_team_balance()
            if self.allow_cmd_teams_round_end:
                self.allow_cmd_teams = False

    def handle_team_balance(self):
        """
        balance teams if needed
        """
        with self.players_lock:
            game_data = self.game.get_gamestats()
            if (abs(game_data[Player.teams[1]] - game_data[Player.teams[2]])) > 1:
                if self.allow_cmd_teams:
                    self.game.balance_teams(game_data)
                    self.ts_do_team_balance = False
                    self.debug("Balance teams by user request")
                else:
                    if self.ts_gametype or self.bomb_gametype or self.freeze_gametype:
                        self.ts_do_team_balance = True
                        self.game.rcon_say("^7Teams will be balanced at the end of the round!")
            else:
                self.game.rcon_say("^7Teams are already balanced")
                self.ts_do_team_balance = False

    def autobalancer(self):
        """
        auto balance teams at the end of the round if needed
        """
        if self.teams_autobalancer:
            with self.players_lock:
                game_data = self.game.get_gamestats()
                if (abs(game_data[Player.teams[1]] - game_data[Player.teams[2]])) > 1:
                    self.game.balance_teams(game_data)
                    self.debug("Autobalancer performed team balance")
                self.ts_do_team_balance = False

    def handle_freeze(self, line):
        """
        handle freeze
        """
        info = line.split(":", 1)[0].split(" ")
        player_num = int(info[0])
        with self.players_lock:
            self.game.players[player_num].freeze()

    def handle_thawout(self, line):
        """
        handle thaw out
        """
        info = line.split(":", 1)[0].split(" ")
        player_num = int(info[0])
        with self.players_lock:
            self.game.players[player_num].thawout()

    def handle_awards(self):
        """
        display awards and personal stats at the end of the round
        """
        most_kills = 0
        most_flags = 0
        most_streak = 0
        most_hs = 0
        most_frozen = 0
        most_thawouts = 0
        most_defused = 0
        most_planted = 0
        flagrunner = ""
        serialkiller = ""
        streaker = ""
        freezer = ""
        thawouter = ""
        headshooter = ""
        defused_by = ""
        planted_by = ""
        msg = []
        append = msg.append
        with self.players_lock:
            for player in self.game.players.itervalues():
                if player.get_flags_captured() > most_flags:
                    most_flags = player.get_flags_captured()
                    flagrunner = player.get_name()
                if player.get_kills() > most_kills and player.get_player_num() != 1022:
                    most_kills = player.get_kills()
                    serialkiller = player.get_name()
                if player.get_max_kill_streak() > most_streak and player.get_player_num() != 1022:
                    most_streak = player.get_max_kill_streak()
                    streaker = player.get_name()
                if player.get_headshots() > most_hs:
                    most_hs = player.get_headshots()
                    headshooter = player.get_name()
                if player.get_freeze() > most_frozen:
                    most_frozen = player.get_freeze()
                    freezer = player.get_name()
                if player.get_thawout() > most_thawouts:
                    most_thawouts = player.get_thawout()
                    thawouter = player.get_name()
                if player.get_defused_bomb() > most_defused:
                    most_defused = player.get_defused_bomb()
                    defused_by = player.get_name()
                if player.get_planted_bomb() > most_planted:
                    most_planted = player.get_planted_bomb()
                    planted_by = player.get_name()
                # display personal stats at the end of the round, stats for players in spec will not be displayed
                if player.get_team() != 3:
                    if self.freeze_gametype:
                        self.game.rcon_tell(player.get_player_num(), "^7Stats %s: ^7F ^2%d ^7T ^3%d ^7HS ^1%d ^7TK ^1%d" % (player.get_name(), player.get_freeze(), player.get_thawout(), player.get_headshots(), player.get_team_kill_count()))
                    else:
                        self.game.rcon_tell(player.get_player_num(), "^7Stats %s: ^7K ^2%d ^7D ^3%d ^7HS ^1%d ^7TK ^1%d" % (player.get_name(), player.get_kills(), player.get_deaths(), player.get_headshots(), player.get_team_kill_count()))

            # display Awards
            if most_flags > 1:
                append("^7%s: ^2%d ^4caps" % (flagrunner, most_flags))
            if most_planted > 1:
                append("^7%s: ^2%d ^5planted" % (planted_by, most_planted))
            if most_defused > 1:
                append("^7%s: ^2%d ^4defused" % (defused_by, most_defused))
            if most_frozen > 1:
                append("^7%s: ^2%d ^3freezes" % (freezer, most_frozen))
            if most_thawouts > 1:
                append("^7%s: ^2%d ^4thaws" % (thawouter, most_thawouts))
            if most_kills > 1:
                append("^7%s: ^2%d ^3kills" % (serialkiller, most_kills))
            if most_streak > 1:
                append("^7%s: ^2%d ^6streaks" % (streaker, most_streak))
            if most_hs > 1:
                append("^7%s: ^2%d ^1heads" % (headshooter, most_hs))
            if msg:
                self.game.rcon_say("^1AWARDS: %s" % " ^7- ".join(msg))

    def debug(self, msg):
        """
        print debug messages
        """
        if self.verbose:
            print msg


### CLASS Player ###
class Player(object):
    """
    Player class
    """
    teams = {0: "green", 1: "red", 2: "blue", 3: "spectator"}
    roles = {0: "Guest", 1: "User", 2: "Regular", 20: "Moderator", 40: "Admin", 60: "Full Admin", 80: "Senior Admin", 100: "Head Admin"}

    def __init__(self, player_num, ip_address, guid, name):
        """
        create a new instance of Player
        """
        self.player_num = player_num
        self.guid = guid
        self.name = "".join(name.split())
        self.player_id = 0
        self.aliases = []
        self.registered_user = False
        self.num_played = 0
        self.last_visit = 0
        self.admin_role = 0
        self.kills = 0
        self.froze = 0
        self.thawouts = 0
        self.db_kills = 0
        self.killing_streak = 0
        self.max_kill_streak = 0
        self.db_killing_streak = 0
        self.deaths = 0
        self.db_deaths = 0
        self.db_suicide = 0
        self.head_shots = 0
        self.db_head_shots = 0
        self.all_hits = 0
        self.tk_count = 0
        self.db_tk_count = 0
        self.db_team_death = 0
        self.tk_victim_names = []
        self.tk_killer_names = []
        self.ping_value = 0
        self.high_ping_count = 0
        self.spec_warn_count = 0
        self.warn_counter = 0
        self.last_warn_time = 0
        self.flags_captured = 0
        self.flags_returned = 0
        self.bombholder = False
        self.bomb_carrier_killed = 0
        self.killed_with_bomb = 0
        self.bomb_planted = 0
        self.bomb_defused = 0
        self.address = ip_address
        self.team = 3
        self.team_lock = None
        self.time_joined = time.time()
        self.welcome_msg = True
        self.country = None
        self.ban_id = 0

        self.prettyname = self.name
        # remove color characters from name
        for item in xrange(10):
            self.prettyname = self.prettyname.replace('^%d' % item, '')

        # GeoIP lookup
        info = GEOIP.lookup(ip_address)
        if info.country:
            self.country = info.country_name

        # check ban_list
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.time_joined))
        values = (self.guid, now)
        curs.execute("SELECT `id` FROM `ban_list` WHERE `guid` = ? AND `expires` > ?", values)
        result = curs.fetchone()
        if result:
            self.ban_id = result[0]
        else:
            values = (self.address, now)
            curs.execute("SELECT `id` FROM `ban_list` WHERE `ip_address` = ? AND `expires` > ?", values)
            result = curs.fetchone()
            if result:
                self.ban_id = result[0]

    def ban(self, duration=900, reason='tk', admin=None):
        if admin:
            reason = "%s, ban by %s" % (reason, admin)
        unix_expiration = duration + time.time()
        expire_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(unix_expiration))
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        values = (self.guid,)
        curs.execute("SELECT `expires` FROM `ban_list` WHERE `guid` = ?", values)
        result = curs.fetchone()
        if result:
            if result[0] < expire_date:
                values = (self.address, expire_date, self.guid)
                curs.execute("UPDATE `ban_list` SET `ip_address` = ?,`expires` = ? WHERE `guid` = ?", values)
                conn.commit()
                ban_status = True
            else:
                values = (self.address, self.guid)
                curs.execute("UPDATE `ban_list` SET `ip_address` = ? WHERE `guid` = ?", values)
                conn.commit()
                ban_status = False
        else:
            values = (self.player_id, self.guid, self.prettyname, self.address, expire_date, timestamp, reason)
            curs.execute("INSERT INTO `ban_list` (`id`,`guid`,`name`,`ip_address`,`expires`,`timestamp`,`reason`) VALUES (?,?,?,?,?,?,?)", values)
            conn.commit()
            ban_status = True
        return ban_status

    def add_ban_point(self, point_type, duration):
        unix_expiration = duration + time.time()
        expire_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(unix_expiration))
        values = (self.guid, point_type, expire_date)
        # add ban_point to database
        curs.execute("INSERT INTO `ban_points` (`guid`,`point_type`,`expires`) VALUES (?,?,?)", values)
        conn.commit()
        # check amount of ban_points
        values = (self.guid, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        curs.execute("SELECT COUNT(*) FROM `ban_points` WHERE `guid` = ? AND `expires` > ?", values)
        # ban player when he gets more than 1 ban_point
        if curs.fetchone()[0] > 1:
            # ban duration multiplied by 3
            ban_duration = duration * 3
            self.ban(duration=ban_duration, reason=point_type)
            ban_period = ban_duration / 60
        else:
            ban_period = 0
        return ban_period

    def reset(self):
        self.kills = 0
        self.froze = 0
        self.thawouts = 0
        self.killing_streak = 0
        self.max_kill_streak = 0
        self.deaths = 0
        self.head_shots = 0
        self.all_hits = 0
        self.tk_count = 0
        self.tk_victim_names = []
        self.tk_killer_names = []
        self.warn_counter = 0
        self.last_warn_time = 0
        self.flags_captured = 0
        self.flags_returned = 0
        self.bombholder = False
        self.bomb_carrier_killed = 0
        self.killed_with_bomb = 0
        self.bomb_planted = 0
        self.bomb_defused = 0
        self.team_lock = None

    def reset_flag_stats(self):
        self.flags_captured = 0
        self.flags_returned = 0

    def save_info(self):
        if self.registered_user:
            if self.db_deaths == 0:
                ratio = 1.0
            else:
                ratio = round(float(self.db_kills) / float(self.db_deaths), 2)
            values = (self.db_kills, self.db_deaths, self.db_head_shots, self.db_tk_count, self.db_team_death, self.db_killing_streak, self.db_suicide, ratio, self.guid)
            curs.execute("UPDATE `xlrstats` SET `kills` = ?,`deaths` = ?,`headshots` = ?,`team_kills` = ?,`team_death` = ?,`max_kill_streak` = ?,`suicides` = ?,`rounds` = `rounds` + 1,`ratio` = ? WHERE `guid` = ?", values)
            conn.commit()

    def check_database(self):
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        # check player table
        values = (self.guid,)
        curs.execute("SELECT COUNT(*) FROM `player` WHERE `guid` = ?", values)
        if curs.fetchone()[0] == 0:
            # add new player to database
            values = (self.guid, self.prettyname, self.address, now, self.prettyname)
            curs.execute("INSERT INTO `player` (`guid`,`name`,`ip_address`,`time_joined`,`aliases`) VALUES (?,?,?,?,?)", values)
            conn.commit()
            self.aliases.append(self.prettyname)
        else:
            # update name, IP address and last join date
            values = (self.prettyname, self.address, now, self.guid)
            curs.execute("UPDATE `player` SET `name` = ?,`ip_address` = ?,`time_joined` = ? WHERE `guid` = ?", values)
            conn.commit()
            # get known aliases
            values = (self.guid,)
            curs.execute("SELECT `aliases` FROM `player` WHERE `guid` = ?", values)
            result = curs.fetchone()
            # create list of aliases
            self.aliases = result[0].split(', ')
            if self.prettyname not in self.aliases:
                # add new alias to list
                if len(self.aliases) < 15:
                    self.aliases.append(self.prettyname)
                    alias_string = ', '.join(self.aliases)
                    values = (alias_string, self.guid)
                    curs.execute("UPDATE `player` SET `aliases` = ? WHERE `guid` = ?", values)
                    conn.commit()
        # get player-id
        values = (self.guid,)
        curs.execute("SELECT `id` FROM `player` WHERE `guid` = ?", values)
        self.player_id = curs.fetchone()[0]
        # check XLRSTATS table
        values = (self.guid,)
        curs.execute("SELECT COUNT(*) FROM `xlrstats` WHERE `guid` = ?", values)
        if curs.fetchone()[0] == 0:
            self.registered_user = False
        else:
            self.registered_user = True
            # get DB DATA for XLRSTATS
            values = (self.guid,)
            curs.execute("SELECT `last_played`,`num_played`,`kills`,`deaths`,`headshots`,`team_kills`,`team_death`,`max_kill_streak`,`suicides`,`admin_role` FROM `xlrstats` WHERE `guid` = ?", values)
            result = curs.fetchone()
            self.last_visit = result[0]
            self.num_played = result[1]
            self.db_kills = result[2]
            self.db_deaths = result[3]
            self.db_head_shots = result[4]
            self.db_tk_count = result[5]
            self.db_team_death = result[6]
            self.db_killing_streak = result[7]
            self.db_suicide = result[8]
            self.admin_role = result[9]
            # update name, last_played and increase num_played counter
            values = (self.prettyname, now, self.guid)
            curs.execute("UPDATE `xlrstats` SET `name` = ?,`last_played` = ?,`num_played` = `num_played` + 1 WHERE `guid` = ?", values)
            conn.commit()

    def define_offline_player(self, player_id):
        self.player_id = player_id
        values = (self.guid,)
        # get known aliases
        curs.execute("SELECT `aliases` FROM `player` WHERE `guid` = ?", values)
        result = curs.fetchone()
        # create list of aliases
        self.aliases = result[0].split(', ')
        curs.execute("SELECT COUNT(*) FROM `xlrstats` WHERE `guid` = ?", values)
        if curs.fetchone()[0] == 0:
            self.admin_role = 0
            self.registered_user = False
        else:
            curs.execute("SELECT `last_played`,`admin_role` FROM `xlrstats` WHERE `guid` = ?", values)
            result = curs.fetchone()
            self.last_visit = result[0]
            self.admin_role = result[1]
            self.registered_user = True

    def register_user_db(self, role=1):
        if not self.registered_user:
            now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            values = (self.guid, self.prettyname, self.address, now, now, role)
            curs.execute("INSERT INTO `xlrstats` (`guid`,`name`,`ip_address`,`first_seen`,`last_played`,`num_played`,`admin_role`) VALUES (?,?,?,?,?,1,?)", values)
            conn.commit()
            self.registered_user = True
            self.admin_role = role
            self.welcome_msg = False

    def update_db_admin_role(self, role):
        values = (role, self.guid)
        curs.execute("UPDATE `xlrstats` SET `admin_role` = ? WHERE `guid` = ?", values)
        conn.commit()
        # overwrite admin role in game, no reconnect of player required
        self.set_admin_role(role)

    def get_ban_id(self):
        return self.ban_id

    def set_name(self, name):
        self.name = "".join(name.split())

    def get_name(self):
        return self.name

    def get_aliases(self):
        if len(self.aliases) == 15:
            self.aliases.append("and more...")
        return str(", ".join(self.aliases))

    def set_guid(self, guid):
        self.guid = guid

    def get_guid(self):
        return self.guid

    def get_player_num(self):
        return self.player_num

    def get_player_id(self):
        return self.player_id

    def set_team(self, team):
        self.team = team

    def get_team(self):
        return self.team

    def get_team_lock(self):
        return self.team_lock

    def set_team_lock(self, team):
        self.team_lock = team

    def get_num_played(self):
        return self.num_played

    def get_last_visit(self):
        return str(self.last_visit)

    def get_db_kills(self):
        return self.db_kills

    def get_kills(self):
        return self.kills

    def get_db_deaths(self):
        return self.db_deaths

    def get_deaths(self):
        return self.deaths

    def get_db_headshots(self):
        return self.db_head_shots

    def get_headshots(self):
        return self.head_shots

    def disable_welcome_msg(self):
        self.welcome_msg = False

    def get_welcome_msg(self):
        return self.welcome_msg

    def get_country(self):
        return self.country

    def get_registered_user(self):
        return self.registered_user

    def set_admin_role(self, role):
        self.admin_role = role

    def get_admin_role(self):
        return self.admin_role

    def get_ip_address(self):
        return self.address

    def get_time_joined(self):
        return self.time_joined

    def get_max_kill_streak(self):
        return self.max_kill_streak

    def kill(self):
        self.killing_streak += 1
        self.kills += 1
        self.db_kills += 1

    def die(self):
        if self.killing_streak > self.max_kill_streak:
            self.max_kill_streak = self.killing_streak
        if self.max_kill_streak > self.db_killing_streak:
            self.db_killing_streak = self.max_kill_streak
        self.killing_streak = 0
        self.deaths += 1
        self.db_deaths += 1

    def suicide(self):
        self.db_suicide += 1

    def headshot(self):
        self.head_shots += 1
        self.db_head_shots += 1

    def set_all_hits(self):
        self.all_hits += 1

    def get_all_hits(self):
        return self.all_hits

    def get_killing_streak(self):
        return self.killing_streak

    def get_db_tks(self):
        return self.db_tk_count

    def get_team_kill_count(self):
        return self.tk_count

    def add_killed_me(self, killer):
        self.tk_killer_names.append(killer)

    def get_killed_me(self):
        return self.tk_killer_names

    def clear_killed_me(self, victim):
        while self.tk_victim_names.count(victim) > 0:
            self.tk_victim_names.remove(victim)

    def add_tk_victims(self, victim):
        self.tk_victim_names.append(victim)

    def get_tk_victim_names(self):
        return self.tk_victim_names

    def clear_tk(self, killer):
        while self.tk_killer_names.count(killer) > 0:
            self.tk_killer_names.remove(killer)

    def clear_all_tk(self):
        self.tk_killer_names = []

    def add_high_ping(self, value):
        self.high_ping_count += 1
        self.ping_value = value

    def clear_high_ping(self):
        self.high_ping_count = 0

    def get_high_ping(self):
        return self.high_ping_count

    def get_ping_value(self):
        return self.ping_value

    def add_spec_warning(self):
        self.spec_warn_count += 1

    def clear_spec_warning(self):
        self.spec_warn_count = 0

    def get_spec_warning(self):
        return self.spec_warn_count

    def add_warning(self):
        self.warn_counter += 1
        self.last_warn_time = time.time()

    def get_warning(self):
        return self.warn_counter

    def get_last_warn_time(self):
        return self.last_warn_time

    def clear_warning(self):
        self.warn_counter = 0
        self.spec_warn_count = 0
        self.tk_victim_names = []
        self.tk_killer_names = []
        # clear ban_points
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        values = (self.guid, now)
        curs.execute("DELETE FROM `ban_points` WHERE `guid` = ? and `expires` > ?", values)
        conn.commit()

    def team_death(self):
        # increase team death counter
        self.db_team_death += 1

    def team_kill(self):
        # increase teamkill counter
        self.tk_count += 1
        self.db_tk_count += 1

# CTF Mode
    def capture_flag(self):
        self.flags_captured += 1

    def get_flags_captured(self):
        return self.flags_captured

    def return_flag(self):
        self.flags_returned += 1

    def get_flags_returned(self):
        return self.flags_returned

# Bomb Mode
    def is_bombholder(self):
        self.bombholder = True

    def bomb_tossed(self):
        self.bombholder = False

    def get_bombholder(self):
        return self.bombholder

    def kill_bomb_carrier(self):
        self.bomb_carrier_killed += 1

    def get_bomb_carrier_kills(self):
        return self.bomb_carrier_killed

    def kills_with_bomb(self):
        self.killed_with_bomb += 1

    def get_kills_with_bomb(self):
        return self.killed_with_bomb

    def planted_bomb(self):
        self.bomb_planted += 1
        self.bombholder = False

    def get_planted_bomb(self):
        return self.bomb_planted

    def defused_bomb(self):
        self.bomb_defused += 1

    def get_defused_bomb(self):
        return self.bomb_defused

# Freeze Tag
    def freeze(self):
        self.froze += 1

    def get_freeze(self):
        return self.froze

    def thawout(self):
        self.thawouts += 1

    def get_thawout(self):
        return self.thawouts


### CLASS Game ###
class Game(object):
    """
    Game class
    """
    def __init__(self, config_file, urt42_modversion):
        """
        create a new instance of Game

        @param config_file: The full path of the bot configuration file
        @type  config_file: String
        """
        self.all_maps_list = []
        self.next_mapname = None
        self.mapname = None
        self.maplist = []
        self.players = {}
        self.live = False
        self.urt42_modversion = urt42_modversion
        game_cfg = ConfigParser.ConfigParser()
        game_cfg.read(config_file)
        self.rcon_handle = Rcon(game_cfg.get('server', 'server_ip'), game_cfg.get('server', 'server_port'), game_cfg.get('server', 'rcon_password'))
        if game_cfg.getboolean('rules', 'show_rules'):
            # create instance of Rules to display the rules and rotation messages
            Rules('./conf/rules.conf', game_cfg.getint('rules', 'rules_frequency'), self.rcon_handle)

        # add Spunky Bot as player 'World' to the game
        spunky_bot = Player(1022, '127.0.0.1', 'NONE', 'World')
        self.add_player(spunky_bot)
        print "- Added Spunky Bot successful to the game.\n"
        print "Spunky Bot is running until you are closing this session or pressing CTRL + C to abort this process."
        print "Note: Use the provided initscript to run Spunky Bot as daemon.\n"

    def send_rcon(self, command):
        """
        send RCON command

        @param command: The RCON command
        @type  command: String
        """
        if self.live:
            self.rcon_handle.push(command)

    def rcon_say(self, msg):
        """
        display message in global chat

        @param msg: The message to display in global chat
        @type  msg: String
        """
        # wrap long messages into shorter list elements
        lines = textwrap.wrap(msg, 145)
        for line in lines:
            self.send_rcon('say ^3%s' % line)

    def rcon_tell(self, player_num, msg, pm_tag=True):
        """
        tell message to a specific player

        @param player_num: The player number
        @type  player_num: Integer
        @param msg: The message to display in private chat
        @type  msg: String
        @param pm_tag: Display '[pm]' (private message) in front of the message
        @type  pm_tag: bool
        """
        lines = textwrap.wrap(msg, 135)
        prefix = "^4[pm]"
        for line in lines:
            if pm_tag:
                self.send_rcon('tell %d %s ^3%s' % (player_num, prefix, line))
                prefix = ""
            else:
                self.send_rcon('tell %d ^3%s' % (player_num, line))

    def rcon_bigtext(self, msg):
        """
        display bigtext message

        @param msg: The message to display in global chat
        @type  msg: String
        """
        self.send_rcon('bigtext "%s"' % msg)

    def rcon_forceteam(self, player_num, team):
        """
        force player to given team

        @param player_num: The player number
        @type  player_num: Integer
        @param team: The team (red, blue, spectator)
        @type  team: String
        """
        self.send_rcon('forceteam %d %s' % (player_num, team))

    def rcon_clear(self):
        """
        clear RCON queue
        """
        self.rcon_handle.clear()

    def get_rcon_handle(self):
        """
        get RCON handle
        """
        return self.rcon_handle

    def kick_player(self, player_num, reason=''):
        """
        kick player

        @param player_num: The player number
        @type  player_num: Integer
        @param reason: Reason for kick
        @type  reason: String
        """
        if reason and self.urt42_modversion:
            self.send_rcon('kick %d "%s"' % (player_num, reason))
        else:
            self.send_rcon('kick %d' % player_num)

    def go_live(self):
        """
        go live
        """
        self.live = True
        self.rcon_handle.go_live()
        self.set_all_maps()
        self.maplist = self.rcon_handle.get_mapcycle_path()
        self.set_current_map()

    def set_current_map(self):
        """
        set the current and next map in rotation
        """
        try:
            self.mapname = self.rcon_handle.get_quake_value('mapname')
        except KeyError:
            self.mapname = self.next_mapname

        if self.maplist:
            if self.mapname in self.maplist:
                if self.maplist.index(self.mapname) < (len(self.maplist) - 1):
                    self.next_mapname = self.maplist[self.maplist.index(self.mapname) + 1]
                else:
                    self.next_mapname = self.maplist[0]
            else:
                self.next_mapname = self.maplist[0]
        else:
            self.next_mapname = self.mapname

    def set_all_maps(self):
        """
        set a list of all available maps
        """
        all_maps = self.rcon_handle.get_rcon_output("dir map bsp")[1].split()
        all_maps.sort()
        all_maps_list = [maps.replace("/", "").replace(".bsp", "") for maps in all_maps if maps.startswith("/")]
        if all_maps_list:
            self.all_maps_list = all_maps_list

    def get_all_maps(self):
        """
        get a list of all available maps
        """
        return self.all_maps_list

    def add_player(self, player):
        """
        add a player to the game

        @param player: The instance of the player
        @type  player: Instance
        """
        self.players[player.get_player_num()] = player
        player.check_database()

    def get_gamestats(self):
        """
        get number of players in red team, blue team and spectator
        """
        game_data = {Player.teams[1]: 0, Player.teams[2]: 0, Player.teams[3]: 0}
        for player in self.players.itervalues():
            player_team = player.get_team()
            # red team
            if player_team == 1:
                game_data[Player.teams[1]] += 1
            # blue team
            elif player_team == 2:
                game_data[Player.teams[2]] += 1
            # spectators
            elif player_team == 3:
                game_data[Player.teams[3]] += 1
        return game_data

    def balance_teams(self, game_data):
        """
        balance teams if needed

        @param game_data: Dictionary of players in each team
        @type  game_data: dict
        """
        if (game_data[Player.teams[1]] - game_data[Player.teams[2]]) > 1:
            team1 = 1
            team2 = 2
        elif (game_data[Player.teams[2]] - game_data[Player.teams[1]]) > 1:
            team1 = 2
            team2 = 1
        else:
            self.rcon_say("^7Teams are already balanced")
            return
        self.rcon_bigtext("AUTOBALANCING TEAMS...")
        num_ptm = math.floor((game_data[Player.teams[team1]] - game_data[Player.teams[team2]]) / 2)
        player_list = [player for player in self.players.itervalues() if player.get_team() == team1 and not player.get_team_lock()]
        player_list.sort(cmp=lambda player1, player2: cmp(player2.get_time_joined(), player1.get_time_joined()))
        for player in player_list[:int(num_ptm)]:
            self.rcon_forceteam(player.get_player_num(), Player.teams[team2])
        self.rcon_say("^7Autobalance complete!")


### Main ###
print "\n\nStarting Spunky Bot:"

# load the GEO database and store it globally in interpreter memory
GEOIP = pygeoip.Database('./lib/GeoIP.dat')

# connect to database
conn = sqlite3.connect('./data.sqlite')
curs = conn.cursor()

# create tables if not exists
curs.execute('CREATE TABLE IF NOT EXISTS xlrstats (id INTEGER PRIMARY KEY NOT NULL, guid TEXT NOT NULL, name TEXT NOT NULL, ip_address TEXT NOT NULL, first_seen DATETIME, last_played DATETIME, num_played INTEGER DEFAULT 1, kills INTEGER DEFAULT 0, deaths INTEGER DEFAULT 0, headshots INTEGER DEFAULT 0, team_kills INTEGER DEFAULT 0, team_death INTEGER DEFAULT 0, max_kill_streak INTEGER DEFAULT 0, suicides INTEGER DEFAULT 0, ratio REAL DEFAULT 0, rounds INTEGER DEFAULT 0, admin_role INTEGER DEFAULT 1)')
curs.execute('CREATE TABLE IF NOT EXISTS player (id INTEGER PRIMARY KEY NOT NULL, guid TEXT NOT NULL, name TEXT NOT NULL, ip_address TEXT NOT NULL, time_joined DATETIME, aliases TEXT)')
curs.execute('CREATE TABLE IF NOT EXISTS ban_list (id INTEGER PRIMARY KEY NOT NULL, guid TEXT NOT NULL, name TEXT, ip_address TEXT, expires DATETIME DEFAULT 259200, timestamp DATETIME, reason TEXT)')
curs.execute('CREATE TABLE IF NOT EXISTS ban_points (id INTEGER PRIMARY KEY NOT NULL, guid TEXT NOT NULL, point_type TEXT, expires DATETIME)')
print "- Connected to database 'data.sqlite' successful."

# create instance of LogParser
LogParser('./conf/settings.conf')

# close database connection
conn.close()
