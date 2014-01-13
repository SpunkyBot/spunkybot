# Spunky Bot

**Spunky Bot** is a lightweight game server administration bot and RCON tool.
Its purpose is to administrate an [Urban Terror](http://www.urbanterror.info) 4.1 / 4.2 server and provide statistical data for players.
The code of the Spunky Bot is inspired by the eb2k9 bot by Shawn Haggard, which was released under the Beerware License.

[![Build Status](https://travis-ci.org/urthub/spunkybot.png?branch=master)](https://travis-ci.org/urthub/spunkybot)


## Features

- Lightweight and fast
- Real Time game statistics
- Different user groups and levels
- Supports all RCON commands
- Supports temporary and permanent bans
- No other software requirements
- Runs 'out of the box' 

## Environment
- Urban Terror 4.1.1 and 4.2.017
- Python 2.6.x / 2.7.x
- SQLite 3 database
- Linux platform (tested on Debian 6 & 7 and CentOS 6)
- Support of 32-bit and 64-bit Linux system 


## Resources
* [Documentation](https://github.com/urthub/spunkybot/wiki)
* [Bug Tracker](https://github.com/urthub/spunkybot/issues)
* [Code](https://github.com/urthub/spunkybot)
* [Homepage](http://www.spunkybot.de)


## Configuration
- Modify the Urban Terror server config file as follows:
	- `seta g_logsync "1"`
	- `seta g_loghits "1"`
- The Spunky Bot settings are configured in the file `/conf/settings.conf`
- In-game displayed rules/advertisements are contained in the file `/conf/rules.conf`
	- If you do not want to display rules, set the value `show_rules=0` in the config file `/conf/settings.conf`
- Run the bot manually: `python spunky.py`
- Or use the provided initscript to run the Spunky Bot as daemon

**_First start instruction:_**

- Connect to your game server and type `!iamgod` in global chat to get the admin level "Head Admin". This command is only once available.


### Bot Commands
The description of all available commands as well as the admin levels and rights are located under the subfolder `/doc`.


## License
The Spunky Bot is released under the MIT License.


### Third Party Libraries
 - RCON: [pyquake3.py](https://github.com/urthub/pyquake3)
	- The library has been modified to fix some error handling issues and fulfill the PEP8 conformance. This file is released under the GNU General Public License.
 - GeoIP: [pygeoip.py](https://github.com/urthub/pygeoip)
	- The library has been extended with the list `GeoIP_country_name` to support full country names (e.g. Germany for country_code DE). This file is released under the MIT License.

Urban Terror™ and FrozenSand™ are trademarks of 0870760 B.C. Ltd.
