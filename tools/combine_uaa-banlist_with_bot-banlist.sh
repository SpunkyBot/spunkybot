#!/bin/bash

# download latest UAA network banlist
wget http://www.urtadmins.net/banlist/UAA-banlist-aimbot-only_for-use-without-b3.txt -O /opt/urbanterror/.q3a/q3ut4/uaa-banlist.txt

# merge UAA and Spunky Bot banlist, duplicated entries will be removed
cat /opt/urbanterror/.q3a/q3ut4/spunky-bot/bot-banlist.txt /opt/urbanterror/.q3a/q3ut4/uaa-banlist.txt | uniq > /opt/urbanterror/.q3a/q3ut4/banlist.txt

exit 0
