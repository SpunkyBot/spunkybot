#!/usr/bin/env python

import sys
import re

try:
    from setuptools import setup, find_packages
except ImportError:
    print('Spunky Bot needs setuptools in order to build. Install it using'
          ' your package manager (usually python-setuptools) or via pip (pip'
          ' install setuptools).')
    sys.exit(1)

if sys.version_info < (2, 6):
    raise NotImplementedError('Sorry, you need at least Python 2.6.')

metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", open('spunky.py').read()))

long_description = """Overview
========
`Spunky Bot`_ is a lightweight game server administration bot and RCON tool.
Its purpose is to administer, manage and maintain an `Urban Terror`_ server and
to provide real time statistics data for players.

Spunky Bot is a cross-platform package and offers in-game commands without
authentication and automated administration even when no admin is online.

Your gameserver can be enhanced with the ultimate administration power that
Spunky Bot brings! The all-in-one server administration bot for Urban Terror
gives admins the power to easily manage and administrate their server.
It allows players access to statistics and gives powerful options to manage
the flow of a game.

Spunky Bot is free and open source, released under the MIT_ license.
There are no software requirements, Spunky Bot is running "out of the box".
The installation is just click and go. There is no need to install a heavy
MySQL database, SQLite is used to boost up the performance and to reduce the
memory footprint.

Features
========
* Lightweight and fast
* Real time game statistics
* Different user groups and levels
* Supports all RCON commands
* Supports temporary and permanent bans of players
* Supports rotation messages

Installation
============
::

    pip install spunkybot


See the Homepage_ for usage and documentation or visit the Git Repository_
for the source code.

.. _Spunky Bot: https://spunkybot.de/
.. _Urban Terror: http://www.urbanterror.info/
.. _MIT: https://opensource.org/licenses/MIT
.. _Homepage: https://spunkybot.de/
.. _Repository: https://github.com/SpunkyBot/spunkybot/
"""

setup(name='spunkybot',
      version=metadata['version'],
      description='An automated game server bot and RCON tool for Urban Terror',
      long_description=long_description,
      author='Alexander Kress',
      author_email='feedback@spunkybot.de',
      url='https://spunkybot.de/',
      keywords='Urban Terror Game Administration RCON Bot',
      download_url='https://github.com/SpunkyBot/spunkybot/releases/latest',
      license='MIT',
      install_requires=['setuptools'],
      py_modules=['spunky'],
      package_dir={'conf': 'conf', 'lib': 'lib'},
      packages=find_packages(exclude=['tests']),
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: MIT License',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: System :: Logging',
          'Topic :: System :: Monitoring',
          'Topic :: System :: Systems Administration',
          'Topic :: Games/Entertainment',
          'Topic :: Utilities',
      ],
      data_files=[('', ['debian-startscript', 'systemd-spunkybot.service', 'README.md', 'LICENSE']),
                  ('lib', ['lib/GeoIP.dat'])],
      )
