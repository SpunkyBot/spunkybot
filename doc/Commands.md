# Spunky Bot

## Admin Levels and Bot Commands

### Guest [0]

* **help** - display all available commands
  * Usage: `!help`
  * Short: `!h`
* **forgive** - forgive a player for team killing
  * Usage: `!forgive [<name|id>]`
  * Short: `!f [<name|id>]`
* **forgiveall** - forgive all team kills
  * Usage: `!forgiveall`
  * Short: `!fa`
* **forgivelist** - list all players who killed you
  * Usage: `!forgivelist`
  * Short: `!fl`
* **forgiveprev** - forgive last team kill
  * Usage: `!forgiveprev`
  * Short: `!fp`
* **grudge** - grudge a player for team killing (a grudged player will not be forgiven)
  * Usage: `!grudge [<name|id>]`
* **bombstats** - display Bomb mode stats
  * Usage: `!bombstats`
* **ctfstats** - display Capture the Flag stats
  * Usage: `!ctfstats`
* **freezestats** - display freeze/thawout stats
  * Usage: `!freezestats`
* **hestats** - display HE grenade kill stats
  * Usage: `!hestats`
* **hits** - display hit stats
  * Usage: `!hits`
* **hs** - display headshot counter
  * Usage: `!hs`
* **knife** - display knife kill stats
  * Usage: `!knife`
* **register** - register yourself as a basic user
  * Usage: `!register`
* **spree** - display current kill streak
  * Usage: `!spree`
* **stats** - display current map stats
  * Usage: `!stats`
* **teams** - balance teams
  * Usage: `!teams`
* **time** - display the current server time
  * Usage: `!time`

### User [1]

* **regtest** - display current user status
  * Usage: `!regtest`
* **xlrstats** - display full player statistics
  * Usage: `!xlrstats [<name|id>]`
* **xlrtopstats** - display the top players
  * Usage: `!xlrtopstats`
  * Short: `!topstats`

### Moderator [20]

* **admintest** - display current admin status
  * Usage: `!admintest`
* **country** - get the country of a player
  * Usage: `!country <name|id>`
* **lastmaps** - list the last played maps
  * Usage: `!lastmaps`
* **leveltest** - get the admin level for a given player or myself
  * Usage: `!leveltest [<name|id>]`
  * Short: `!lt [<name|id>]`
* **list** - list all connected players
  * Usage: `!list`
* **locate** - display geolocation info of a player
  * Usage: `!locate <name|id>`
  * Short: `!lc <name|id>`
* **nextmap** - display the next map in rotation
  * Usage: `!nextmap`
* **mute** - mute or unmute a player
  * Usage: `!mute <name|id> [<seconds>]`
* **poke** - notify a player that he needs to move
  * Usage: `!poke <name|id>`
* **seen** - display when a player was last seen
  * Usage: `!seen <name|id>`
* **shuffleteams** - shuffle the teams
  * Usage: `!shuffleteams`
  * Short: `!shuffle`
* **spec** - move yourself to spectator
  * Usage: `!spec`
  * Short: `!sp`
* **warn** - warn player
  * Usage: `!warn <name|id> [<reason>]`
  * Short: `!w <name|id> [<reason>]`
  * Available short form reasons: _tk_, _sk_, _wh_, _ci_, _obj_, _afk_, _spec_, _ping_, _spam_, _camp_, _score_, _skill_, _lang_, _racism_, _name_, _whiner_, _abuse_, _insult_, _teams_
* **warninfo** - display how many warnings a player has
  * Usage: `!warninfo <name|id>`
  * Short: `!wi <name|id>`
* **warnremove** - remove a player's last warning
  * Usage: `!warnremove <name|id>`
  * Short: `!wr <name|id>`
* **warns** - list the warnings
  * Usage: `!warns`
* **warntest** - test a warning
  * Usage: `!warntest <warning>`

### Admin [40]

* **admins** - list all the online admins
  * Usage: `!admins`
* **afk** - force a player to spec, because he is away from keyboard
  * Usage: `!afk <name|id>`
* **aliases** - list the aliases of a player
  * Usage: `!aliases <name|id>`
  * Short: `!alias <name|id>`
* **bigtext** - display big message on screen
  * Usage: `!bigtext <text>`
* **exit** - display last disconnected player of this match
  * Usage: `!exit`
* **find** - display the slot number of a player
  * Usage: `!find <name|id>`
* **force** - force a player to the given team or release the player from a forced team (free)
  * Usage: `!force <name|id> <blue/red/spec/free> [<lock>]`
  * Adding `lock` will lock the player where it is forced to.
* **kick** - kick a player
  * Usage: `!kick <name|id> <reason>`
  * Short: `!k <name|id> <reason>`
* **nuke** - nuke a player
  * Usage: `!nuke <name|id>`
* **regulars** - display the regular players online
  * Usage: `!regulars`
  * Short: `!regs`
* **say** - say a message to all players (allow spectator to say a message to players in-game)
  * Usage: `!say <text>`
  * Short: `!!<text>`
* **tell** - tell a message to a specific player
  * Usage: `!tell <name|id> <text>`
* **tempban** - ban a player temporary for the given period of 1 sec to 3 days
  * Usage: `!tempban <name|id> <duration> [<reason>]`
  * Short: `!tb <name|id> <duration> [<reason>]`
  * Maximum ban duration: 72 hours
* **warnclear** - clear the player warnings
  * Usage: `!warnclear <name|id>`
  * Short: `!wc <name|id>`

### Full Admin [60]

