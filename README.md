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
 - [x] Internal redirect
   - [x] Hash matching
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

### Admin Site

Front-end settings are going away because the admin site can already do it, and handles permissions much better than I ever could.

Group management will stay web-based because you don't want group admins to be staff, that's scary.

# Suggestions?
