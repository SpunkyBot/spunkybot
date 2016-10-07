# Spunky Bot

## Admin Levels and Bot Commands

### Guest [0]

- **help** - display all available commands
	- Usage: `!help`
	- Short: `!h`
- **forgiveprev** - forgive last team kill
	- Usage: `!forgiveprev`
	- Short: `!fp`
- **forgiveall** - forgive all team kills
	- Usage: `!forgiveall`
	- Short: `!fa`
- **hs** - display headshot counter
	- Usage: `!hs`
- **register** - register yourself as a basic user
	- Usage: `!register`
- **spree** - display current kill streak
	- Usage: `!spree`
- **stats** - display current map stats
	- Usage: `!stats`
- **bombstats** - display bomb stats
	- Usage: `!bombstats`
- **ctfstats** - display Capture the Flag stats
	- Usage: `!ctfstats`
- **freezestats** - display freeze/thawout stats
	- Usage: `!freezestats`
- **hestats** - display HE grenade kill stats
	- Usage: `!hestats`
- **knife** - display knife kill stats
	- Usage: `!knife`
- **hits** - display hit stats
	- Usage: `!hits`
- **teams** - balance teams
	- Usage: `!teams`
- **time** - display the current server time
	- Usage: `!time`


### User [1]

- **regtest** - regtest - display current user status
	- Usage: `!regtest`
- **xlrstats** - display full player statistics
	- Usage: `!xlrstats [<name>]`
- **xlrtopstats** - display the top players
	- Usage: `!xlrtopstats`
	- Short: `!topstats`


### Moderator [20]

- **admintest** - display current admin status
	- Usage: `!admintest`
- **country** - get the country of the player
	- Usage: `!country <name>`
- **leveltest** - get the admin level for a given player or myself
	- Usage: `!leveltest [<name>]`
	- Short: `!lt [<name>]`
- **list** - list all connected players
	- Usage: `!list`
- **locate** - display geolocation info of the player
	- Usage: `!locate <name>`
- **nextmap** - display the next map in rotation
	- Usage: `!nextmap`
- **mute** - mute or unmute a player
	- Usage: `!mute <name> [<seconds>]`
- **poke** - notify a player that he needs to move
	- Usage: `!poke <name>`
- **seen** - display when the player was last seen
	- Usage: `!seen <name>`
- **shuffleteams** - shuffle the teams
	- Usage: `!shuffleteams`
	- Short: `!shuffle`
- **warn** - warn user
	- Usage: `!warn <name> [<reason>]`
	- Short: `!w <name> [<reason>]`
	- Available short form reasons: _tk_, _obj_, _spec_, _ping_, _spam_, _camp_, _lang_,  _racism_, _name_, _skill_, _whiner_
- **warninfo** - display how many warnings the player has
	- Usage: `!warninfo <name>`
	- Short: `!wi <name>`
- **warnremove** - remove a users last warning
	- Usage: `!warnremove <name>`
	- Short: `!wr <name>`
- **warns** - list the warnings
	- Usage: `!warns`
- **warntest** -  test a warning
	- Usage: `!warntest <warning>`


### Admin [40]

- **admins** - list all the online admins
	- Usage: `!admins`
- **aliases** - list the aliases of the player
	- Usage: `!aliases <name>`
	- Short: `!alias <name>`
- **bigtext** - display big message on screen
	- Usage: `!bigtext <text>`
- **say** - say a message to all players (allow spectator to say a message to players in-game)
	- Usage: `!say <text>`
	- Short: `!!<text>`
- **find** - display the slot number of the player
	- Usage: `!find <name>`
- **force** - force a player to the given team
	- Usage: `!force <name> <blue/red/spec> [<lock>]`
- **nuke** - nuke a player
	- Usage: `!nuke <name>`
- **kick** - kick a player
	- Usage: `!kick <name> <reason>`
	- Short: `!k <name> <reason>`
- **warnclear** - clear the user warnings
	- Usage: `!warnclear <name>`
	- Short: `!wc <name>`
- **tempban** - ban a player temporary for the given period (1 min to 24 hrs)
	-  Usage: `!tempban <name> <duration> [<reason>]`
	-  Short: `!tb <name> <duration> [<reason>]`
	-  Max ban duration: 24 hours


### Full Admin [60]

- **scream** - scream a message in different colors to all players
	- Usage: `!scream <text>`
- **slap** - slap a player (a number of times)
	- Usage: `!slap <name> [<amount>]`
	- Default amount: 1
	- Max amount: 15
- **swap** - swap teams for player A and B (if in different teams)
	- Usage: `!swap <playerA> <playerB>`
- **version** - display the version of the bot
	- Usage: `!version`
- **veto** - stop voting process
	- Usage: `!veto`
- **ci** - kick player with connection interrupt
	- Usage: `!ci <name>`
- **ban** - ban a player for 7 days
	- Usage: `!ban <name> <reason>`
- **baninfo** - display active bans of a player
	- Usage: `!baninfo <name>`
	- Short: `!bi <name>`


### Senior Admin [80]

- **banlist** - display the last active 10 bans
	- Usage: `!banlist`
- **cyclemap** - start next map in rotation
	- Usage: `!cyclemap`
- **exec** - execute given config file
	- Usage: `!exec <filename>`
- **kiss** - clear all player warnings
	- Usage: `!kiss`
- **kill** - kill a player
	- Usage: `!kill <name>`
- **lastbans** - list the last 4 bans
	- Usage: `!lastbans`
	- Short: `!bans`
- **lookup** - search for player in database
	- Usage: `!lookup <name>`
	- Short: `!l <name>`
- **makereg** - make a player a regular (Level 2) user
	- Usage: `!makereg <name>`
	- Short: `!mr <name>`
- **map** - load given map
	- Usage: `!map <ut4_name>`
- **maps** - display all available maps
	- Usage: `!maps
- **maprestart** - restart the map
	- Usage: `!maprestart`
- **moon** - activate Moon mode (low gravity)
	- Usage: `!moon <on/off>`
- **permban** - ban a player permanent
	- Usage: `!permban <name> <reason>`
	- Short: `!pb <name> <reason>`
- **putgroup** - add a client to a group
	- Usage: `!putgroup <name> <group>`
	- Available Groups: _user_, _regular_, _mod_, _admin_, _fulladmin_
- **setnextmap** - set the given map as nextmap
	- Usage: `!setnextmap <ut4_name>`
- **swapteams** - swap the current teams
	- Usage: `!swapteams`
- **unban** - unban a player from the database
	- Usage: `!unban <ID>`


### Head Admin [100]

- **putgroup** - add a client to a group
	- Usage: `!putgroup <name> <group>`
	- Available Groups: _user_, _regular_, _mod_, _admin_, _fulladmin_, _senioradmin_
- **ungroup** - remove admin level from a player
	- Usage: `!ungroup <name>`