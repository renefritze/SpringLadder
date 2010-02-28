# -*- coding: utf-8 -*-

helpstring_ladder_admin_manager = """!ladderjoinchannel channelname password: joins set channel and stores for automatic join
!ladderleavechannel channelname : leaves set channel and removes it from autojoin list
!ladderchangeaicount ladderID value : sets the AI count used by the ladder
!ladderchangeaicount ladderID min max : sets the AI count used by the ladder
!ladderchangecontrolteamsize ladderID value : sets the control team size (player ID) used by the ladder
!ladderchangecontrolteamsize ladderID min max : sets the control team size (player ID) used by the ladder
!ladderchangecontrolteamcount ladderID value : sets the control team count (player ID) used by the ladder
!ladderchangecontrolteamcount ladderID min max : sets the control team count (player ID) used by the ladder
!ladderchangeallysize ladderID value : sets the ally size used by the ladder
!ladderchangeallysize ladderID min max : sets the ally size used by the ladder
!ladderchangeallycount ladderID value : sets the ally count used by the ladder
!ladderchangeallycount ladderID min max : sets the ally count used by the ladder
!ladderaddoption ladderID blacklist/whitelist optionkey optionvalue : adds a new rule to the ladder, blacklist/whitelist is boolean and 1 means whitelist, a given key cannot have a whitelist and blacklist at the same time
!ladderremoveoption ladderID optionkey optionvalue : removes optionvalue from the ladder rules, if the optionkey has no values anymore it will be automatically removed
!ladderlistrankingalgos : list all available ranking algorithms by name
!laddersetrankingalgo ladderID algoName :set the used algorithm for ranking, currently switching algo on non-empty ladder will not recalc past results with new algo
!ladderdeletematch ladderID matchID: delete a match and all associated data from db, forces a recalculation of entire history of rankings for that ladder
!ladderbanuser ladderID username [time] : ban username from participating in any match on ladder ladderID for given amount of time (optional,floats, format: [D:]H )
!ladderunbanuser ladderID username : unban username from participating in any match on ladder ladderID
!ladderlistbans ladderID : list bans for given ladderID
!ladderrecalculateranks ladderID : recalculates full player rankings for given ladderID"""

helpstring_global_admin_manager ="""!ladderadd laddername : creates a new ladder
!ladderremove ladderID : deletes a ladder
!laddercopy source_id target_name : copy ladder with source_id to new ladder named target_name including all options
!ladderaddladderadmin ladderID username : add a new (local) admin to the ladder with LadderID
!ladderaddglobaladmin username : add a new global admin
!ladderdeleteladderadmin ladderID username : delete new (local) admin from the ladder with LadderID
!ladderdeleteglobaladmin username : delete global admin
!ladderbanuserglobal username [time] : ban username from participating in any match on any ladder for given amount of time (optional,floats, format: [D:]H )
!ladderunbanuserglobal username : unban username from participating in any match on any ladder
!ladderclosewhenempty : schedules a bot stop when there are no bot spawned
!ladderdisable : disables possibility for users to spawn new bots
!ladderenable : re-enables possibility for users to spawn new bots
!ladderauth password nick: set your user password for player nick
!laddermergeaccounts fromPlayer toPlayer [forcemerge] : merges all score results for all ladder of fromPlayer in toPlayer, if the 2 accounts fought eachother it will raise an exception ( optional: bool, automatic delete conflicting matches"""

helpstring_user_manager ="""!ladderlist : lists available ladders with their IDs
!ladder [password]: requests a bot to join your current game to monitor and submit scores
!ladder ladderID [password]: requests a bot to join your current game to monitor and submit scores got given ladderID
!ladderlistoptions ladderID : lists enforced options for given ladderID
!score ladderID : lists scores for all the players for the given ladderID
!score playername : lists scores for the given player in all ladders
!score ladderID playername : lists score for the given player for the given ladderID
!ladderlistmatches ladderID : list all matches for ladderID, newest first
!ladderauth password : set your user password (no spaces, no reuse of important passwords)
!ladderopponent ladderID : list opponents with similar skills suitable for a fight, best candidates first"""


helpstring_user_slave = """!ladderlist : lists available ladders with their IDs
!ladder ladderID: sets the ladder to report scores to, -1 to disable reporting
!ladderlistoptions ladderID : lists enforced options for given ladderID
!ladderlistoptions: lists enforced options for currently active ladderID
!ladderchecksetup : checks that all options and player setup are compatible with current set ladder
!ladderchecksetup ladderID: checks that all options and player setup are compatible for given ladderID
!ladderforcestart : forces the client to start spring
!score playername : lists scores for the given player in the current ladder
!score ladderid: lists scores for all the players for given ladderid
!score ladderID playername : lists score for the given player for the given ladderID
!ladderopponent ladderID : list opponents with similar skills suitable for a fight for given ladderID, best candidates first
!ladderopponent ladderID : list opponents with similar skills suitable for a fight for current ladder, best candidates first"""
