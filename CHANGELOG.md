# Changelog
All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.11.0] - 2018-08-06
### Added
* Added command `!banall <pattern>` to ban all players matching pattern
* Added command `!rebuild` to sync up all available maps
* Added option to kill spawnkillers instantly
* Added support for Urban Terror 4.3.4

### Changed
* Command `!maps` is showing the total number of available maps
* Exclude bots from autokick for team kills to avoid unbalanced teams
* Exclude bots from autokick of low score players to avoid unbalanced teams
* Updated schedule library
* Improved some feedback messages

### Fixed
* Fixed #55: Make bots immune from spawnkill autokick
* Fixed #56: Command `!maps` does not show all maps
* Fixed #57: Fix year 2038 problem on 32-bit systems
* Fixed version check, issued by string compare
* Various minor bug fixes


## [1.10.0] - 2018-05-31
### Added
* Added option for automatic expiration of warnings
* Added option to kick players for using bad words
* Added option to display multi-kill messages
* Added option "free" to release lock from forced team
* Added option to define ban duration for command `!ban`
* Added command `!grudge [<name>]` to grudge a player for team killing
* Added command `!gear` to set allowed weapons
* Added command `!forgiveclear <name>` to clear player team kills
* Added command `!forgiveinfo <name>` to display a players team kills
* Added command `!forgivelist` to list players who killed you
* Added command `!forgive [<name>]` to forgive team kills
* Added command `!regulars` to display regular players online
* Added command `!unreg <name>` to remove player from regular group
* Added commands to change the gametype
* Added support for old <ut_name> map names
* Added support for latest Urban Terror 4.3.3 release
* Added support for ioquake3 binary
* Added support for macOS 10.13 and Ubuntu 18.04
* Added reason 'score' to reason dictionary
* Added "Top Objectives" awards for CTF and Bomb mode

### Changed
* Do not show forgive notice for grudged players
* Clear team kills for command `!warnclear`  and `!clear`
* Clear warnings if already expired
* Command `!warninfo` shows now all active warnings
* Command `!swap` moves admin using command if playerB is not given
* Command `!tempban` supports now up 1 sec to 3 days periods
* Show msg "Planted?" when bomb explodes
* Introduced detonation time for bomb mode
* Imported latest GeoIP database (April 2018)
* Unified warn system: warnings + team kills are now combined
* Converted loopback/localhost to 127.0.0.1

### Fixed
* Fixed #50: Improve parsing rotation messages file
* Fixed #49: Ban directly for 15 mins
* Fixed #48: Extend max tempban duration to 3 days
* Fixed #47: Show last maps only for nextmap/map votes
* Fixed #46: Add commands to change the gametype
* Fixed #15: Add command `!grudge [<name>]` to grudge a player for team killing
* Various minor bug fixes


## [1.9.0] - 2017-05-14
### Added
* Added Monster Kill counter
* Added group Super Admins (level 90) with same rights as Head admins
* Added option to kill all opponents when bomb exploded or is defused
* Added option to autokick spawn killers
* Added option to limit successful nextmap votes
* Added option to enable/disable sending heartbeat
* Added option to display rule as chat/bigtext/server message
* Added UrT bot support with commands `!bots on/off` and `!addbots`
* Added support for `@bigtext MESSAGE` in rotation messages
* Added command `!lastmaps` to list the last played maps
* Added command `!kickall <pattern>` to kick players matching pattern
* Added command `!restart` to perform a restart of the map
* Added command `!status` to report the status of the bot
* Added command `!id <name>` to show IP, guid and auth of player
* Added command `!tell <name>` to tell a msg to a specific player
* Added command `!afk <name>` to force an afk player to spec
* Added command `!spec` to move yourself to spectator
* Added command `!exit` to display last disconnected player
* Added command `!kickbots` to kick all bots
* Added command option `@locate <name>`
* Added shortcut `!lc` for command `!locate`
* Added public welcome message
* Added help for each command, e.g. `!help tempban`
* Added handler for callvote and vote_passed
* Added systemd service and sysVinit file
* Added support for Debian 9 Stretch and Ubuntu 16.10

