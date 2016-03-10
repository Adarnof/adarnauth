# adarnauth

[Live Demo](https://adarnauth.allianceauth.com)

Started as a rewrite of the core of AllianceAuth but has ballooned to a standalone auth system.

## Project Outline

### EVE Models

 - [x] Character
   - [x] Fetch from public API
   - [x] Async update task
   - [x] Determine owning user
   - [ ] Handle character deletion
 - [x] Corp
   - [x] Fetch from public API
   - [x] Async update task
   - [ ] Handle corp closure
 - [x] Alliance
   - [x] Fetch from public API
   - [x] Async update task
   - [ ] Handle alliance closure
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
 - [ ] Standing
   - [ ] Auto-populate
 - [x] Site access permission

### Groups

 - [x] Extend Group Model
   - [x] Owner/Admin/Member tiers
   - [x] Nesting (parent/child)
 - [x] Auto Assignment

### SSO

 - [x] Process SSO callback
 - [x] Generate missing user accounts
 - [ ] Internal redirect
   - [ ] Hash matching
   - [x] Session identity verification
   - [x] View redirect
   - [x] Auto-cleanup

### Explicit Service Support

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
 - [ ] Teamspeak?

# Suggestions?
