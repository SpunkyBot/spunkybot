This README is just a quick start document. You can find more detailed documentation of Spunky Bot at [https://spunkybot.de](https://spunkybot.de).

# What is Spunky Bot?

**Spunky Bot** is a lightweight game server administration bot and RCON tool.
Its purpose is to administer, manage and maintain an [Urban Terror](http://www.urbanterror.info) 4.1 / 4.2 / 4.3 server and to provide real time statistics data for players.
Spunky Bot is a cross-platform package and offers in-game commands without authentication and automated administration even when no admin is online.
The code of Spunky Bot is inspired by the eb2k9 bot by Shawn Haggard, which was released under the Beerware License.

[![Build Status](https://travis-ci.org/SpunkyBot/spunkybot.png)](https://travis-ci.org/SpunkyBot/spunkybot)
[![Actions Status](https://github.com/SpunkyBot/spunkybot/workflows/CI/badge.svg)](https://github.com/SpunkyBot/spunkybot/actions)
[![License](https://img.shields.io/github/license/SpunkyBot/spunkybot)](https://github.com/SpunkyBot/spunkybot/blob/develop/LICENSE)
[![Release](https://img.shields.io/github/v/release/SpunkyBot/spunkybot.svg?color=orange)](https://github.com/SpunkyBot/spunkybot/releases)
[![PyPI version](https://img.shields.io/pypi/v/spunkybot.svg)](https://pypi.python.org/pypi/spunkybot)
[![Python version](https://img.shields.io/pypi/pyversions/spunkybot?color=yellow)](https://pypi.org/project/spunkybot)
[![GitHub Downloads](https://img.shields.io/github/downloads/SpunkyBot/spunkybot/total?color=yellowgreen)](https://github.com/SpunkyBot/spunkybot/releases)

If you want to know more, this is a list of selected starting points:

* Introduction to [Spunky Bot](https://spunkybot.de)
* The full list of [commands](https://spunkybot.de/docs/commands)
* There is much more inside the [official documentation](https://docs.spunkybot.de)

## Features

* Lightweight and fast
* Real time game statistics
* Different user groups and levels
* Supports all RCON commands
* Supports temporary and permanent bans of players
* Supports rotation messages
* Stores all player related information in a SQLite database
* Runs 'out of the box', no other software requirements

## Environment

* Urban Terror 4.1.1 / 4.2.023 / 4.3.4
* Python 2.6 / 2.7
* SQLite 3 database
* Cross-platform (tested on Debian 6 - 10, Ubuntu 10.04 - 20.04, CentOS 6 / 7, macOS 10.13, Windows 7 / 10)
* Supporting 32-bit and 64-bit operating systems

## Quickstart

It's easy to get started with Spunky Bot:

* Download the [latest release](https://spunkybot.de/download)
* Read our [quickstart guide](https://spunkybot.de/docs/start) to get up and running

### Configuration

* Modify the Urban Terror server config file as follows:

```
seta g_logsync "1"
seta g_loghits "1"
seta g_friendlyfire "2"
```

* Restart your Urban Terror server
* Modify the Spunky Bot configuration file `/conf/settings.conf` and set game server port and RCON password
* In-game displayed rules/advertisements are contained in the file `/conf/rules.conf`
* If you do not want to display the rotation messages, set the value `show_rules=0` in the config file `/conf/settings.conf`
* Run the application manually: `python spunky.py`
* Or use the provided systemd or sysVinit script to run Spunky Bot as daemon

**_First start instruction:_**

* Connect to your game server and type `!iamgod` in the global chat to get the admin level "Head Admin". This command is only once available.

## Documentation

You can find all details in the latest [documentation](https://docs.spunkybot.de).

### Bot Commands

The description of all available [commands](https://github.com/SpunkyBot/spunkybot/blob/develop/doc/Commands.md) as well as the admin levels and rights is located under the subfolder `/doc`.

## Resources

* [Documentation](https://docs.spunkybot.de)
* [Bug Tracker](https://github.com/SpunkyBot/spunkybot/issues)
* [Mailing List](https://groups.google.com/group/spunkybot)
* [Source Code](https://github.com/SpunkyBot/spunkybot)
* [Homepage](https://spunkybot.de)

## Changelog

You can keep up-to-date with the changes that we have made via our [releases page](https://github.com/Spunkybot/spunkybot/releases).

## Versioning

Spunky Bot is currently maintained under the [Semantic Versioning](http://semver.org) guidelines. Releases will be numbered with the following format: `<major>.<minor>.<patch>`

## Additional Information

For additional information, visit the Spunky Bot website at [https://www.spunkybot.de](https://www.spunkybot.de).

If you have any questions about Spunky Bot or need help, please use the [mailing list](https://groups.google.com/group/spunkybot).

* Joining the mailing list:
  * Send an email to <mailto:spunkybot+subscribe@googlegroups.com>
  * or subscribe via web: [https://groups.google.com/forum/#!forum/spunkybot/join](https://groups.google.com/forum/#!forum/spunkybot/join)
* Leaving the mailing list:
  * Send an email to <mailto:spunkybot+unsubscribe@googlegroups.com>
  * or unsubscribe via web: [https://groups.google.com/forum/#!forum/spunkybot/unsubscribe](https://groups.google.com/forum/#!forum/spunkybot/unsubscribe)
* If you joined the group, you can post to this group:
  * Send an email to spunkybot@googlegroups.com

If you have bug reports or feature suggestions, please use the [issue tracker](https://github.com/SpunkyBot/spunkybot/issues?state=open).

## Contributing

You can help us in different ways:

* Open an [issue](https://github.com/SpunkyBot/spunkybot/issues) with suggestions for improvements
* Fork this repository and submit a pull request:
  * Click the Fork button to create your personal fork
  * Create your feature branch (`git checkout -b new-feature`)
  * Commit your changes (`git commit -am 'Add some feature'`)
  * Push to the branch (`git push origin new-feature`)
  * Create a new pull request
* Improve the [documentation](https://github.com/SpunkyBot/spunkybot-docs) (separate repository)

By contributing code to this project in any form, including sending a pull request via GitHub, a code fragment or patch via mail or public discussion groups, you agree to release your code under the terms of the MIT license that you can find in the [LICENSE](https://github.com/SpunkyBot/spunkybot/blob/develop/LICENSE) file included in this source distribution.

Please see the [CONTRIBUTING](https://github.com/SpunkyBot/spunkybot/blob/develop/.github/CONTRIBUTING.md) guide for information regarding the contribution process.

## License

The code of Spunky Bot is released under the MIT License. See the [LICENSE](https://github.com/SpunkyBot/spunkybot/blob/develop/LICENSE) file for the full license text.

### Third Party Libraries

* RCON: [pyquake3.py](https://github.com/urthub/pyquake3)
  * The library has been modified to fix some error handling issues and fulfill the PEP8 conformance. This file is released under the GNU General Public License.
* GeoIP: [pygeoip.py](https://github.com/urthub/pygeoip)
  * The library has been extended with the list `GeoIP_country_name` to support full country names (e.g. Germany for country_code DE). This file is released under the MIT License.
* GeoLite database: [www.maxmind.com](http://www.maxmind.com)
  * The GeoLite databases created by MaxMind are distributed under the Creative Commons Attribution-ShareAlike 4.0 International License and the MaxMind Open Data License.
* Schedule: [schedule.py](https://github.com/dbader/schedule)
  * This file is released under the MIT License.

Urban Terror® and FrozenSand™ are trademarks, or registered trademarks of Frozensand Games Limited.

## Thank you!

We really appreciate all kinds of feedback and contributions. Thanks for using and supporting Spunky Bot!