### Changed
* Show team mates that bomb was tossed or collected
* Show number of players in each team when using command `!teams`
* Show number of kills when killspree is ended
* Show bomb planted/defused server message
* Show survivor winning team server message
* Show ban reason when banned player tries to connect
* Show nextmap at map begin in dynamic cycle
* Show authname in welcome message
* Improved displaying country for bots or in local LAN
* Improved message "bomb has been planted"
* Reset warn-timer when clearing all warnings
* Extended reason dictionary with sk, wh, insult, autojoin, 999
* Allowed configuration of RCON_DELAY
* Allowed port 1024 again (many latin players use it)
* Imported latest GeoIP database

### Fixed
* Fixed issue #43: added command `!exit` to display last disconnected player
* Fixed issue #42: added support for `@bigtext MESSAGE` in rotation messages
* Fixed issue #41: added bot support
* Fixed issue #40: added support for command `!instagib on/off`
* Fixed issue #39: added support for DB ID and authname for command `!xlrstats`
* Fixed issue #37: added group Super Admins (level 90)
* Fixed issue #32: limit length of name to 20 characters
* Various minor bug fixes


## [1.8.0] - 2016-10-23
### Added
* Added support of bot commands in rotating messages: `@admins`, `@nextmap` and `@time`
* Added command `!rain <on/off>` to enable/disable raindrops in maps
* Added command `!exec <file>` to execute the given scriptfile
* Added command `!reload` to reload the map
* Added command `!password [<password>]` to set or remove a private server password
* Added support to find players by their auth-name
* Added additional debug logging and display server CVARs

### Changed
* Reworked Rules/Rotation Messages class
* Reworked RCON class
* Improved debug messages
* Imported latest GeoIP database

### Fixed
* Fixed issue #33: avoid output of duplicate messages
* Fixed issue #34: catch python exception
* Fixed debug output of gamelog path
* Various minor bug fixes


## [1.7.0] - 2016-10-02
### Added
* Added full support for Urban Terror release 4.3
* Added command `!locate` to display geolocation info of a player
* Added first knife kill message
* Added more warning reasons

### Changed
* Improved some feedback messages
* Imported latest GeoIP database


## [1.6.0] - 2016-04-03
### Added
* Added option to display headshot hit series
* Added option to display nade kill series
* Added option to display knife kill series
* Added command `!knife` to display number of knife kills
* Added most knife kills to Awards output
* Added output of message 'added to group'
* Added output of capture count as server msg in CTF mode
* Added PyPi support

### Changed
* Consolidated warnings in one list
* Improved error message for missing games.log file
* Imported latest GeoIP database
* Performance improvements

### Fixed
* Fixed #31: tell command suppports all player numbers
* Fixed chat message issue with single "!" content
* Fixed possible loop if games.log file is empty
* Fixed missing reason in database for command `!tb`
* Fixed missing text color setup
* Various minor bug fixes


[Unreleased]: https://github.com/SpunkyBot/spunkybot/compare/1.11.0...develop
[1.11.0]: https://github.com/SpunkyBot/spunkybot/compare/1.10.0...1.11.0
[1.10.0]: https://github.com/SpunkyBot/spunkybot/compare/1.9.0...1.10.0
[1.9.0]: https://github.com/SpunkyBot/spunkybot/compare/1.8.0...1.9.0
[1.8.0]: https://github.com/SpunkyBot/spunkybot/compare/1.7.0...1.8.0
[1.7.0]: https://github.com/SpunkyBot/spunkybot/compare/1.6.0...1.7.0
[1.6.0]: https://github.com/SpunkyBot/spunkybot/compare/1.5.0...1.6.0