* **ban** - ban a player for several days
  * Usage: `!ban <name|id> <reason>`
  * Short: `!b <name|id> <reason>`
* **baninfo** - display active bans of a player
  * Usage: `!baninfo <name|id>`
  * Short: `!bi <name|id>`
* **ci** - kick player with connection interrupt
  * Usage: `!ci <name|id>`
* **forgiveclear** - clear a player's team kills
  * Usage: `!forgiveclear [<name|id>]`
  * Short: `!fc [<name|id>]`
* **forgiveinfo** - display a player's team kills
  * Usage: `!forgiveinfo <name|id>`
  * Short: `!fi <name|id>`
* **id** - show the IP, guid and authname of a player
  * Usage: `!id <name|id>`
* **kickbots** kick all bots
  * Usage: `!kickbots`
  * Short: `!kb`
* **ping** - display the ping of a player
  * Usage: `!ping <name|id>`
* **rain** - enables or disables rain
  * Usage: `!rain <on/off>`
* **scream** - scream a message in different colors to all players
  * Usage: `!scream <text>`
* **slap** - slap a player (a number of times)
  * Usage: `!slap <name|id> [<amount>]`
  * Default amount: 1
  * Max amount: 15
* **status** - report the status of the bot
  * Usage: `!status`
* **swap** - swap teams for player A and B (if in different teams). If player B is not specified, the admin using the command is swapped with player A
  * Usage: `!swap <playerA> [<playerB>]`
* **version** - display the version of the bot
  * Usage: `!version`
* **veto** - stop voting process
  * Usage: `!veto`

### Senior Admin [80]

* **addbots** - add bots to the game (requires `!bots on` first)
  * Usage: `!addbots`
* **banall** - ban all players matching pattern
  * Usage: `!banall <pattern> [<reason>]`
  * Short: `!ball`
* **banlist** - display the last active 10 bans
  * Usage: `!banlist`
* **bots** - enables or disables bot support
  * Usage: `!bots <on/off>`
* **cyclemap** - cycle to the next map
  * Usage: `!cyclemap`
* **exec** - execute given config file
  * Usage: `!exec <filename>`
* **gear** - set allowed weapons
  * Usage: `!gear <default/all/knife/pistol/shotgun/sniper>`
* **instagib** - set Instagib mode
  * Usage: `!instagib <on/off>`
* **kickall** - kick all players matching pattern
  * Usage: `!kickall <pattern> [<reason>]`
  * Short: `!kall`
* **clear** - clear all player warnings
  * Usage: `!clear`
  * Alias: `!kiss`
* **kill** - kill a player
  * Usage: `!kill <name|id>`
* **lastbans** - list the last 4 bans
  * Usage: `!lastbans`
  * Short: `!bans`
* **lookup** - search for player in the database
  * Usage: `!lookup <name|id>`
  * Short: `!l <name|id>`
* **makereg** - make a player a regular (Level 2) user
  * Usage: `!makereg <name|id>`
  * Short: `!mr <name|id>`
* **map** - load given map
  * Usage: `!map <ut4_name>`
* **mapcycle** - list the map rotation
  * Usage: `!mapcycle`
* **maps** - display all available maps
  * Usage: `!maps`
* **maprestart** - restart the map
  * Usage: `!maprestart`
  * Short: `!restart`
* **moon** - activate low gravity mode (Moon mode)
  * Usage: `!moon <on/off>`
  * Alias: `!lowgravity <on/off>`
* **permban** - ban a player permanent
  * Usage: `!permban <name|id> <reason>`
  * Short: `!pb <name|id> <reason>`
* **putgroup** - add a client to a group
  * Usage: `!putgroup <name|id> <group>`
  * Available Groups: _user_, _regular_, _mod_, _admin_, _fulladmin_
* **rebuild** - sync up all available maps
  * Usage: `!rebuild`
* **setgravity** - set the gravity (default = 800), less means less gravity
  * Usage: `!setgravity <value>`
* **setnextmap** - set the next map
  * Usage: `!setnextmap <ut4_name>`
* **swapteams** - swap the current teams
  * Usage: `!swapteams`
* **unban** - unban a player from the database
  * Usage: `!unban <ID>`
* **unreg** - remove a player from the regular group
  * Usage: `!unreg <name|id>`

### Super Admin [90]

* **bomb** - change gametype to Bomb
  * Usage: `!bomb`
* **ctf** - change gametype to Capture the Flag
  * Usage: `!ctf`
* **ffa** - change gametype to Free For All
  * Usage: `!ffa`
* **gungame** - change gametype to Gun Game
  * Usage: `!gungame`
* **jump** - change gametype to Jump
  * Usage: `!jump`
* **lms** - change gametype to Last Man Standing
  * Usage: `!lms`
* **tdm** - change gametype to Team Deathmatch
  * Usage: `!tdm`
* **ts** - change gametype to Team Survivor
  * Usage: `!ts`
* **password** - set private server password
  * Usage: `!password [<password>]`
  * Set an empty string to remove a password
* **putgroup** - add a client to a group
  * Usage: `!putgroup <name|id> <group>`
  * Available Groups: _user_, _regular_, _mod_, _admin_, _fulladmin_, _senioradmin_
* **reload** - reload map
  * Usage: `!reload`
* **ungroup** - remove admin level from a player
  * Usage: `!ungroup <name|id>`

### Head Admin [100]

* **putgroup** - add a client to a group
  * Usage: `!putgroup <name|id> <group>`
  * Available Groups: _user_, _regular_, _mod_, _admin_, _fulladmin_, _senioradmin_, _superadmin_
