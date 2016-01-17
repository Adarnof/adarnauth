# adarnauth
Yet another open-source auth system. But this one is new and shiny.

The goal of this project is to overhaul [AllianceAuth](https://github.com/R4stl1n/allianceauth) - it's got more duct tape holding it together than my entire hangar of minmatar ships.

## Project Outline

- [x] EVE model creation and updating
- [x] EVE SSO login integration
- [x] User access right management
- [x] Extended group model
- [x] Front-end web design and views for groups, access, characters
- [ ] LDAP
  - [ ] LDAP Models
  - [ ] Methods
  - [ ] OU syncing
  - [ ] Service DCs
  - [ ] CN syncing
  - [ ] Views
- [x] ~~Service model~~
- [ ] ~~Core service managers~~
  - [x] ~~openfire~~
  - [x] ~~phpbb~~
  - [ ] ~~discord~~
- [ ] ~~Front-end web design and views for services      <-- first release upon completion~~
- [ ] Accessory functions: application, fleet fits, timerboard, etc
- [ ] ~~More service managers: mumble, ts3, slack, ipboard3, etc~~
- [ ] Documentation and Tests (ongoing)

For the visual learners out there, here's an image of what the inital work on v2 is focused on. Stuff in the brown spraypain is being completely overhauled, the rest will be revamped (namely, services) or grafted on.

![v2](https://camo.githubusercontent.com/f144a7ed9152ca1154a8622d4a55f8e49f79a010/687474703a2f2f692e696d6775722e636f6d2f554c79704841332e706e67)

## What's this new LDAP nonsense?

I've been debugging issues with mumble for 8 months now and it comes down to mumble not respecting database changes. Only way to get its attention is through the ICE interface, but this doesn't let you manage groups.

The only other alternative is a custom authenticator which return a string of groups. For this I have two options:

 1. Write a custom authenticator for django
 2. Piggyback on the existing LDAP authenticator

Seeing as every service but TS3 (really people, why are you still using that crap?) supports LDAP authentication, I can enable every service out there which can use LDAP in one go.  
SMF? Yes. Mediawiki? Yes. IPBoard? You got it. The list goes on.

I know nothing of LDAP. So I'm pushing beta release back to March. Sorry. But it's worth it.

# Always looking for suggestions. Contact Adarnof in-game.
