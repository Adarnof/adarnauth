# adarnauth

[Live Demo](https://adarnauth.allianceauth.com)

Started as a rewrite of the core of AllianceAuth but has ballooned to a standalone auth system.

# Wow such rewrite!

A major shift in project direction is in progress for two reasons:

1. CCP released their own version of an ACL system with CREST endpoints [on the way.](https://www.reddit.com/r/evetech/comments/4j347w/are_there_crest_endpoints_for_citadel_management/)
2. I want to release a multitude of apps, many of which share functional components.

One means a complete rewrite of the access management system with the goal of mirroring the in-game system for an easy crossover. *Imagine a world where you can import and export your auth ACL with citadels...*

Two means repackaging all the functions into little lego blocks I can play with to create a range of apps quickly and easily.

## I've come up with a series of django apps I need to create:

### SSO Token Management

This app will be responsible for storing SSO tokens for use with CREST-capable apps. It needs to handle redirects and callbacks, and be able to filter tokens by granted scopes.

Work has begun: [adarnauth-eve-sso](https://github.com/Adarnof/adarnauth-eve-sso)

### EVE Model Management

This app will house all the EVE-related models: characters, corps, alliances, API keys. It needs to be able to update model information and understand when they're no longer needed.

API keys need to be sorted by granted masks. I'll probably do this in a manner similar to SSO scopes, with pre-defined Mask models.

### ACL

This app will house Access Lists. It will depend on the EVE Model Management app.

It will have to provide a model mixin for determining if a character has access.

### Standings

This app will populate ACLs from standings, either API keys or CREST. It will depend on the SSO Management and EVE Model Management apps.

Standings will have to update automatically and trigger ACL reassessment upon change.

### Group Management

This app will house the ExtendedGroup models. Maybe with an ACL mixin.

### Base Service Model

This app will be the abstract base from which every other service is constructed.

It will contain a generic base service with the required functions (Add, Remove users).

Further abstract base services will include dabatase support and API support.

Another mixin will provide group functionality.

No true models will be created here, but will serve as a template for every service to come.

## This list will expand as I see fit.

As apps are written, they will be integrated into this repo to form ~~Voltron~~ Adarnauth.


## Old Project Outline

### EVE Models

 - [x] Character
   - [x] Fetch from public API
   - [x] Async update task
   - [x] Determine owning user
   - [x] Handle character deletion
 - [x] Corp
   - [x] Fetch from public API
   - [x] Async update task
   - [x] Handle corp closure
 - [x] Alliance
   - [x] Fetch from public API
   - [x] Async update task
   - [x] Handle alliance closure
 - [x] API Key
   - [x] Update from authorized API
   - [x] Populate characters
   - [x] Populate corp
   - [x] API verified permission
   - [x] Verify via SSO
 - [x] Standings
   - [x] Pull from authorized API

### Access Rules

 - [x] Character
   - [x] Auto-populate
 - [x] Corp
   - [x] Auto-populate
 - [x] Alliance
   - [x] Auto-populate
 - [x] Standing
   - [x] Auto-populate
 - [x] Site access permission

### Groups

 - [x] Extend Group Model
   - [x] Owner/Admin/Member tiers
   - [x] Nesting (parent/child)
 - [x] Auto Assignment

### SSO

 - [x] Process SSO callback
 - [x] Generate missing user accounts
 - [ ] Owner hash matching
 - [x] Internal redirect
   - [x] Hash matching
   - [x] Session identity verification
   - [x] View redirect
   - [ ] Auto-cleanup

### Explicit Service Support

 - [x] Mumble
   - [x] Base service functions
   - [x] Group mapping
   - [x] Front-end creation
   - [x] Signals
 - [ ] Openfire
   - [x] Base service functions
   - [ ] Broadcast
   - [x] Group mapping
   - [ ] Front-end creation
   - [x] Signals
 - [ ] Phpbb3
   - [x] Base service functions
   - [x] Group mapping
   - [ ] Front-end creation
   - [x] Signals
 - [ ] Discord
   - [ ] Base service functions
   - [ ] Broadcast
   - [ ] Group mapping
   - [ ] Front-end creation
   - [ ] Signals

### App Admin Hardening
Tolerate users pushing buttons on the admin site I might not like.

 - [x] access
 - [x] authentication
 - [x] eveonline
 - [x] groupmanagement
 - [ ] ldap_service
 - [ ] mumble
 - [ ] openfire
 - [ ] phpbb

# Suggestions?
