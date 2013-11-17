"""
Spunky Bot - Automated game server bot
http://urthub.github.io/spunkybot
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

### IMPORTS
import re
import time
import sqlite3
import math
import textwrap
import lib.pygeoip as PyGeoIP

from lib.rcon import Rcon
from lib.rules import Rules
from Queue import Queue
from threading import Thread
from threading import RLock
from ConfigParser import ConfigParser


## CLASS TaskManager ###
class TaskManager(object):
    """
    Tasks
     - get RCON status
     - display alert messages
     - check warnings
     - check for spectators on full server
     - check player ping
    """
    def __init__(self, frequency, max_ping, rcon_dispatcher):
        """
        create a new instance of TaskManager
        """
        self.frequency = frequency
        self.max_ping = max_ping
        self.rcon_dispatcher = rcon_dispatcher
        # start Thread
        self.processor = Thread(target=self.process)
        self.processor.setDaemon(True)
        self.processor.start()

    def process(self):
        """
        Thread process
        """
        while 1:
            # wait for given delay in the config file
            time.sleep(self.frequency)
            # get rcon status
            self.rcon_dispatcher.get_status()
            try:
                # check amount of warnings and kick player if needed
                self.check_warn()
                # check for spectators
                self.check_spec()
                # check for player with high ping
                self.check_ping()
            except Exception:
                continue

    def check_ping(self):
        """
        check ping of all players and set warning for high ping user
        """
        with players_lock:
            # rcon update status
            self.rcon_dispatcher.quake.rcon_update()
            for player in self.rcon_dispatcher.quake.players:
                # if ping is too high, inform player and increase warn counter, Admins or higher levels will not get the warning
                ping_value = player.ping
                gameplayer = game.players[int(player.num)]
                if self.max_ping < ping_value < 999 and gameplayer.get_admin_role() < 40:
                    gameplayer.add_high_ping()
                    game.rcon_tell(player.num, "^1WARNING ^7[^3%d^7]: ^7Your ping is too high [^4%d^7]. The maximum allowed is %d." % (gameplayer.get_high_ping(), ping_value, self.max_ping), False)
                else:
                    gameplayer.clear_high_ping()

    def check_spec(self):
        """
        check for spectators and set warning
        """
        counter = 0
        with players_lock:
            # get number of connected players
            for _ in game.players.itervalues():
                counter += 1

            for player in game.players.itervalues():
                gtv_connected = False
                # search for player with name prefix GTV-
                if 'GTV-' in player.get_name():
                    gtv_connected = True
                # if player is spectator on full server (more than 10 players), inform player and increase warn counter, GTV or Moderator or higher levels will not get the warning
                if counter > 11 and player.get_team() == 3 and player.get_admin_role() < 20 and player.get_time_joined() < (time.time() - 30) and player.get_player_num() != 1022 and not gtv_connected:
                    player.add_spec_warning()
                    game.rcon_tell(player.get_player_num(), "^1WARNING ^7[^3%d^7]: ^7You are spectator too long on full server" % player.get_spec_warning(), False)
                else:
                    player.clear_spec_warning()

    def check_warn(self):
        """
        check warnings and kick players with too many warnings
        """
        with players_lock:
            for player in game.players.itervalues():
                # kick player with 3 warnings, Admins will never get kicked
                if player.get_warning() > 2 and player.get_admin_role() < 40:
                    game.rcon_say("^7Player ^3%s ^7kicked, because of too many warnings" % player.get_name())
                    game.kick_player(player)
                # kick player with high ping after 3 warnings, Admins will never get kicked
                elif player.get_high_ping() > 2 and player.get_admin_role() < 40:
                    game.rcon_say("^7Player ^3%s ^7kicked, because his ping was too high for this server" % player.get_name())
                    game.kick_player(player)
                # kick spectator after 3 warnings, Moderator or higher levels will not get kicked
                elif player.get_spec_warning() > 2 and player.get_admin_role() < 20:
                    game.rcon_say("^7Player ^3%s ^7kicked, because of spectator too long on full server" % player.get_name())
                    game.kick_player(player)

                # warn player with 2 warnings, Admins will never get the alert warning
                if (player.get_warning() == 2 or player.get_spec_warning() == 2) and player.get_admin_role() < 40:
                    game.rcon_say("^1ALERT: ^7Player ^3%s, ^7auto-kick from warnings if not cleared" % player.get_name())
                    # increase counter to kick player next cycle automatically
                    player.add_spec_warning()
                    player.add_warning()


### CLASS Log Parser ###
class LogParser(object):
    """
    log file parser
    """
    def __init__(self, file_name, verbose_mode, tk_autokick, iamgod):
        """
        create a new instance of LogParser

        @param file_name: The full path of the games log file
        @type  file_name: String
        @param verbose_mode: Enable or disable verbose mode to print debug messages
        @type  verbose_mode: String
        @param tk_autokick: Enable or disable autokick for team killing
        @type  tk_autokick: String
        @param iamgod: Enable or disable option the get Head Admin
        @type  iamgod: String
        """
        # hit zone support for UrT > 4.2.013
        self.hit_points = {0: "HEAD", 1: "HEAD", 2: "HELMET", 3: "TORSO", 4: "VEST", 5: "LEFT_ARM", 6: "RIGHT_ARM", 7: "GROIN", 8: "BUTT", 9: "LEFT_UPPER_LEG", 10: "RIGHT_UPPER_LEG", 11: "LEFT_LOWER_LEG", 12: "RIGHT_LOWER_LEG", 13: "LEFT_FOOT", 14: "RIGHT_FOOT"}
        self.hit_item = {1: "UT_MOD_KNIFE", 2: "UT_MOD_BERETTA", 3: "UT_MOD_DEAGLE", 4: "UT_MOD_SPAS", 5: "UT_MOD_MP5K", 6: "UT_MOD_UMP45", 8: "UT_MOD_LR300", 9: "UT_MOD_G36", 10: "UT_MOD_PSG1", 14: "UT_MOD_SR8", 15: "UT_MOD_AK103", 17: "UT_MOD_NEGEV", 19: "UT_MOD_M4", 20: "UT_MOD_GLOCK", 21: "UT_MOD_COLT1911", 22: "UT_MOD_MAC11", 23: "UT_MOD_BLED", 24: "UT_MOD_KICKED", 25: "UT_MOD_KNIFE_THROWN"}
        self.death_cause = {1: "MOD_WATER", 5: "UT_MOD_TELEFRAG", 6: "MOD_FALLING", 7: "UT_MOD_SUICIDE", 9: "MOD_TRIGGER_HURT", 10: "MOD_CHANGE_TEAM", 12: "UT_MOD_KNIFE", 13: "UT_MOD_KNIFE_THROWN", 14: "UT_MOD_BERETTA", 15: "UT_MOD_KNIFE_DEAGLE", 16: "UT_MOD_SPAS", 17: "UT_MOD_UMP45", 18: "UT_MOD_MP5K", 19: "UT_MOD_LR300", 20: "UT_MOD_G36", 21: "UT_MOD_PSG1", 22: "UT_MOD_HK69", 23: "UT_MOD_BLED", 24: "UT_MOD_KICKED", 25: "UT_MOD_HEGRENADE", 28: "UT_MOD_SR8", 30: "UT_MOD_AK103", 31: "UT_MOD_SPLODED", 32: "UT_MOD_SLAPPED", 34: "UT_MOD_BOMBED", 35: "UT_MOD_NUKED", 36: "UT_MOD_NEGEV", 37: "UT_MOD_HK69_HIT", 38: "UT_MOD_M4", 39: "UT_MOD_GLOCK", 40: "UT_MOD_COLT1911", 41: "UT_MOD_MAC11", 42: "UT_MOD_FLAG"}

        # RCON commands for the different admin roles
        self.user_cmds = ['hs', 'register', 'stats', 'teams', 'time', 'xlrstats']
        self.mod_cmds = self.user_cmds + ['country', 'leveltest', 'list', 'mute', 'shuffleteams', 'warn']
        self.admin_cmds = self.mod_cmds + ['admins', 'aliases', 'bigtext', 'force', 'kick', 'nuke', 'say', 'tempban', 'warnclear']
        self.fulladmin_cmds = self.admin_cmds + ['ban', 'ci', 'scream', 'slap', 'veto']
        self.senioradmin_cmds = self.fulladmin_cmds + ['banlist', 'cyclemap', 'kill', 'kiss', 'map', 'maprestart', 'permban', 'putgroup', 'setnextmap', 'unban', 'ungroup']

        # alphabetic sort of the commands
        self.mod_cmds.sort()
        self.admin_cmds.sort()
        self.fulladmin_cmds.sort()
        self.senioradmin_cmds.sort()

        # open game log file
        self.log_file = open(file_name, 'r')
        # go to the end of the file
        self.log_file.seek(0, 2)
        self.ffa_lms_gametype = False
        self.ctf_gametype = False
        # enable/disable debug output
        self.verbose = True if verbose_mode == '1' else False
        # enable/disable autokick for team killing
        self.tk_autokick = True if tk_autokick == '1' else False
        # enable/disable option to get Head Admin
        self.iamgod = True if iamgod == '1' else False

    def find_game_start(self):
        """
        find InitGame start
        """
        lgf = self.log_file
        seek_amount = 768
        # search within the specified range for the InitGame message
        start_pos = lgf.tell() - seek_amount
        end_pos = start_pos + seek_amount
        lgf.seek(start_pos)
        game_start = False
        while not game_start:
            while lgf:
                line = lgf.readline()
                msg = re.search("(\d+:\d+)\s([A-Za-z]+\:)", line)
                if msg is not None and msg.group(2) == 'InitGame:':
                    game_start = True
                    if 'g_modversion\\4.1' in line:
                        # hit zone support for UrT 4.1
                        self.hit_points = {0: "HEAD", 1: "HELMET", 2: "TORSO", 3: "KEVLAR", 4: "ARMS", 5: "LEGS", 6: "BODY"}
                        self.hit_item = {1: "UT_MOD_KNIFE", 2: "UT_MOD_BERETTA", 3: "UT_MOD_DEAGLE", 4: "UT_MOD_SPAS", 5: "UT_MOD_MP5K", 6: "UT_MOD_UMP45", 8: "UT_MOD_LR300", 9: "UT_MOD_G36", 10: "UT_MOD_PSG1", 14: "UT_MOD_SR8", 15: "UT_MOD_AK103", 17: "UT_MOD_NEGEV", 19: "UT_MOD_M4", 21: "UT_MOD_KICKED", 22: "UT_MOD_KNIFE_THROWN"}
                        self.death_cause = {1: "MOD_WATER", 5: "UT_MOD_TELEFRAG", 6: "MOD_FALLING", 7: "UT_MOD_SUICIDE", 9: "MOD_TRIGGER_HURT", 10: "MOD_CHANGE_TEAM", 12: "UT_MOD_KNIFE", 13: "UT_MOD_KNIFE_THROWN", 14: "UT_MOD_BERETTA", 15: "UT_MOD_KNIFE_DEAGLE", 16: "UT_MOD_SPAS", 17: "UT_MOD_UMP45", 18: "UT_MOD_MP5K", 19: "UT_MOD_LR300", 20: "UT_MOD_G36", 21: "UT_MOD_PSG1", 22: "UT_MOD_HK69", 23: "UT_MOD_BLED", 24: "UT_MOD_KICKED", 25: "UT_MOD_HEGRENADE", 28: "UT_MOD_SR8", 30: "UT_MOD_AK103", 31: "UT_MOD_SPLODED", 32: "UT_MOD_SLAPPED", 33: "UT_MOD_BOMBED", 34: "UT_MOD_NUKED", 35: "UT_MOD_NEGEV", 37: "UT_MOD_HK69_HIT", 38: "UT_MOD_M4", 39: "UT_MOD_FLAG", 40: "UT_MOD_GOOMBA"}
                    if 'g_gametype\\0' in line or 'g_gametype\\1' in line:
                        # disable teamkill event for FFA (0) and LMS (1) mode
                        self.ffa_lms_gametype = True
                    if 'g_gametype\\7' in line:
                        self.ctf_gametype = True
                if lgf.tell() > end_pos:
                    break
                elif len(line) == 0:
                    break
            if lgf.tell() < seek_amount:
                lgf.seek(0, 0)
            else:
                cur_pos = start_pos - seek_amount
                end_pos = start_pos
                start_pos = cur_pos
                if start_pos < 0:
                    start_pos = 0
                lgf.seek(start_pos)

    def read_log(self):
        """
        read the logfile
        """
        self.find_game_start()
        lgf = self.log_file
        lgf.seek(0, 2)
        while lgf:
            line = lgf.readline()
            if len(line) != 0:
                self.parse_line(line)
            else:
                if not game.live:
                    print("Going Live...")
                    game.go_live()
                time.sleep(.125)

    def parse_line(self, string):
        """
        parse the logfile and search for specific action
        """
        inactive = set(['ClientConnect', 'sayteam', 'tell', 'saytell', 'Item', 'red', 'Flag Return', 'SurvivorWinner', 'Hotpotato', 'Warmup', 'Callvote', 'Vote', 'VotePassed', 'VoteFailed', 'Radio', 'score', 'InitAuth', 'AccountValidated', 'AccountRejected', 'AccountKick', 'InitRound'])
        line = string[7:]
        tmp = line.split(":", 1)
        try:
            line = tmp[1].strip()
            if tmp is not None:
                if tmp[0].lstrip() == 'InitGame':
                    self.handle_game_init(line)
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
                elif tmp[0].lstrip() == 'ShutdownGame':
                    self.handle_shutdown()
                elif tmp[0].lstrip() == 'say':
                    self.handle_say(line)
                elif tmp[0].lstrip() == 'Flag':
                    self.handle_flag(line)
                elif tmp[0].lstrip() == 'Exit':
                    self.handle_awards()
                elif tmp[0].lstrip() in inactive:
                    self.handle_misc()
                else:
                    self.error("ERROR: Unknown log entry in parse_line(): " + repr(tmp))
        except IndexError:
            if '------' in tmp[0]:
                self.handle_misc()
            elif 'Session data initialised' in tmp[0]:
                self.handle_misc()
            elif 'Bomb' in tmp[0] or 'Pop' in tmp[0]:
                self.handle_misc()
            else:
                if tmp[0] != '':
                    self.error("IndexError in parse_line(): %s" % tmp)
        except Exception:
            return -1

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

    def player_exists(self, player_num):
        """
        check if player exists
        """
        with players_lock:
            if player_num in game.players:
                return True
            else:
                return False

    def handle_game_init(self, line):
        """
        handle Game Init
        """
        if 'g_gametype\\0' in line or 'g_gametype\\1' in line:
            self.ffa_lms_gametype = True
        else:
            self.ffa_lms_gametype = False
        if 'g_gametype\\7' in line:
            self.ctf_gametype = True
        else:
            self.ctf_gametype = False
        self.debug("Starting game...")
        game.new_game()

    def handle_shutdown(self):
        """
        handle game end/shutdown
        """
        with players_lock:
            self.debug("Shutting down game...")
            game.rcon_handle.clear()
            for player in game.players.itervalues():
                player.save_info()
                player.reset()

    def handle_userinfo(self, line):
        """
        handle player user information, auto-kick known cheater ports or guids
        """
        with players_lock:
            player_num = int(line[:2].strip())
            line = line[2:].lstrip("\\").lstrip()
            values = self.explode_line(line.lstrip())
            challenge = True if 'challenge' in values else False
            try:
                guid = values['cl_guid'].rstrip('\n')
                name = re.sub(r"\s+", "", values['name'])
                ip_port = values['ip']
            except KeyError:
                if 'cl_guid' in values:
                    guid = values['cl_guid']
                else:
                    guid = "None"
                    game.send_rcon("Player with invalid GUID kicked")
                    game.send_rcon("kick %d" % player_num)
                if 'name' in values:
                    name = re.sub(r"\s+", "", values['name'])
                else:
                    name = "UnnamedPlayer"
                    game.send_rcon("Player with invalid name kicked")
                    game.send_rcon("kick %d" % player_num)
                if 'ip' in values:
                    ip_port = values['ip']
                else:
                    ip_port = "0.0.0.0"
                    game.send_rcon("Player with invalid IP address kicked")
                    game.send_rcon("kick %d" % player_num)

            address = ip_port.split(":")[0].strip()
            port = ip_port.split(":")[1].strip()

            # kick player with hax port 1337 or 1024
            if port == "1337" or port == "1024":
                game.send_rcon("Cheater Port detected for %s -> Player kicked" % name)
                game.send_rcon("kick %d" % player_num)
            # kick player with hax guid 'kemfew'
            if "KEMFEW" in guid.upper():
                game.send_rcon("Cheater GUID detected for %s -> Player kicked" % name)
                game.send_rcon("kick %d" % player_num)
            if "WORLD" in guid.upper() or "UNKNOWN" in guid.upper():
                game.send_rcon("Invalid GUID detected for %s -> Player kicked" % name)
                game.send_rcon("kick %d" % player_num)

            if not self.player_exists(player_num):
                try:
                    player = Player(player_num, address, guid, name)
                    game.add_player(player)
                except UnboundLocalError as error:
                    self.error("UnboundLocalError in handle_userinfo(): %s - %s" % (error, error.message))
            if game.players[player_num].get_guid() != guid:
                game.players[player_num].set_guid(guid)
            if game.players[player_num].get_name() != name:
                game.players[player_num].set_name(name)
            if challenge:
                self.debug("Player number: " + str(player_num) + " \"" + name + "\" is challenging the server and has the guid of: " + guid)
            else:
                if 'name' in values and values['name'] != game.players[player_num].get_name():
                    game.players[player_num].set_name(values['name'])

            # kick banned player
            if game.players[player_num].get_banned_player():
                game.send_rcon("kick %d" % player_num)

    def handle_userinfo_changed(self, line):
        """
        handle player changes
        """
        with players_lock:
            player_num = int(line[:2].strip())
            player = game.players[player_num]
            line = line[2:].lstrip("\\")
            try:
                values = self.explode_line(line.lstrip())
                team_num = values['t']
                player.set_team(int(team_num))
                name = re.sub(r"\s+", "", values['n'])
            except KeyError:
                player.set_team(3)
                team_num = "3"
                name = "UnnamedPlayer"

            team_dict = {0: "GREEN", 1: "RED", 2: "BLUE", 3: "SPEC"}
            if team_num in team_dict:
                team = team_dict[team_num]
            else:
                team = "SPEC"

            if not(game.players[player_num].get_name() == name):
                game.players[player_num].set_name(name)
            self.debug("Player number: " + str(player_num) + " \"" + name + "\" is on the " + team + " team")

    def handle_begin(self, line):
        """
        handle player entering game
        """
        with players_lock:
            player_num = int(line[:2].strip())
            try:
                player = game.players[player_num]
                # Welcome message for registered players
                if player.get_registered_user() and player.get_welcome_msg():
                    game.rcon_tell(player_num, "^7[^2Authed^7] Welcome back " + player.get_name() + ", you are ^2" + str(player.roles[player.get_admin_role()]) + "^7, last visit " + str(player.get_last_visit()) + ", you played " + str(player.get_num_played()) + " times", False)
                    # disable welcome message for next rounds
                    player.disable_welcome_msg()
            except KeyError:
                return -1
            else:
                self.debug("Player number: " + str(player_num) + " \"" + player.get_name() + "\" has entered the game")

    def handle_disconnect(self, line):
        """
        handle player disconnect
        """
        with players_lock:
            player_num = int(line[:2].strip())
            try:
                player = game.players[player_num]
                player.save_info()
                player.reset()
                del game.players[player_num]
            except KeyError:
                return -1
            else:
                self.debug("Player number: " + str(player_num) + " \"" + player.get_name() + "\" has left the game")

    def handle_hit(self, line):
        """
        handle all kind of hits
        """
        with players_lock:
            parts = line.split(":", 1)
            info = parts[0].split(" ")
            hitter_id = int(info[1])
            victim_id = int(info[0])
            try:
                hitter = game.players[hitter_id]
                victim = game.players[victim_id]
                hitter_name = hitter.get_name()
                victim_name = victim.get_name()
            except KeyError:
                return -1
            hitpoint = int(info[2])
            hit_item = int(info[3])
            # increase summary of all hits
            hitter.set_all_hits()

            if hitpoint in self.hit_points:
                if self.hit_points[hitpoint] == 'HEAD' or self.hit_points[int(hitpoint)] == 'HELMET':
                    hitter.headshot()
                    player_color = "^1" if (hitter.get_team() == 1) else "^4"
                    hs_plural = " headshots" if hitter.get_headshots() > 1 else " headshot"
                    if game.live:
                        percentage = int(round(float(hitter.get_headshots()) / float(hitter.get_all_hits()), 2) * 100)
                        game.send_rcon(player_color + hitter.get_name() + " ^7has " + str(hitter.get_headshots()) + "^7" + hs_plural + " (" + str(percentage) + " percent)")
                self.debug("Player number: " + str(hitter_id) + " \"" + hitter_name + "\" hit " + str(victim_id) + " \"" + victim_name + "\" in the " + self.hit_points[hitpoint] + " with " + self.hit_item[hit_item])

    def handle_kill(self, line):
        """
        handle kills
        """
        with players_lock:
            parts = line.split(":", 1)
            info = parts[0].split(" ")
            info1 = parts[1].strip().split(" ")
            k_name = info1[0]
            killer_id = int(info[0])
            victim_id = int(info[1])
            death_cause = self.death_cause[int(info[2])]
            try:
                victim = game.players[victim_id]
            except KeyError:
                return -1

            # do not count non-client kills
            if k_name != "<non-client>":
                try:
                    killer = game.players[killer_id]
                except KeyError:
                    return -1
            else:
                # killed by WORLD
                killer = game.players[1022]

            killer_name = killer.get_name()
            victim_name = victim.get_name()

            # teamkill event - disabled for FFA and LMS, for all other game modes team kills are counted and punished
            if not self.ffa_lms_gametype:
                if (victim.get_team() == killer.get_team() and victim.get_player_num() != killer.get_player_num()) and death_cause != "UT_MOD_BOMBED":
                    if self.tk_autokick:
                        game.send_rcon("%s ^1teamkilled ^7%s" % (killer_name, victim_name))
                    # increase team kill counter for killer and kick for too many team kills
                    killer.team_kill(victim, self.tk_autokick)
                    # increase team death counter for victim
                    victim.team_death()

            # suicide counter
            if death_cause == 'UT_MOD_SUICIDE' or death_cause == 'MOD_FALLING' or death_cause == 'MOD_WATER' or death_cause == 'UT_MOD_SPLODED' or (killer.get_player_num() == victim.get_player_num() and (death_cause == 'UT_MOD_HEGRENADE' or death_cause == 'UT_MOD_HK69' or death_cause == 'UT_MOD_NUKED' or death_cause == 'UT_MOD_SLAPPED')):
                killer.suicide()
                victim.die()
            elif int(info[2]) != 10:  # 10: MOD_CHANGE_TEAM
                killer.kill()
                killer_color = "^1" if (killer.get_team() == 1) else "^4"
                if killer.get_killing_streak() == 5 and killer_name != 'World':
                    game.rcon_say(killer_color + killer_name + " ^7is on a killing spree!")
                elif killer.get_killing_streak() == 10 and killer_name != 'World':
                    game.rcon_say(killer_color + killer_name + " ^7is on a rampage!")
                elif killer.get_killing_streak() == 15 and killer_name != 'World':
                    game.rcon_say(killer_color + killer_name + " ^7is unstoppable!")
                elif killer.get_killing_streak() == 20 and killer_name != 'World':
                    game.rcon_say(killer_color + killer_name + " ^7is godlike!")

                victim_color = "^1" if (victim.get_team() == 1) else "^4"
                if victim.get_killing_streak() >= 20 and killer_name != victim_name and killer_name != 'World':
                    game.rcon_say(victim_color + victim_name + "'s ^7godlike was ended by " + killer_color + killer_name + "!")
                elif victim.get_killing_streak() >= 15 and killer_name != victim_name and killer_name != 'World':
                    game.rcon_say(victim_color + victim_name + "'s ^7unstoppable was ended by " + killer_color + killer_name + "!")
                elif victim.get_killing_streak() >= 10 and killer_name != victim_name and killer_name != 'World':
                    game.rcon_say(victim_color + victim_name + "'s ^7rampage was ended by " + killer_color + killer_name + "!")
                elif victim.get_killing_streak() >= 5 and killer_name != victim_name and killer_name != 'World':
                    game.rcon_say(victim_color + victim_name + "'s ^7killing spree was ended by " + killer_color + killer_name + "!")
                victim.die()
                self.debug("Player number: " + str(killer_id) + " \"" + killer_name + "\" killed " + str(victim_id) + " \"" + victim_name + "\" with " + death_cause)
            else:
                self.debug("Player number: " + str(killer_id) + " \"" + killer_name + "\" has changed teams")

    def handle_say(self, line):
        """
        handle say commands
        """
        reason_dict = {'obj': 'go for objective', 'camp': 'stop camping', 'spam': 'do not spam, shut-up!', 'lang': 'bad language', 'racism': 'racism is not tolerated',
                       'ping': 'fix your ping', 'afk': 'away from keyboard', 'tk': 'stop team killing', 'spec': 'spectator too long on full server', 'ci': 'connection interrupted'}

        with players_lock:
            s = self.explode_line2(line)

            if s['command'] == '!mapstats':
                game.rcon_tell(s['player_num'], "^7" + str(game.players[s['player_num']].get_kills()) + " ^7kills - " + str(game.players[s['player_num']].get_deaths()) + " ^7deaths")
                game.rcon_tell(s['player_num'], "^7" + str(game.players[s['player_num']].get_team_killer()) + " ^7teamkills")
                game.rcon_tell(s['player_num'], "^7" + str(game.players[s['player_num']].get_killing_streak()) + " ^7current kill streak")
                game.rcon_tell(s['player_num'], "^7" + str(game.players[s['player_num']].get_all_hits()) + " ^7total hits - " + str(game.players[s['player_num']].get_headshots()) + " ^7headshots")
                if self.ctf_gametype:
                    game.rcon_tell(s['player_num'], "^7" + str(game.players[s['player_num']].get_flags_captured()) + " ^7flags captured - " + str(game.players[s['player_num']].get_flags_returned()) + " ^7flags returned")

            elif s['command'] == '!help' or s['command'] == '!h':
                ## TO DO - specific help for each command
                if game.players[s['player_num']].get_admin_role() < 20:
                    game.rcon_tell(s['player_num'], "^7Available commands:")
                    game.rcon_tell(s['player_num'], ", ".join(self.user_cmds), False)
                # help for mods - additional commands
                elif game.players[s['player_num']].get_admin_role() == 20:
                    game.rcon_tell(s['player_num'], "^7Moderator commands:")
                    game.rcon_tell(s['player_num'], ", ".join(self.mod_cmds), False)
                # help for admins - additional commands
                elif game.players[s['player_num']].get_admin_role() == 40:
                    game.rcon_tell(s['player_num'], "^7Admin commands:")
                    game.rcon_tell(s['player_num'], ", ".join(self.admin_cmds), False)
                # help for full admins - additional commands
                elif game.players[s['player_num']].get_admin_role() == 60:
                    game.rcon_tell(s['player_num'], "^7Full Admin commands:")
                    game.rcon_tell(s['player_num'], ", ".join(self.fulladmin_cmds), False)
                elif game.players[s['player_num']].get_admin_role() >= 80:
                    game.rcon_tell(s['player_num'], "^7Senior Admin commands:")
                    game.rcon_tell(s['player_num'], ", ".join(self.senioradmin_cmds), False)

## player commands
            # register - register yourself as a basic user
            elif s['command'] == '!register':
                if not game.players[s['player_num']].get_registered_user():
                    game.players[s['player_num']].register_user_db(role=1)
                    game.rcon_tell(s['player_num'], "%s ^7put in group User" % game.players[s['player_num']].get_name())
                else:
                    game.rcon_tell(s['player_num'], "%s ^7is already in a higher level group" % game.players[s['player_num']].get_name())

            # hs - display headshot counter
            elif s['command'] == '!hs':
                game.rcon_tell(s['player_num'], "^7%d headshots" % game.players[s['player_num']].get_headshots())

            # time - display the servers current time
            elif s['command'] == '!time':
                game.rcon_say("^7%s CET" % time.strftime("%H:%M", time.localtime(time.time())))

            # teams - balance teams
            elif s['command'] == '!teams' and not self.ffa_lms_gametype:
                game_data = game.get_gamestats()
                if (abs(game_data[Player.teams[1]] - game_data[Player.teams[2]]) + 3) > 1:
                    game.balance_teams()

            # stats - display current map stats
            elif s['command'] == '!stats':
                if game.players[s['player_num']].get_deaths() == 0:
                    ratio = 1.0
                else:
                    ratio = round(float(game.players[s['player_num']].get_kills()) / float(game.players[s['player_num']].get_deaths()), 2)
                game.rcon_tell(s['player_num'], "^7Stats " + game.players[s['player_num']].get_name() + ": ^7K ^2" + str(game.players[s['player_num']].get_kills()) + " ^7D ^3" + str(game.players[s['player_num']].get_deaths()) + " ^7TK ^1" + str(game.players[s['player_num']].get_team_killer()) + " ^7Ratio ^5" + str(ratio) + " ^7HS ^2" + str(game.players[s['player_num']].get_headshots()))

            # xlrstats - display full player stats
            elif s['command'] == '!xlrstats':
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    for player in game.players.itervalues():
                        if (arg.upper() in (player.get_name()).upper()) or arg == str(player.get_player_num()):
                            if player.get_registered_user():
                                if player.get_xlr_deaths() == 0:
                                    ratio = 1.0
                                else:
                                    ratio = round(float(player.get_xlr_kills()) / float(player.get_xlr_deaths()), 2)
                                game.rcon_tell(s['player_num'], "^7XLR Stats " + player.get_name() + ": ^7K ^2" + str(player.get_xlr_kills()) + " ^7D ^3" + str(player.get_xlr_deaths()) + " ^7TK ^1" + str(player.get_xlr_tks()) + " ^7Ratio ^5" + str(ratio) + " ^7HS ^2" + str(player.get_xlr_headshots()))
                            else:
                                game.rcon_tell(s['player_num'], "^7Sorry, this player is not registered")
                else:
                    if game.players[s['player_num']].get_registered_user():
                        if game.players[s['player_num']].get_xlr_deaths() == 0:
                            ratio = 1.0
                        else:
                            ratio = round(float(game.players[s['player_num']].get_xlr_kills()) / float(game.players[s['player_num']].get_xlr_deaths()), 2)
                        game.rcon_tell(s['player_num'], "^7XLR Stats " + game.players[s['player_num']].get_name() + ": ^7K ^2" + str(game.players[s['player_num']].get_xlr_kills()) + " ^7D ^3" + str(game.players[s['player_num']].get_xlr_deaths()) + " ^7TK ^1" + str(game.players[s['player_num']].get_xlr_tks()) + " ^7Ratio ^5" + str(ratio) + " ^7HS ^2" + str(game.players[s['player_num']].get_xlr_headshots()))
                    else:
                        game.rcon_tell(s['player_num'], "^7You need to ^2!register ^7first")

## mod level 20
            # country
            elif s['command'] == '!country' and game.players[s['player_num']].get_admin_role() >= 20:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    for player in game.players.itervalues():
                        if (arg.upper() in (player.get_name()).upper()) or arg == str(player.get_player_num()):
                            game.rcon_tell(s['player_num'], "Country ^3" + player.get_name() + ": ^7" + str(player.get_country()))
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !country <name>")

            # leveltest
            elif (s['command'] == '!leveltest' or s['command'] == '!lt') and game.players[s['player_num']].get_admin_role() >= 20:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    for player in game.players.itervalues():
                        if (arg.upper() in (player.get_name()).upper()) or arg == str(player.get_player_num()):
                            game.rcon_tell(s['player_num'], "Level ^3" + player.get_name() + " [^2" + str(player.get_admin_role()) + "^3]: ^7" + str(player.roles[player.get_admin_role()]))
                else:
                    game.rcon_tell(s['player_num'], "Level ^3" + game.players[s['player_num']].get_name() + " [^2" + str(game.players[s['player_num']].get_admin_role()) + "^3]: ^7" + str(game.players[s['player_num']].roles[game.players[s['player_num']].get_admin_role()]))

            # list - list all connected players
            elif s['command'] == '!list' and game.players[s['player_num']].get_admin_role() >= 20:
                msg = "^7Players online: "
                for player in game.players.itervalues():
                    if player.get_player_num() != 1022:
                        msg += "^3%s[^2%d^3], " % (player.get_name(), player.get_player_num())
                game.rcon_tell(s['player_num'], msg.rstrip(', '))

            # mute - mute or unmute a player
            elif s['command'] == '!mute' and game.players[s['player_num']].get_admin_role() >= 20:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    count = 0
                    for player in game.players.itervalues():
                        if arg.upper() in (player.get_name()).upper() or arg == str(player.get_player_num()):
                            victim = player
                            count += 1
                    if count == 0:
                        game.rcon_tell(s['player_num'], "No Player found")
                    elif count > 1:
                        game.rcon_tell(s['player_num'], "More than one Player found")
                    else:
                        game.send_rcon("mute %d" % victim.get_player_num())
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !mute <name>")

            # shuffleteams
            elif (s['command'] == '!shuffleteams' or s['command'] == '!shuffle') and not self.ffa_lms_gametype and game.players[s['player_num']].get_admin_role() >= 20:
                game.send_rcon('shuffleteams')

            # warn - warn user
            elif (s['command'] == '!warn' or s['command'] == '!w') and game.players[s['player_num']].get_admin_role() >= 20:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    if ' ' in arg:
                        liste = arg.split(' ')
                        user = liste[0]
                        reason = ' '.join(liste[1:])
                        count = 0
                        for player in game.players.itervalues():
                            if user.upper() in (player.get_name()).upper() or user == str(player.get_player_num()):
                                victim = player
                                count += 1
                        if count == 0:
                            game.rcon_tell(s['player_num'], "No Player found")
                        elif count > 1:
                            game.rcon_tell(s['player_num'], "More than one Player found")
                        else:
                            if victim.get_admin_role() >= game.players[s['player_num']].get_admin_role():
                                game.rcon_tell(s['player_num'], "You cannot warn an admin")
                            else:
                                victim.add_warning()
                                msg = "^1WARNING ^7[^3" + str(victim.get_warning()) + "^7]: ^2" + victim.get_name() + "^7, reason: "
                                if reason in reason_dict:
                                    msg += reason_dict[reason]
                                    if reason == 'tk' and victim.get_warning() > 1:
                                        victim.add_ban_point('tk, ban by ' + game.players[s['player_num']].get_name(), 600)
                                    elif reason == 'lang' and victim.get_warning() > 1:
                                        victim.add_ban_point('lang', 300)
                                    elif reason == 'spam' and victim.get_warning() > 1:
                                        victim.add_ban_point('spam', 300)
                                    elif reason == 'racism' and victim.get_warning() > 1:
                                        victim.add_ban_point('racism', 300)
                                else:
                                    msg += reason
                                game.rcon_say(msg)
                    else:
                        game.rcon_tell(s['player_num'], "^7You need to enter a reason: ^3!warn <name> <reason>")
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !warn <name> <reason>")

## admin level 40
            # admins - list all the online admins
            elif (s['command'] == '!admins' or s['command'] == '@admins') and game.players[s['player_num']].get_admin_role() >= 40:
                msg = "^7Admins online: "
                for player in game.players.itervalues():
                    if player.get_admin_role() >= 20:
                        msg += "^3%s[^2%d^3], " % (player.get_name(), player.get_admin_role())
                if '@' in s['command']:
                    game.rcon_say(msg.rstrip(', '))
                else:
                    game.rcon_tell(s['player_num'], msg.rstrip(', '))

            # aliases - list the aliases of the player
            elif (s['command'] == '!aliases' or s['command'] == '!alias') and game.players[s['player_num']].get_admin_role() >= 40:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    count = 0
                    for player in game.players.itervalues():
                        if arg.upper() in (player.get_name()).upper() or arg == str(player.get_player_num()):
                            victim = player
                            count += 1
                    if count == 0:
                        game.rcon_tell(s['player_num'], "No Player found")
                    elif count > 1:
                        game.rcon_tell(s['player_num'], "More than one Player found")
                    else:
                        game.rcon_tell(s['player_num'], "^7Aliases of ^5%s: ^3%s" % (victim.get_name(), str(victim.get_aliases())))
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !alias <name>")

            # bigtext - display big message on screen
            elif s['command'] == '!bigtext' and game.players[s['player_num']].get_admin_role() >= 40:
                if line.split(s['command'])[1]:
                    game.rcon_bigtext("%s" % line.split(s['command'])[1].strip())
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !bigtext <text>")

            # say - say a message to all players
            elif s['command'] == '!say' and game.players[s['player_num']].get_admin_role() >= 40:
                if line.split(s['command'])[1]:
                    game.rcon_say("%s" % line.split(s['command'])[1].strip())
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !say <text>")

            # force - force a player to the given team
            elif s['command'] == '!force' and game.players[s['player_num']].get_admin_role() >= 40:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    if ' ' in arg:
                        user = arg.split(' ')[0]
                        team = arg.split(' ')[1]
                        team_dict = {'red': 'red', 'r': 'red', 're': 'red',
                                     'blue': 'blue', 'b': 'blue', 'bl': 'blue', 'blu': 'blue',
                                     'spec': 'spectator', 'spectator': 'spectator', 's': 'spectator', 'sp': 'spectator', 'spe': 'spectator'}
                        count = 0
                        for player in game.players.itervalues():
                            if user.upper() in (player.get_name()).upper() or user == str(player.get_player_num()):
                                victim = player
                                count += 1
                        if count == 0:
                            game.rcon_tell(s['player_num'], "No Player found")
                        elif count > 1:
                            game.rcon_tell(s['player_num'], "More than one Player found")
                        else:
                            if team in team_dict:
                                game.rcon_forceteam(victim.get_player_num(), team_dict[team])
                                game.rcon_tell(victim.get_player_num(), "^3You are forced to: ^7%s" % team_dict[team])
                            else:
                                game.rcon_tell(s['player_num'], "^7Usage: !force <name> <blue/red/spec>")
                    else:
                        game.rcon_tell(s['player_num'], "^7Usage: !force <name> <blue/red/spec>")
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !force <name> <blue/red/spec>")

            # nuke - nuke a player
            elif s['command'] == '!nuke' and game.players[s['player_num']].get_admin_role() >= 40:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    count = 0
                    for player in game.players.itervalues():
                        if arg.upper() in (player.get_name()).upper() or arg == str(player.get_player_num()):
                            victim = player
                            count += 1
                    if count == 0:
                        game.rcon_tell(s['player_num'], "No Player found")
                    elif count > 1:
                        game.rcon_tell(s['player_num'], "More than one Player found")
                    else:
                        if victim.get_admin_role() >= game.players[s['player_num']].get_admin_role():
                            game.rcon_tell(s['player_num'], "You cannot nuke an admin")
                        else:
                            game.send_rcon("nuke " + str(victim.get_player_num()))
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !nuke <name>")

            # kick - kick a player
            elif (s['command'] == '!kick' or s['command'] == '!k') and game.players[s['player_num']].get_admin_role() >= 40:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    if ' ' in arg:
                        liste = arg.split(' ')
                        user = liste[0]
                        reason = ' '.join(liste[1:])
                        count = 0
                        for player in game.players.itervalues():
                            if user.upper() in (player.get_name()).upper() or user == str(player.get_player_num()):
                                victim = player
                                count += 1
                        if count == 0:
                            game.rcon_tell(s['player_num'], "No Player found")
                        elif count > 1:
                            game.rcon_tell(s['player_num'], "More than one Player found")
                        else:
                            if victim.get_admin_role() >= game.players[s['player_num']].get_admin_role():
                                game.rcon_tell(s['player_num'], "You cannot kick an admin")
                            else:
                                game.kick_player(victim)
                                msg = "^2" + victim.get_name() + "^4 kicked by ^3" + game.players[s['player_num']].get_name() + "^4, reason: "
                                if reason in reason_dict:
                                    msg += reason_dict[reason]
                                else:
                                    msg += reason
                                game.rcon_say(msg)
                                print("KICK: %s" % msg)
                    else:
                        game.rcon_tell(s['player_num'], "^7You need to enter a reason: ^3!kick <name> <reason>")
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !kick <name> <reason>")

            # warnclear - clear the user warnings
            elif (s['command'] == '!warnclear' or s['command'] == '!wc' or s['command'] == '!wr') and game.players[s['player_num']].get_admin_role() >= 40:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    count = 0
                    for player in game.players.itervalues():
                        if arg.upper() in (player.get_name()).upper() or arg == str(player.get_player_num()):
                            victim = player
                            count += 1
                    if count == 0:
                        game.rcon_tell(s['player_num'], "No Player found")
                    elif count > 1:
                        game.rcon_tell(s['player_num'], "More than one Player found")
                    else:
                        victim.clear_warning()
                        game.rcon_say("^1All warnings cleared for ^2%s" % victim.get_name())
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !warnclear <name>")

            # tempban - ban a player temporary for given period in hours (1-24 hrs)
            elif (s['command'] == '!tempban' or s['command'] == '!tb') and game.players[s['player_num']].get_admin_role() >= 40:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    if ' ' in arg:
                        liste = arg.split(' ')
                        user = liste[0]
                        if len(liste) == 2:
                            reason_string = liste[1]
                            duration_string = '1'
                        else:
                            reason_string = liste[1]
                            duration_string = liste[2].rstrip('hm')
                        if reason_string.rstrip('hm').isdigit():
                            game.rcon_tell(s['player_num'], "^7You need to enter a reason: ^3!tempban <name> <reason> [<duration in hours>]")
                        else:
                            reason = str(reason_string) + ", ban by " + game.players[s['player_num']].get_name()
                            if duration_string.isdigit():
                                duration = int(duration_string) * 3600
                            else:
                                duration = 3600
                            if duration == 3600:
                                duration_output = "1 hour"
                            else:
                                duration_output = str(duration_string) + " hours"
                            if duration > 86400:
                                duration = 86400
                                duration_output = "24 hours"
                            count = 0
                            for player in game.players.itervalues():
                                if user.upper() in (player.get_name()).upper() or user == str(player.get_player_num()):
                                    victim = player
                                    count += 1
                            if count == 0:
                                game.rcon_tell(s['player_num'], "No Player found")
                            elif count > 1:
                                game.rcon_tell(s['player_num'], "More than one Player found")
                            else:
                                if victim.get_admin_role() >= game.players[s['player_num']].get_admin_role():
                                    game.rcon_tell(s['player_num'], "You cannot ban an admin")
                                else:
                                    victim.ban(duration=duration, reason=reason)
                                    game.rcon_say("^2" + victim.get_name() + "^4 banned by ^3" + game.players[s['player_num']].get_name() + "^4 for " + duration_output + ", ^3reason: " + str(reason_string))
                    else:
                        game.rcon_tell(s['player_num'], "^7You need to enter a reason: ^3!tempban <name> <reason> [<duration in hours>]")
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !tempban <name> <reason> [<duration in hours>]")

## full admin level 60
            # scream - scream a message in different colors to all players
            elif s['command'] == '!scream' and game.players[s['player_num']].get_admin_role() >= 60:
                if line.split(s['command'])[1]:
                    game.rcon_say("^1%s" % line.split(s['command'])[1].strip())
                    game.rcon_say("^2%s" % line.split(s['command'])[1].strip())
                    game.rcon_say("^3%s" % line.split(s['command'])[1].strip())
                    game.rcon_say("^5%s" % line.split(s['command'])[1].strip())
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !scream <text>")

            # slap - slap a player (a number of times); (1-10 times)
            elif (s['command'] == '!slap' or s['command'] == '!spank') and game.players[s['player_num']].get_admin_role() >= 60:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    if ' ' in arg:
                        user = arg.split(' ')[0]
                        number = arg.split(' ')[1]
                        if not number.isdigit():
                            number = 1
                        else:
                            number = int(number)
                        if number > 10:
                            number = 10
                    else:
                        user = arg
                        number = 1
                    count = 0
                    for player in game.players.itervalues():
                        if user.upper() in (player.get_name()).upper() or user == str(player.get_player_num()):
                            victim = player
                            count += 1
                    if count == 0:
                        game.rcon_tell(s['player_num'], "No Player found")
                    elif count > 1:
                        game.rcon_tell(s['player_num'], "More than one Player found")
                    else:
                        if victim.get_admin_role() >= game.players[s['player_num']].get_admin_role():
                            game.rcon_tell(s['player_num'], "You cannot slap an admin")
                        else:
                            for _ in range(0, number):
                                game.send_rcon("slap %d" % victim.get_player_num())
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !slap <name> [<amount>]")

            # veto - stop voting process
            elif s['command'] == '!veto' and game.players[s['player_num']].get_admin_role() >= 60:
                game.send_rcon('veto')

            # ci - kick player with connection interrupted
            elif s['command'] == '!ci' and game.players[s['player_num']].get_admin_role() >= 60:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    count = 0
                    player_ping = 0
                    for player in game.players.itervalues():
                        if arg.upper() in (player.get_name()).upper() or arg == str(player.get_player_num()):
                            victim = player
                            count += 1
                    if count == 0:
                        game.rcon_tell(s['player_num'], "No Player found")
                    elif count > 1:
                        game.rcon_tell(s['player_num'], "More than one Player found")
                    else:
                        # update rcon status
                        game.rcon_handle.quake.rcon_update()
                        for player in game.rcon_handle.quake.players:
                            if victim.get_player_num() == player.num:
                                player_ping = player.ping
                        if player_ping == 999:
                            game.kick_player(victim)
                            game.rcon_say("^2%s ^4kicked by ^3%s^4, connection interrupted" % (victim.get_name(), game.players[s['player_num']].get_name()))
                        else:
                            game.rcon_tell(s['player_num'], "%s has no connection interrupted" % victim.get_name())
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !ci <name>")

            # ban - ban a player for 7 days
            elif (s['command'] == '!ban' or s['command'] == '!b') and game.players[s['player_num']].get_admin_role() >= 60:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    if ' ' in arg:
                        liste = arg.split(' ')
                        user = liste[0]
                        reason_string = ' '.join(liste[1:])
                        reason = reason_string + ", ban by " + game.players[s['player_num']].get_name()
                        count = 0
                        for player in game.players.itervalues():
                            if user.upper() in (player.get_name()).upper() or user == str(player.get_player_num()):
                                victim = player
                                count += 1
                        if count == 0:
                            game.rcon_tell(s['player_num'], "No Player found")
                        elif count > 1:
                            game.rcon_tell(s['player_num'], "More than one Player found")
                        else:
                            if victim.get_admin_role() >= game.players[s['player_num']].get_admin_role():
                                game.rcon_tell(s['player_num'], "You cannot ban an admin")
                            else:
                                # ban for 7 days
                                victim.ban(duration=604800, reason=reason)
                                game.rcon_say("^2" + victim.get_name() + "^4 banned by ^3" + game.players[s['player_num']].get_name() + "^4 for 7 days, ^3reason: " + reason_string)
                    else:
                        game.rcon_tell(s['player_num'], "^7You need to enter a reason: ^3!ban <name> <reason>")
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !ban <name> <reason>")

## senior admin level 80
            # kiss - clear all player warnings
            elif (s['command'] == '!kiss' or s['command'] == '!clear') and game.players[s['player_num']].get_admin_role() >= 80:
                for player in game.players.itervalues():
                    player.clear_warning()
                game.rcon_say("^1All player warnings cleared")

            # map - load given map
            elif s['command'] == '!map' and game.players[s['player_num']].get_admin_role() >= 80:
                if line.split(s['command'])[1]:
                    game.send_rcon('map %s' % line.split(s['command'])[1].strip())
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !map <ut4_name>")

            # maprestart - restart the map
            elif s['command'] == '!maprestart' and game.players[s['player_num']].get_admin_role() >= 80:
                game.send_rcon('restart')

            # cyclemap - start next map in rotation
            elif s['command'] == '!cyclemap' and game.players[s['player_num']].get_admin_role() >= 80:
                game.send_rcon('cyclemap')

            # setnextmap - set the given map as nextmap
            elif s['command'] == '!setnextmap' and game.players[s['player_num']].get_admin_role() >= 80:
                if line.split(s['command'])[1]:
                    game.send_rcon('g_nextmap %s' % line.split(s['command'])[1].strip())
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !setnextmap <ut4_name>")

            # kill - kill a player
            elif s['command'] == '!kill' and game.players[s['player_num']].get_admin_role() >= 80:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    count = 0
                    for player in game.players.itervalues():
                        if arg.upper() in (player.get_name()).upper() or arg == str(player.get_player_num()):
                            victim = player
                            count += 1
                    if count == 0:
                        game.rcon_tell(s['player_num'], "No Player found")
                    elif count > 1:
                        game.rcon_tell(s['player_num'], "More than one Player found")
                    else:
                        if victim.get_admin_role() >= game.players[s['player_num']].get_admin_role():
                            game.rcon_tell(s['player_num'], "You cannot kill an admin")
                        else:
                            game.send_rcon("smite %d" % victim.get_player_num())
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !kill <name>")

            # permban - ban a player permanent
            elif (s['command'] == '!permban' or s['command'] == '!pb') and game.players[s['player_num']].get_admin_role() >= 80:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    if ' ' in arg:
                        liste = arg.split(' ')
                        user = liste[0]
                        reason_string = ' '.join(liste[1:])
                        reason = reason_string + ", ban by " + game.players[s['player_num']].get_name()
                        count = 0
                        for player in game.players.itervalues():
                            if user.upper() in (player.get_name()).upper() or user == str(player.get_player_num()):
                                victim = player
                                count += 1
                        if count == 0:
                            game.rcon_tell(s['player_num'], "No Player found")
                        elif count > 1:
                            game.rcon_tell(s['player_num'], "More than one Player found")
                        else:
                            if victim.get_admin_role() >= game.players[s['player_num']].get_admin_role():
                                game.rcon_tell(s['player_num'], "You cannot ban an admin")
                            else:
                                # ban for 20 years
                                victim.ban(duration=630720000, reason=reason)
                                game.rcon_say("^2" + victim.get_name() + "^4 banned by ^3" + game.players[s['player_num']].get_name() + "^4 permanent, ^3reason: " + reason_string)
                                # add IP address to bot-banlist.txt
                                banlist = open('./bot-banlist.txt', 'a+')
                                banlist.write(str(victim.get_ip_address()) + ":-1   // " + victim.get_name() + "    banned on  " + time.strftime("%d/%m/%Y (%H:%M)", time.localtime(time.time())) + ", reason : " + reason_string + "\n")
                                banlist.close()
                    else:
                        game.rcon_tell(s['player_num'], "^7You need to enter a reason: ^3!permban <name> <reason>")
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !permban <name> <reason>")

            # putgroup - add a client to a group
            elif s['command'] == '!putgroup' and game.players[s['player_num']].get_admin_role() >= 80:
                if line.split(s['command'])[1]:
                    cmd = str(line.split(s['command'])[1]).strip()
                    if ' ' in cmd:
                        user = cmd.split(' ')[0]
                        right = cmd.split(' ')[1]
                        count = 0
                        for player in game.players.itervalues():
                            if user.upper() in (player.get_name()).upper() or user == str(player.get_player_num()):
                                victim = player
                                count += 1
                        if count == 0:
                            game.rcon_tell(s['player_num'], "No Player found")
                        elif count > 1:
                            game.rcon_tell(s['player_num'], "More than one Player found")
                        else:
                            if victim.get_registered_user():
                                new_role = victim.get_admin_role()
                            else:
                                # register new user in DB and set role to 1
                                victim.register_user_db(role=1)
                                new_role = 1

                            if right == "user" and victim.get_admin_role() < 80:
                                game.rcon_tell(s['player_num'], "" + victim.get_name() + " put in group User")
                                new_role = 1
                            elif right == "regular" and victim.get_admin_role() < 80:
                                game.rcon_tell(s['player_num'], "" + victim.get_name() + " put in group Regular")
                                new_role = 2
                            elif (right == "mod" or right == "moderator") and victim.get_admin_role() < 80:
                                game.rcon_tell(s['player_num'], "" + victim.get_name() + " added as Moderator")
                                new_role = 20
                            elif right == "admin" and victim.get_admin_role() < 80:
                                game.rcon_tell(s['player_num'], "" + victim.get_name() + " added as Admin")
                                new_role = 40
                            elif right == "fulladmin" and victim.get_admin_role() < 80:
                                game.rcon_tell(s['player_num'], "" + victim.get_name() + " added as Full Admin")
                                new_role = 60
                            # Note: senioradmin level can only be set by head admin
                            elif right == "senioradmin" and game.players[s['player_num']].get_admin_role() == 100 and victim.get_player_num() != s['player_num']:
                                game.rcon_tell(s['player_num'], "" + victim.get_name() + " added as ^6Senior Admin")
                                new_role = 80
                            else:
                                game.rcon_tell(s['player_num'], "Sorry, you cannot put " + victim.get_name() + " in group <" + str(right) + ">")

                            # update database and set admin_role
                            values = (new_role, victim.get_guid())
                            curs.execute("UPDATE `xlrstats` SET `admin_role` = ? WHERE `guid` = ?", values)
                            conn.commit()
                            # overwrite admin role in game, no reconnect of player required
                            victim.set_admin_role(new_role)
                    else:
                        game.rcon_tell(s['player_num'], "^7Usage: !putgroup <name> <group>")
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !putgroup <name> <group>")

            # banlist - display the last 6 entries of the banlist
            elif s['command'] == '!banlist' and game.players[s['player_num']].get_admin_role() >= 80:
                curs.execute("SELECT * FROM `ban_list` ORDER BY `id` DESC LIMIT 6")
                result = curs.fetchall()
                msg = ''
                if len(result) > 6:
                    limit = 6
                elif len(result) == 0:
                    limit = 0
                else:
                    limit = len(result)
                for item in range(limit):
                    msg += '[' + str(result[item][0]) + ']' + result[item][2] + ', '  # 0=ID, 2=Name
                if not msg:
                    msg = 'Currently no one is banned'
                game.rcon_tell(s['player_num'], "^7Banlist: %s" % str(msg.rstrip(', ')))

            # unban - unban a player from the database via ID
            elif s['command'] == '!unban' and game.players[s['player_num']].get_admin_role() >= 80:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    if arg.isdigit():
                        values = (int(arg),)
                        curs.execute("DELETE FROM `ban_list` WHERE `id` = ?", values)
                        conn.commit()
                        game.rcon_tell(s['player_num'], "^7Player ID <%s> unbanned" % arg)
                    else:
                        game.rcon_tell(s['player_num'], "^7Usage: !unban <ID>")
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !unban <ID>")

## head admin level 100
            # ungroup - remove the admin level from a player
            elif s['command'] == '!ungroup' and game.players[s['player_num']].get_admin_role() == 100:
                if line.split(s['command'])[1]:
                    arg = str(line.split(s['command'])[1]).strip()
                    count = 0
                    for player in game.players.itervalues():
                        if arg.upper() in (player.get_name()).upper() or arg == str(player.get_player_num()):
                            victim = player
                            count += 1
                    if count == 0:
                        game.rcon_tell(s['player_num'], "No Player found")
                    elif count > 1:
                        game.rcon_tell(s['player_num'], "More than one Player found")
                    else:
                        if 1 < victim.get_admin_role() < 100:
                            game.rcon_tell(s['player_num'], "%s put in group User" % victim.get_name())
                            # update database and set admin_role to 1
                            values = (1, victim.get_guid())
                            curs.execute("UPDATE `xlrstats` SET `admin_role` = ? WHERE `guid` = ?", values)
                            conn.commit()
                            # overwrite admin role in game, no reconnect of player required
                            victim.set_admin_role(1)
                        else:
                            game.rcon_tell(s['player_num'], "Sorry, you cannot put %s in group User" % victim.get_name())
                else:
                    game.rcon_tell(s['player_num'], "^7Usage: !ungroup <name>")

## iamgod
            # iamgod - register user as Head Admin
            elif s['command'] == '!iamgod':
                if self.iamgod:
                    if not game.players[s['player_num']].get_registered_user():
                        # register new user in DB and set admin role to 100
                        game.players[s['player_num']].register_user_db(role=100)
                    else:
                        values = (100, game.players[s['player_num']].get_guid())
                        curs.execute("UPDATE `xlrstats` SET `admin_role` = ? WHERE `guid` = ?", values)
                        conn.commit()
                        # overwrite admin role in game, no reconnect of player required
                        game.players[s['player_num']].set_admin_role(100)
                    game.rcon_tell(s['player_num'], "^7You are registered as ^6Head Admin")

    def handle_flag(self, line):
        """
        handle flag
        """
        tmp = line.split(" ")
        player_num = int(tmp[0].strip())
        action = tmp[1].strip()
        with players_lock:
            player = game.players[player_num]
            if action == '0:':
                player.kill_flag_carrier()
            elif action == '1:':
                player.return_flag()
            elif action == '2:':
                player.capture_flag()

    def handle_misc(self):
        """
        dummy handler
        """
        return

    def handle_awards(self):
        """
        display awards and personal stats at the end of the round
        """
        most_kills = 0
        most_flags = 0
        most_streak = 0
        most_hs = 0
        flagrunner = ""
        serialkiller = ""
        streaker = ""
        headshooter = ""
        msg = ""
        with players_lock:
            for player in game.players.itervalues():
                if player.get_flags_captured() > most_flags:
                    most_flags = player.get_flags_captured()
                    flagrunner = player.get_name()
                if player.get_kills() > most_kills and player.get_name() != 'World':
                    most_kills = player.get_kills()
                    serialkiller = player.get_name()
                if player.get_max_kill_streak() > most_streak and player.get_name() != 'World':
                    most_streak = player.get_max_kill_streak()
                    streaker = player.get_name()
                if player.get_headshots() > most_hs:
                    most_hs = player.get_headshots()
                    headshooter = player.get_name()
            if most_flags > 1:
                msg += "^7%s: ^2%d ^4caps ^7- " % (flagrunner, most_flags)
            if most_kills > 1:
                msg += "^7%s: ^2%d ^3kills" % (serialkiller, most_kills)
            if most_streak > 1:
                msg += " ^7- %s: ^2%d ^6streaks" % (streaker, most_streak)
            if most_hs > 1:
                msg += " ^7- %s: ^2%d ^1heads" % (headshooter, most_hs)
            if msg:
                game.rcon_say("^1AWARDS: %s" % msg)

            # display personal stats at the end of the round
            for player in game.players.itervalues():
                # display personal stats, stats for players in spec will not be displayed
                if player.get_team() != 3:
                    game.rcon_tell(player.get_player_num(), "^7Stats " + player.get_name() + ": ^7K ^2" + str(player.get_kills()) + " ^7D ^3" + str(player.get_deaths()) + " ^7HS ^1" + str(player.get_headshots()) + " ^7TK ^1" + str(player.get_team_killer()))

    def explode_line2(self, line):
        """
        explode line
        """
        line = line.strip()
        try:
            tmp = line.split(" ")
            array = {"player_num": int(tmp[0]), "name": tmp[1], "command": tmp[2]}
        except IndexError:
            array = {"player_num": None, "name": None, "command": None}
        return array

    def error(self, msg):
        """
        error logging
        """
        err_log = open('./error.log', 'a+')
        err_log.write(time.ctime() + "   ---   " + repr(msg) + "\n")
        err_log.close()
        print msg

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
    teams = {0: "green", 1: "red", 2: "blue", 3: "spectators"}
    roles = {0: "Guest", 1: "User", 2: "Regular", 20: "Moderator", 40: "Admin", 60: "Full Admin", 80: "Senior Admin", 100: "Head Admin"}

    def __init__(self, player_num, ip_address, guid, name, team=0):
        """
        create a new instance of Player
        """
        self.player_num = player_num
        self.guid = guid
        self.name = "".join(name.split())
        self.aliases = []
        self.registered_user = False
        self.num_played = 0
        self.last_visit = 0
        self.admin_role = 0
        self.kills = 0
        self.xlr_kills = 0
        self.killing_streak = 0
        self.max_kill_streak = 0
        self.xlr_killing_streak = 0
        self.deaths = 0
        self.xlr_deaths = 0
        self.xlr_suicide = 0
        self.head_shots = 0
        self.xlr_head_shots = 0
        self.all_hits = 0
        self.kill_mate = 0
        self.xlr_kill_mate = 0
        self.xlr_team_death = 0
        self.tk_mate_names = []
        self.high_ping_count = 0
        self.spec_warn_count = 0
        self.warn_counter = 0
        self.flags_captured = 0
        self.flags_returned = 0
        self.flag_carriers_killed = 0
        self.address = ip_address
        self.team = int(team)
        self.team_kills = []
        self.time_joined = time.time()
        self.welcome_msg = True
        self.country = None
        self.banned_player = False

        self.prettyname = "".join(name.split())
        # remove color characters from name
        for item in range(10):
            self.prettyname = self.prettyname.replace('^%d' % item, '')

        # check ban_list
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        values = (self.guid, self.address, now)
        curs.execute("SELECT COUNT(*) FROM `ban_list` WHERE (`guid` = ? OR `ip_address` = ?) AND `expires` > ?", values)
        if curs.fetchone()[0] > 0:
            print("Player " + self.name + " BANNED - GUID: " + str(self.guid) + " - IP ADDRESS: " + str(self.address))
            game.send_rcon("%s ^1banned" % self.name)
            self.banned_player = True

        if not self.banned_player:
            # GeoIP lookup
            info = GEOIP.lookup(ip_address)
            if info.country:
                self.country = info.country_name
                game.rcon_say("%s ^7connected from %s" % (name, info.country_name))

    def ban(self, duration=900, reason='tk'):
        unix_expiration = int(duration) + time.time()
        expire_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(unix_expiration))
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        values = (self.guid, self.prettyname, self.address, expire_date, timestamp, reason)
        curs.execute("INSERT INTO `ban_list` (`guid`,`name`,`ip_address`,`expires`,`timestamp`,`reason`) VALUES (?,?,?,?,?,?)", values)
        conn.commit()
        game.kick_player(self)
        print("BAN: Player " + self.name + " banned for " + reason + ", duration (in sec.): " + str(duration))

    def reset(self):
        self.kills = 0
        self.killing_streak = 0
        self.max_kill_streak = 0
        self.deaths = 0
        self.head_shots = 0
        self.all_hits = 0
        self.kill_mate = 0
        self.tk_mate_names = []
        self.warn_counter = 0
        self.flags_captured = 0
        self.flags_returned = 0
        self.flag_carriers_killed = 0
        self.team_kills = []

    def save_info(self):
        if self.registered_user:
            if self.xlr_deaths == 0:
                ratio = 1.0
            else:
                ratio = round(float(self.xlr_kills) / float(self.xlr_deaths), 2)
            values = (self.xlr_kills, self.xlr_deaths, self.xlr_head_shots, self.xlr_kill_mate, self.xlr_team_death, self.xlr_killing_streak, self.xlr_suicide, ratio, self.guid)
            curs.execute("UPDATE `xlrstats` SET `kills` = ?,`deaths` = ?,`headshots` = ?,`team_kills` = ?,`team_death` = ?,`max_kill_streak` = ?,`suicides` = ?,`rounds` = `rounds` + 1,`ratio` = ? WHERE `guid` = ?", values)
            conn.commit()

    def check_database(self):
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        # check player table
        values = (self.guid,)
        curs.execute("SELECT COUNT(*) FROM `player` WHERE `guid` = ?", values)
        if curs.fetchone()[0] < 1:
            values = (self.guid, self.prettyname, self.address, now, self.prettyname)
            curs.execute("INSERT INTO `player` (`guid`,`name`,`ip_address`,`time_joined`, `aliases`) VALUES (?,?,?,?,?)", values)
            conn.commit()
            self.aliases.append(self.prettyname)
        else:
            values = (self.prettyname, self.address, now, self.guid)
            curs.execute("UPDATE `player` SET `name` = ?,`ip_address` = ?,`time_joined` = ? WHERE `guid` = ?", values)
            conn.commit()
            # get known aliases
            values = (self.guid,)
            curs.execute("SELECT `aliases` FROM `player` WHERE `guid` = ?", values)
            result = curs.fetchone()
            # create list of aliases
            self.aliases = result[0].split(', ')
            if not self.prettyname in self.aliases:
                # add new alias to list
                if len(self.aliases) < 11:
                    self.aliases.append(self.prettyname)
                    alias_string = ', '.join(self.aliases)
                    values = (alias_string, self.guid)
                    curs.execute("UPDATE `player` SET `aliases` = ? WHERE `guid` = ?", values)
                    conn.commit()
        # check XLRSTATS table
        values = (self.guid,)
        curs.execute("SELECT COUNT(*) FROM `xlrstats` WHERE `guid` = ?", values)
        if curs.fetchone()[0] < 1:
            self.registered_user = False
        else:
            self.registered_user = True
            # get DB DATA for XLRSTATS
            values = (self.guid,)
            curs.execute("SELECT `last_played`, `num_played`, `kills`, `deaths`, `headshots`, `team_kills`, `team_death`, `max_kill_streak`,`suicides`, `admin_role` FROM `xlrstats` WHERE `guid` = ?", values)
            result = curs.fetchone()
            self.last_visit = result[0]
            self.num_played = result[1]
            self.xlr_kills = result[2]
            self.xlr_deaths = result[3]
            self.xlr_head_shots = result[4]
            self.xlr_kill_mate = result[5]
            self.xlr_team_death = result[6]
            self.xlr_killing_streak = result[7]
            self.xlr_suicide = result[8]
            self.admin_role = result[9]
            # update name, last_played and increase num_played counter
            values = (self.prettyname, now, self.guid)
            curs.execute("UPDATE `xlrstats` SET `name` = ?,`last_played` = ?,`num_played` = `num_played` + 1 WHERE `guid` = ?", values)
            conn.commit()

    def register_user_db(self, role=1):
        if not self.registered_user:
            now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            values = (self.guid, self.prettyname, self.address, now, now, role)
            curs.execute("INSERT INTO `xlrstats` (`guid`,`name`,`ip_address`,`first_seen`,`last_played`,`num_played`,`admin_role`) VALUES (?,?,?,?,?,1,?)", values)
            conn.commit()
            self.registered_user = True
            self.admin_role = role
            self.welcome_msg = False

    def get_banned_player(self):
        return self.banned_player

    def set_name(self, name):
        self.name = "".join(name.split())

    def get_name(self):
        return self.name

    def get_aliases(self):
        return ", ".join(self.aliases)

    def set_guid(self, guid):
        self.guid = guid

    def get_guid(self):
        return self.guid

    def get_player_num(self):
        return self.player_num

    def set_team(self, team):
        self.team = team

    def get_team(self):
        return self.team

    def get_num_played(self):
        return self.num_played

    def get_last_visit(self):
        return self.last_visit

    def get_xlr_kills(self):
        return self.xlr_kills

    def get_kills(self):
        return self.kills

    def get_xlr_deaths(self):
        return self.xlr_deaths

    def get_deaths(self):
        return self.deaths

    def get_xlr_headshots(self):
        return self.xlr_head_shots

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

    def get_xlr_killing_streak(self):
        return self.xlr_killing_streak

    def get_xlr_suicide(self):
        return self.xlr_suicide

    def kill(self):
        self.killing_streak += 1
        self.kills += 1
        self.xlr_kills += 1

    def die(self):
        if self.killing_streak > self.max_kill_streak:
            self.max_kill_streak = self.killing_streak
        if self.max_kill_streak > self.xlr_killing_streak:
            self.xlr_killing_streak = self.max_kill_streak
        self.killing_streak = 0
        self.deaths += 1
        self.xlr_deaths += 1

    def suicide(self):
        self.xlr_suicide += 1

    def headshot(self):
        self.head_shots += 1
        self.xlr_head_shots += 1

    def set_all_hits(self):
        self.all_hits += 1

    def get_all_hits(self):
        return self.all_hits

    def get_killing_streak(self):
        return self.killing_streak

    def get_xlr_tks(self):
        return self.xlr_kill_mate

    def get_team_killer(self):
        return self.kill_mate

    def add_high_ping(self):
        self.high_ping_count += 1

    def clear_high_ping(self):
        self.high_ping_count = 0

    def get_high_ping(self):
        return self.high_ping_count

    def add_spec_warning(self):
        self.spec_warn_count += 1

    def clear_spec_warning(self):
        self.spec_warn_count = 0

    def get_spec_warning(self):
        return self.spec_warn_count

    def add_warning(self):
        self.warn_counter += 1

    def get_warning(self):
        return self.warn_counter

    def clear_warning(self):
        self.warn_counter = 0
        self.spec_warn_count = 0
        self.team_kills = []
        self.tk_mate_names = []
        # clear ban_points
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        values = (self.guid, now)
        curs.execute("DELETE FROM `ban_points` WHERE `guid` = ? and `expires` > ?", values)
        conn.commit()

    def team_death(self):
        # increase team death counter
        self.xlr_team_death += 1

    def get_xlr_team_death(self):
        return self.xlr_team_death

    def team_kill(self, victim, autokick=True):
        # increase teamkill counter
        self.kill_mate += 1
        self.xlr_kill_mate += 1

        # Regular and higher will not get punished
        if self.admin_role < 2 and autokick:
            # list of names of TK victims
            self.tk_mate_names.append(victim)
            # append timestamp of last TK
            self.team_kills.append(time.time())
            # ban player with too many team kills (min value: 4)
            number_of_max_tk = 5
            # check number of TK entries
            if len(self.team_kills) >= number_of_max_tk:
                tks = self.team_kills[len(self.team_kills) - number_of_max_tk]
                if tks > time.time() - 130:
                    # add TK ban points - 20 minutes
                    self.add_ban_point('tk, auto-kick', 1200)
                    game.kick_player(self)
                    game.rcon_say("^7Player ^3%s ^7kicked for team killing" % self.name)
                    print("KICK: TK autokick for %s" % self.name)
            # slap player for team killing
            elif len(self.team_kills) >= (number_of_max_tk - 1):
                tks = self.team_kills[len(self.team_kills) - (number_of_max_tk - 1)]
                if tks > time.time() - 130:
                    game.send_rcon('slap %d' % self.player_num)
                    game.rcon_say("^1For team killing you will get kicked!")
            # warn player for team killing
            elif len(self.team_kills) >= (number_of_max_tk - 3):
                tks = self.team_kills[len(self.team_kills) - (number_of_max_tk - 3)]
                if tks > time.time() - 130:
                    game.rcon_tell(self.player_num, "^1For team killing you will get kicked!")

    def add_ban_point(self, point_type, duration):
        point_type = str(point_type)
        unix_expiration = int(duration) + time.time()
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
            game.rcon_say("%s ^7banned for ^1%d minutes ^7for too many warnings" % (self.name, (ban_duration / 60)))

# CTF Mode
    def capture_flag(self):
        self.flags_captured += 1

    def get_flags_captured(self):
        return self.flags_captured

    def return_flag(self):
        self.flags_returned += 1

    def get_flags_returned(self):
        return self.flags_returned

    def kill_flag_carrier(self):
        self.flag_carriers_killed += 1

    def get_flag_carriers_killed(self):
        return self.flag_carriers_killed


### CLASS Game ###
class Game(object):
    """
    Game class
    """
    def __init__(self):
        """
        create a new instance of Game
        """
        self.rcon_queue = Queue()
        self.players = {}
        self.live = False
        self.rcon_lock = RLock()
        self.rcon_handle = Rcon(CONFIG.get('server', 'server_ip'), CONFIG.get('server', 'server_port'), CONFIG.get('server', 'rcon_password'))
        if CONFIG.get('rules', 'show_rules') == '1':
            # create instance of Rules to display the rules and advertisements
            Rules('./conf/rules.conf', int(CONFIG.get('rules', 'rules_frequency')), self.rcon_handle)

    def send_rcon(self, command):
        """
        send RCON command

        @param command: The RCON command
        @type  command: String
        """
        with self.rcon_lock:
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

    def kick_player(self, player):
        """
        kick player

        @param player: The instance of the player
        @type  player: Instance
        """
        with players_lock:
            self.send_rcon('kick %d' % player.get_player_num())

    def go_live(self):
        """
        go live
        """
        self.live = True
        self.rcon_handle.go_live()

    def add_player(self, player):
        """
        add a player to the game

        @param player: The instance of the player
        @type  player: Instance
        """
        with players_lock:
            self.players[player.get_player_num()] = player
            player.check_database()

    def get_gamestats(self):
        """
        get number of players in red team, blue team and spectator
        """
        with players_lock:
            game_data = {Player.teams[1]: 0, Player.teams[2]: 0, Player.teams[3]: 0}
            for player in self.players.itervalues():
                # red team
                if player.get_team() == 1:
                    game_data[Player.teams[1]] += 1
                # blue team
                elif player.get_team() == 2:
                    game_data[Player.teams[2]] += 1
                # spectators
                elif player.get_team() == 3:
                    game_data[Player.teams[3]] += 1
            return game_data

    def balance_teams(self):
        """
        balance teams if needed
        """
        game_data = self.get_gamestats()
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
        p_list = []

        def cmp_ab(p1, p2):
            if p1.get_time_joined() < p2.get_time_joined():
                return 1
            elif p1.get_time_joined() == p2.get_time_joined():
                return 0
            else:
                return -1
        with players_lock:
            for player in self.players.itervalues():
                if player.get_team() == team1:
                    p_list.append(player)
            p_list.sort(cmp_ab)
            for player in p_list[:int(num_ptm)]:
                self.rcon_forceteam(player.get_player_num(), Player.teams[team2])
        self.rcon_say("^7Autobalance complete!")

    def new_game(self):
        """
        set-up a new game, set gravity according to config file
        """
        gravity = CONFIG.get('bot', 'gravity')
        self.rcon_handle.clear()
        self.rcon_handle.push("set g_gravity %s" % gravity)


### Main ###

# read settings.conf file
CONFIG = ConfigParser()
CONFIG.read('./conf/settings.conf')

players_lock = RLock()

# connect to database
conn = sqlite3.connect('./data.sqlite')
curs = conn.cursor()

# create instance of LogParser
LOGPARS = LogParser(CONFIG.get('server', 'log_file'), CONFIG.get('bot', 'verbose'), CONFIG.get('bot', 'teamkill_autokick'), CONFIG.get('bot', 'iamgod'))

# load the GEO database and store it globally in interpreter memory
GEOIP = PyGeoIP.Database('./lib/GeoIP.dat')

# create instance of Game
game = Game()

WORLD = Player(1022, '127.0.0.1', 'NONE', 'World', 3)
game.add_player(WORLD)

# create instance of TaskManager
TaskManager(int(CONFIG.get('bot', 'task_frequency')), int(CONFIG.get('bot', 'max_ping')), game.rcon_handle)

# read the logfile
LOGPARS.read_log()

# close database connection
conn.close()
