# Spunky Bot - game server bot

**Spunky Bot** is a lightweight game server administration bot and RCON tool.
Its purpose is to administrate an Urban Terror 4.1 server and provide statistical data for players.
The source code of the Spunky Bot is inspired by the eb2k9 bot by Shawn Haggard, which was released under the Beerware License.


### Bot Commands
The description of all available commands as well as the admin levels and rights are located under the subfolder `/doc`.


### Environment
- Python 2.7.x
- SQLite 3 database
- Linux platform (tested on Debian Wheezy 32-bit)
- Urban Terror 4.1.1


### Configuration
- Modify the Urban Terror server config file as follows:
	- `seta g_logsync "1"`
	- `seta g_loghits "1"`
- The Spunky Bot settings are configured in the file `/conf/settings.conf`
- In-game displayed rules are contained in the file `/conf/rules.conf`
	- If you do not want to display rules, set the value `show_rules=0` in the file `/conf/settings.conf`
- Run the bot: `python spunky.py`

**_First start instruction:_**

- Set in the config file `/conf/settings.conf` the value `iamgod=1`
- Start the Bot, connect to your game server and enter in the global chat `!iamgod`. This will give you the admin level "Admin Head".
- Afterwards set the value `iamgod=0` and restart the Bot (important step!)


### License
The Spunky Bot is released under the MIT License.


### Third Party Libraries
 - RCON: [pyquake3.py](https://github.com/urthub/pyquake3)
	- The library has been modified to fix some error handling issues and fulfill the PEP8 conformance. This file is released under the GNU General Public License.
 - GeoIP: [pygeoip.py](https://github.com/urthub/pygeoip)
	- The library has been extended with the list `GeoIP_country_name` to support full country names (e.g. Germany for country_code DE). This file is released under the MIT License.