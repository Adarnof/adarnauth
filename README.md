# adarnauth
Messing around with Django and EVE SSO

The goal of this project is to overhaul [AllianceAuth](https://github.com/R4stl1n/allianceauth) using the newest Django standards. It will occur in distinct phases:

 [x] EVE model creation and updating
 [x] EVE SSO login integration
 [x] User access right management
 [] Extended group model
 [] Core services: openfire, mumble, phpbb
 [] Front-end web design
 [] More services: discord, ts3, slack, etc
 [] Accessory functions: application, fleet fits, timerboard, etc
 [] Documentation

One of the biggest goals is to shift away from managers full of staticmethods and instead rely on signalling to communicate changes. This will allow abstraction of many features such as services which is a big hurdle with the current system. Logging is also a core requirement, as retroactively adding 1k lines of logging to the old AllianceAuth has been a nightmare.

Always looking for suggestions. Contact Adarnof in-game.
