# Spunky Bot

## Admin Levels and Rights

### Guest [0]

- **help** - display all available commands
	- Usage: `!help`
	- Short: `!h`
- **hs** - display headshot counter
	- Usage: `!hs`
- **register** - register yourself as a basic user
	- Usage: `!register`
- **stats** - display current map stats
	- Usage: `!stats`
- **teams** - balance teams
	- Usage: `!teams`
- **time** - display the current server time
	- Usage: `!time`


### User [1]
- **xlrstats** - display full player statistics
	- Usage: `!xlrstats [<name>]`


### Moderator [20]

- **country** - get the country of the player
	- Usage: `!country <name>`
- **leveltest** - get the admin level for a given player or myself
	- Usage: `!leveltest [<name>]`
	- Short: `!lt [<name>]`
- **list** - list all connected players
	- Usage: `!list`
- **mute** - mute or unmute a player
	- Usage: `!mute <name>`
- **shuffleteams** - shuffle the teams
	- Usage: `!shuffleteams`
	- Short: `!shuffle`
- **warn** - warn user
	- Usage: `!warn <name> <reason>`
	- Short: `!w <name> <reason>`
	- Available short form reasons: _tk_, _obj_, _spec_, _ping_, _spam_, _camp_, _lang_,  _racism_


### Admin [40]

- **admins** - list all the online admins
	- Usage: `!admins`
- **aliases** - list the aliases of the player
	- Usage: `!aliases <name>`
	- Short: `!alias <name>`
- **bigtext** - display big message on screen
	- Usage: `!bigtext <text>`
- **say** - say a message to all players
	- Usage: `!say <text>`
- **force** - force a player to the given team
	- Usage: `!force <name> <blue/red/spec>`
- **nuke** - nuke a player
	- Usage: `!nuke <name>`
- **kick** - kick a player
	- Usage: `!kick <name> <reason>`
	- Short: `!k <name> <reason>`
- **warnclear** - clear the user warnings
	- Usage: `!warnclear <name>`
	- Short: `!wc <name>`
- **tempban** - ban a player temporary for given period in hours
	-  Usage: `!tempban <name> <reason> [<duration in hours>]`
	-  Short: `!tb <name> <reason> [<duration in hours>]`
	-  Default ban duration: 1 hour
	-  Max ban duration: 24 hours


### Full Admin [60]

- **scream** - scream a message in different colors to all players
	- Usage: `!scream <text>`
- **slap** - slap a player (a number of times)
	- Usage: `!slap <name> [<amount>]`
	- Default amount: 1
	- Max amount: 10
	- Alternative: `!spank <name> [<amount>]`
- **veto** - stop voting process
	- Usage: `!veto`
- **afk** - kick player who is away from keyboard
	- Usage: `!afk <name>`
- **ci** - kick player with connection interrupt
	- Usage: `!ci <name>`
- **tk** - kick player for teamkilling
	- Usage: `!tk <name>`
- **ban** - ban a player for 7 days
	- Usage: `!ban <name> <reason>`


### Senior Admin [80]

- **banlist** - display the last entries of the banlist
	- Usage: `!banlist`
- **kiss** - clear all player warnings
	- Usage: `!kiss`
- **kill** - kill a player
	- Usage: `!kill <name>`
- **map** - load given map
	- Usage: `!map <ut4_name>`
- **maprestart** - restart the map
	- Usage: `!maprestart`
- **cyclemap** - start next map in rotation
	- Usage: `!cyclemap`
- **setnextmap** - set the given map as nextmap
	- Usage: `!setnextmap <ut4_name>`
- **permban** - ban a player permanent
	- Usage: `!permban <name> <reason>`
	- Short: `!pb <name> <reason>`
- **putgroup** - add a client to a group
	- Usage: `!putgroup <name> <group>`
	- Available Groups: _user_, _regular_, _mod_, _admin_, _fulladmin_
- **unban** - unban a player from the database
	- Usage: `!unban <ID>`


### Head Admin [100]

- **putgroup** - add a client to a group
	- Usage: `!putgroup <name> <group>`
	- Available Groups: _user_, _regular_, _mod_, _admin_, _fulladmin_, _senioradmin_
- **ungroup** - remove admin level from a player
	- Usage: `!ungroup <name>`