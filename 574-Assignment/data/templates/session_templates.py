"""
Session Notes Query Templates

Templates for generating synthetic training data for the session_notes tool.
Each intent has 10-15 templates that can be filled with entity slots.

20 Intents:
- character_status
- event_sequence
- npc_info
- location_details
- item_tracking
- combat_recap
- spell_ability_usage
- character_decisions
- party_dynamics
- quest_tracking
- puzzle_solutions
- loot_rewards
- death_revival
- divine_religious
- memory_vision
- rules_mechanics
- humor_moments
- unresolved_mysteries
- future_implications
- cross_session
"""

# =============================================================================
# CHARACTER_STATUS - Current state of characters
# =============================================================================

CHARACTER_STATUS_TEMPLATES = [
    {"template": "What is my current HP?", "slots": {}},
    {"template": "What conditions am I suffering from?", "slots": {}},
    {"template": "Am I alive or dead right now?", "slots": {}},
    {"template": "Where is my character located?", "slots": {}},
    {"template": "What's my character's current state?", "slots": {}},
    {"template": "How did my physical state change in the last session?", "slots": {}},
    {"template": "What happened to me in the last session?", "slots": {}},
    {"template": "Am I injured?", "slots": {}},
    {"template": "What debuffs do I have?", "slots": {}},
    {"template": "Is my character conscious?", "slots": {}},
    {"template": "How many hit points am I missing?", "slots": {}},
    {"template": "What status effects are currently on me?", "slots": {}},
    {"template": "Did I take damage last session?", "slots": {}},
    {"template": "Am I exhausted?", "slots": {}},
    {"template": "What level of exhaustion do I have?", "slots": {}},
    {"template": "Is my character poisoned or diseased?", "slots": {}},
    {"template": "What buffs are affecting me?", "slots": {}},
    {"template": "Did I rest last session?", "slots": {}},
    {"template": "Am I at full health?", "slots": {}},
    {"template": "What's my current hit die situation?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "What's {CHARACTER}'s current HP?", "slots": {}},
    {"template": "Is {CHARACTER} still conscious after that fight?", "slots": {}},
    {"template": "Where did we leave {CHARACTER} at the end of the session?", "slots": {}},
    {"template": "What conditions is {PARTY_MEMBER} suffering from?", "slots": {}},
    {"template": "Did {PARTY_MEMBER} get hurt in that last encounter?", "slots": {}},
    {"template": "Is {PARTY_MEMBER} still cursed?", "slots": {}},
    {"template": "How many hit points is {CHARACTER} missing?", "slots": {}},
    {"template": "What happened to {PARTY_MEMBER} during the ambush?", "slots": {}},
    {"template": "Does {CHARACTER} have any exhaustion levels?", "slots": {}},
    {"template": "Is {PARTY_MEMBER} at full health or do they need healing?", "slots": {}},
]

# =============================================================================
# EVENT_SEQUENCE - Chronological events
# =============================================================================

EVENT_SEQUENCE_TEMPLATES = [
    {"template": "What happened in the last session?", "slots": {}},
    {"template": "Walk me through the events of the last session", "slots": {}},
    {"template": "What were the key events that occurred?", "slots": {}},
    {"template": "Give me a chronological summary", "slots": {}},
    {"template": "What happened first, second, and third?", "slots": {}},
    {"template": "Describe the last session in order", "slots": {}},
    {"template": "What's the timeline of recent events?", "slots": {}},
    {"template": "Recap what happened", "slots": {}},
    {"template": "What did we do last time?", "slots": {}},
    {"template": "Summarize the session events", "slots": {}},
    {"template": "How did the session begin?", "slots": {}},
    {"template": "What happened at the end of the session?", "slots": {}},
    {"template": "What was the turning point of the session?", "slots": {}},
    {"template": "Break down the session into major beats", "slots": {}},
    {"template": "What were the main story beats?", "slots": {}},
    {"template": "How did events unfold?", "slots": {}},
    {"template": "What sequence of events led to the climax?", "slots": {}},
    {"template": "Give me the highlights in order", "slots": {}},
    {"template": "What was the order of encounters?", "slots": {}},
    {"template": "How did the session progress?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "What did {CHARACTER} do during the last session?", "slots": {}},
    {"template": "When did {PARTY_MEMBER} join up with us?", "slots": {}},
    {"template": "At what point did we encounter {NPC}?", "slots": {}},
    {"template": "What was {CHARACTER} doing while the rest of us fought?", "slots": {}},
    {"template": "Walk me through {PARTY_MEMBER}'s actions last session", "slots": {}},
    {"template": "When did {NPC} first appear in the timeline?", "slots": {}},
    {"template": "What happened right after {CHARACTER} cast that spell?", "slots": {}},
    {"template": "How did the session end for {PARTY_MEMBER}?", "slots": {}},
    {"template": "What was {NPC} doing during the climax?", "slots": {}},
    {"template": "Summarize what happened between {CHARACTER} and {NPC}", "slots": {}},
]

# =============================================================================
# NPC_INFO - NPC interactions and relationships
# =============================================================================

NPC_INFO_TEMPLATES = [
    {"template": "Who did we meet in the last session?", "slots": {}},
    {"template": "Tell me about the NPCs we encountered", "slots": {}},
    {"template": "What NPCs did we interact with?", "slots": {}},
    {"template": "Who was the {creature} we met?", "slots": {"creature": "creature"}},
    {"template": "What did the {creature} want?", "slots": {"creature": "creature"}},
    {"template": "How did our conversation with the {creature} go?", "slots": {"creature": "creature"}},
    {"template": "What do we know about the NPCs?", "slots": {}},
    {"template": "Who helped us?", "slots": {}},
    {"template": "Who was hostile to us?", "slots": {}},
    {"template": "What's the relationship with the NPCs we met?", "slots": {}},
    {"template": "Did we make any new allies?", "slots": {}},
    {"template": "Who betrayed us?", "slots": {}},
    {"template": "What was the {creature}'s motivation?", "slots": {"creature": "creature"}},
    {"template": "Who gave us information?", "slots": {}},
    {"template": "What did the shopkeeper sell us?", "slots": {}},
    {"template": "Who seemed suspicious?", "slots": {}},
    {"template": "What NPC quest givers did we meet?", "slots": {}},
    {"template": "Did any NPCs lie to us?", "slots": {}},
    {"template": "Who did we negotiate with?", "slots": {}},
    {"template": "What NPCs owe us favors?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "What did {NPC} tell us about the dungeon?", "slots": {}},
    {"template": "How did {NPC} react when we mentioned the treasure?", "slots": {}},
    {"template": "Is {NPC} trustworthy or should we be suspicious?", "slots": {}},
    {"template": "What deal did {CHARACTER} make with {NPC}?", "slots": {}},
    {"template": "Did {NPC} give us any useful information?", "slots": {}},
    {"template": "What does {NPC} want from us?", "slots": {}},
    {"template": "How did {PARTY_MEMBER}'s conversation with {NPC} go?", "slots": {}},
    {"template": "Where can we find {NPC} again?", "slots": {}},
    {"template": "What's {NPC}'s relationship with the villain?", "slots": {}},
    {"template": "Did {NPC} seem to recognize {CHARACTER}?", "slots": {}},
]

# =============================================================================
# LOCATION_DETAILS - Places visited and explored
# =============================================================================

LOCATION_DETAILS_TEMPLATES = [
    {"template": "Where did we go in the last session?", "slots": {}},
    {"template": "What locations did we visit?", "slots": {}},
    {"template": "Describe the {location} we explored", "slots": {"location": "location"}},
    {"template": "What's notable about the places we visited?", "slots": {}},
    {"template": "What did we find at the {location}?", "slots": {"location": "location"}},
    {"template": "Where are we now?", "slots": {}},
    {"template": "What places have we explored?", "slots": {}},
    {"template": "Tell me about the dungeon we went through", "slots": {}},
    {"template": "What was the environment like?", "slots": {}},
    {"template": "What dangers were in the {location}?", "slots": {"location": "location"}},
    {"template": "What rooms did we explore?", "slots": {}},
    {"template": "Describe the layout of the {location}", "slots": {"location": "location"}},
    {"template": "What landmarks did we pass?", "slots": {}},
    {"template": "Were there any hidden areas?", "slots": {}},
    {"template": "What was the atmosphere of the place?", "slots": {}},
    {"template": "How did we enter the {location}?", "slots": {"location": "location"}},
    {"template": "What exits did we find?", "slots": {}},
    {"template": "Was the location trapped?", "slots": {}},
    {"template": "What environmental hazards were there?", "slots": {}},
    {"template": "What secrets did the {location} hold?", "slots": {"location": "location"}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "Where did {CHARACTER} scout ahead to?", "slots": {}},
    {"template": "What did {PARTY_MEMBER} discover in the back room?", "slots": {}},
    {"template": "Where did {NPC} lead us?", "slots": {}},
    {"template": "What part of the dungeon did {CHARACTER} explore alone?", "slots": {}},
    {"template": "Where was {NPC}'s hideout located?", "slots": {}},
    {"template": "What did {PARTY_MEMBER} find when they investigated that area?", "slots": {}},
    {"template": "Where did we agree to meet {NPC}?", "slots": {}},
    {"template": "What room did {CHARACTER} get separated in?", "slots": {}},
    {"template": "Where is {NPC}'s shop located in the city?", "slots": {}},
    {"template": "What secret passage did {PARTY_MEMBER} find?", "slots": {}},
]

# =============================================================================
# ITEM_TRACKING - Items found, lost, used
# =============================================================================

ITEM_TRACKING_TEMPLATES = [
    {"template": "What items did we find in the last session?", "slots": {}},
    {"template": "What did we pick up?", "slots": {}},
    {"template": "Did we lose any items?", "slots": {}},
    {"template": "What happened to the {item}?", "slots": {"item": "item"}},
    {"template": "What items were used during the session?", "slots": {}},
    {"template": "Who has the {item}?", "slots": {"item": "item"}},
    {"template": "What did we trade?", "slots": {}},
    {"template": "Did we buy or sell anything?", "slots": {}},
    {"template": "What equipment changed hands?", "slots": {}},
    {"template": "Track the {item} - where is it now?", "slots": {"item": "item"}},
    {"template": "What consumables did we use?", "slots": {}},
    {"template": "Did we break any items?", "slots": {}},
    {"template": "What potions did we drink?", "slots": {}},
    {"template": "What scrolls did we use?", "slots": {}},
    {"template": "Did we give away any items?", "slots": {}},
    {"template": "What items were stolen from us?", "slots": {}},
    {"template": "Did we identify any magic items?", "slots": {}},
    {"template": "What ammunition did we expend?", "slots": {}},
    {"template": "Did anyone attune to the {item}?", "slots": {"item": "item"}},
    {"template": "What happened to our supplies?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "What did {CHARACTER} pick up from the treasure hoard?", "slots": {}},
    {"template": "Did {PARTY_MEMBER} use any potions during the fight?", "slots": {}},
    {"template": "What did {NPC} give us as a reward?", "slots": {}},
    {"template": "Who is currently holding the magic sword - {CHARACTER} or {PARTY_MEMBER}?", "slots": {}},
    {"template": "What did we trade to {NPC}?", "slots": {}},
    {"template": "Did {CHARACTER} attune to any new magic items?", "slots": {}},
    {"template": "What did {PARTY_MEMBER} buy from the merchant?", "slots": {}},
    {"template": "What items did {NPC} steal from us?", "slots": {}},
    {"template": "Did {CHARACTER} give anything to {NPC}?", "slots": {}},
    {"template": "What scrolls did {PARTY_MEMBER} use in the last battle?", "slots": {}},
]

# =============================================================================
# COMBAT_RECAP - Past combat encounters
# =============================================================================

COMBAT_RECAP_TEMPLATES = [
    {"template": "What fights did we have?", "slots": {}},
    {"template": "Describe the combat encounters", "slots": {}},
    {"template": "How did the battle go?", "slots": {}},
    {"template": "Who did we fight?", "slots": {}},
    {"template": "What was the outcome of the combat?", "slots": {}},
    {"template": "How much damage did we take?", "slots": {}},
    {"template": "What tactics did we use?", "slots": {}},
    {"template": "How did we defeat the {creature}?", "slots": {"creature": "creature"}},
    {"template": "What was the hardest fight?", "slots": {}},
    {"template": "Did anyone go down in combat?", "slots": {}},
    {"template": "What enemies did we face?", "slots": {}},
    {"template": "How many {creature} did we kill?", "slots": {"creature": "creature"}},
    {"template": "What was the initiative order?", "slots": {}},
    {"template": "Did we win or lose the fight?", "slots": {}},
    {"template": "What special attacks did enemies use?", "slots": {}},
    {"template": "Did anyone get a critical hit?", "slots": {}},
    {"template": "How did we start the fight?", "slots": {}},
    {"template": "Did we get ambushed?", "slots": {}},
    {"template": "What legendary actions did the {creature} use?", "slots": {"creature": "creature"}},
    {"template": "How did the combat end?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "How many enemies did {CHARACTER} take down?", "slots": {}},
    {"template": "Did {PARTY_MEMBER} get knocked unconscious during the fight?", "slots": {}},
    {"template": "What was {CHARACTER}'s role in the battle?", "slots": {}},
    {"template": "How much damage did {PARTY_MEMBER} deal to the boss?", "slots": {}},
    {"template": "Who did {CHARACTER} focus their attacks on?", "slots": {}},
    {"template": "Did {PARTY_MEMBER} land any critical hits?", "slots": {}},
    {"template": "What happened when {CHARACTER} charged into combat?", "slots": {}},
    {"template": "How did {PARTY_MEMBER} save the party during the ambush?", "slots": {}},
    {"template": "What tactics did {CHARACTER} and {PARTY_MEMBER} use together?", "slots": {}},
    {"template": "Did {NPC} help us or fight against us?", "slots": {}},
]

# =============================================================================
# SPELL_ABILITY_USAGE - Spells and abilities used
# =============================================================================

SPELL_ABILITY_USAGE_TEMPLATES = [
    {"template": "What spells were cast in the session?", "slots": {}},
    {"template": "Did I use {spell}?", "slots": {"spell": "spell"}},
    {"template": "What abilities did we use?", "slots": {}},
    {"template": "How effective was {spell}?", "slots": {"spell": "spell"}},
    {"template": "What magical effects happened?", "slots": {}},
    {"template": "Did anyone cast {spell}?", "slots": {"spell": "spell"}},
    {"template": "What special abilities were activated?", "slots": {}},
    {"template": "How did {feature} work in that situation?", "slots": {"feature": "feature"}},
    {"template": "What resources did we expend?", "slots": {}},
    {"template": "Track spell slot usage", "slots": {}},
    {"template": "What concentration spells were active?", "slots": {}},
    {"template": "Did any spells fail?", "slots": {}},
    {"template": "What saves did enemies make against {spell}?", "slots": {"spell": "spell"}},
    {"template": "Did we use any racial abilities?", "slots": {}},
    {"template": "What class features were used?", "slots": {}},
    {"template": "How many spell slots remain?", "slots": {}},
    {"template": "What was the best spell moment?", "slots": {}},
    {"template": "Did anyone counterspell?", "slots": {}},
    {"template": "What ritual spells were cast?", "slots": {}},
    {"template": "What cantrips were used?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "What spells did {CHARACTER} cast during the battle?", "slots": {}},
    {"template": "Did {PARTY_MEMBER} use their Channel Divinity?", "slots": {}},
    {"template": "How many spell slots does {CHARACTER} have left?", "slots": {}},
    {"template": "What was that awesome spell {PARTY_MEMBER} used?", "slots": {}},
    {"template": "Did {CHARACTER} maintain concentration on their spell?", "slots": {}},
    {"template": "What racial ability did {PARTY_MEMBER} activate?", "slots": {}},
    {"template": "Did {CHARACTER} use {spell} on the boss?", "slots": {"spell": "spell"}},
    {"template": "How effective was {PARTY_MEMBER}'s Fireball?", "slots": {}},
    {"template": "What class features did {CHARACTER} burn through?", "slots": {}},
    {"template": "Did {NPC} cast any magic during the encounter?", "slots": {}},
]

# =============================================================================
# CHARACTER_DECISIONS - Important choices made
# =============================================================================

CHARACTER_DECISIONS_TEMPLATES = [
    {"template": "What important decisions did we make?", "slots": {}},
    {"template": "Why did we choose that path?", "slots": {}},
    {"template": "What was our reasoning?", "slots": {}},
    {"template": "What moral choices did we face?", "slots": {}},
    {"template": "What did we decide about the {creature}?", "slots": {"creature": "creature"}},
    {"template": "What commitments did we make?", "slots": {}},
    {"template": "What promises did we give?", "slots": {}},
    {"template": "Why did my character do that?", "slots": {}},
    {"template": "What influenced our decisions?", "slots": {}},
    {"template": "What consequences came from our choices?", "slots": {}},
    {"template": "Did we spare or kill the {creature}?", "slots": {"creature": "creature"}},
    {"template": "What ethical dilemmas did we face?", "slots": {}},
    {"template": "Why did we accept that quest?", "slots": {}},
    {"template": "What deals did we make?", "slots": {}},
    {"template": "Did we break any laws?", "slots": {}},
    {"template": "What alignments did our actions reflect?", "slots": {}},
    {"template": "Did we lie to anyone?", "slots": {}},
    {"template": "What sacrifices did we make?", "slots": {}},
    {"template": "Who did we choose to help?", "slots": {}},
    {"template": "What did we refuse to do?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "Why did {CHARACTER} decide to spare the prisoner?", "slots": {}},
    {"template": "What promise did {PARTY_MEMBER} make to {NPC}?", "slots": {}},
    {"template": "What was {CHARACTER}'s reasoning for taking that risk?", "slots": {}},
    {"template": "Did {PARTY_MEMBER} agree with the party's decision?", "slots": {}},
    {"template": "What deal did we strike with {NPC}?", "slots": {}},
    {"template": "Why did {CHARACTER} refuse to help {NPC}?", "slots": {}},
    {"template": "What moral dilemma did {PARTY_MEMBER} face?", "slots": {}},
    {"template": "How did {CHARACTER}'s choice affect our relationship with {NPC}?", "slots": {}},
    {"template": "What did {PARTY_MEMBER} sacrifice for the mission?", "slots": {}},
    {"template": "Why did {CHARACTER} lie to {NPC}?", "slots": {}},
]

# =============================================================================
# PARTY_DYNAMICS - Group interactions
# =============================================================================

PARTY_DYNAMICS_TEMPLATES = [
    {"template": "How is the party getting along?", "slots": {}},
    {"template": "What happened between party members?", "slots": {}},
    {"template": "Did anyone argue?", "slots": {}},
    {"template": "What party interactions were significant?", "slots": {}},
    {"template": "How did the group work together?", "slots": {}},
    {"template": "Were there any conflicts?", "slots": {}},
    {"template": "Who took the lead?", "slots": {}},
    {"template": "What bonding moments happened?", "slots": {}},
    {"template": "How did party roles develop?", "slots": {}},
    {"template": "What's the group dynamic like?", "slots": {}},
    {"template": "Did anyone disagree on tactics?", "slots": {}},
    {"template": "Who saved whom in combat?", "slots": {}},
    {"template": "What secrets were shared?", "slots": {}},
    {"template": "Did any character development happen?", "slots": {}},
    {"template": "How did relationships change?", "slots": {}},
    {"template": "Who is the party leader right now?", "slots": {}},
    {"template": "Were there any romantic moments?", "slots": {}},
    {"template": "Did anyone leave or join the party?", "slots": {}},
    {"template": "What trust issues emerged?", "slots": {}},
    {"template": "How well did we coordinate?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "Did {CHARACTER} and {PARTY_MEMBER} have any conflict?", "slots": {}},
    {"template": "How is {CHARACTER}'s relationship with {PARTY_MEMBER} developing?", "slots": {}},
    {"template": "What secret did {PARTY_MEMBER} reveal to the group?", "slots": {}},
    {"template": "Did {CHARACTER} trust {PARTY_MEMBER} with the plan?", "slots": {}},
    {"template": "What bonding moment happened between {CHARACTER} and {PARTY_MEMBER}?", "slots": {}},
    {"template": "Why did {CHARACTER} and {PARTY_MEMBER} argue?", "slots": {}},
    {"template": "How did {PARTY_MEMBER} save {CHARACTER} in that fight?", "slots": {}},
    {"template": "Is there tension between {CHARACTER} and {PARTY_MEMBER}?", "slots": {}},
    {"template": "What did {CHARACTER} confide in {PARTY_MEMBER}?", "slots": {}},
    {"template": "How did {PARTY_MEMBER} react to {CHARACTER}'s decision?", "slots": {}},
]

# =============================================================================
# QUEST_TRACKING - Quest progress and completion
# =============================================================================

QUEST_TRACKING_TEMPLATES = [
    {"template": "What quest progress did we make?", "slots": {}},
    {"template": "What quests did we complete?", "slots": {}},
    {"template": "What new quests did we accept?", "slots": {}},
    {"template": "What's the status of our main quest?", "slots": {}},
    {"template": "What objectives did we accomplish?", "slots": {}},
    {"template": "What side quests are active?", "slots": {}},
    {"template": "What did we learn about our quest?", "slots": {}},
    {"template": "How close are we to finishing the quest?", "slots": {}},
    {"template": "What quest rewards did we get?", "slots": {}},
    {"template": "What quest-related NPCs did we meet?", "slots": {}},
    {"template": "Did we fail any quests?", "slots": {}},
    {"template": "What quest items did we find?", "slots": {}},
    {"template": "What are our current quest objectives?", "slots": {}},
    {"template": "Did we get any new quest hooks?", "slots": {}},
    {"template": "What's the next step in our main quest?", "slots": {}},
    {"template": "How many quests are we tracking?", "slots": {}},
    {"template": "What quest deadlines are approaching?", "slots": {}},
    {"template": "Did we turn in any quests?", "slots": {}},
    {"template": "What bounties did we complete?", "slots": {}},
    {"template": "What contracts did we fulfill?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "What quest did {NPC} give us?", "slots": {}},
    {"template": "Did we report back to {NPC} about the quest?", "slots": {}},
    {"template": "What's {CHARACTER}'s personal quest status?", "slots": {}},
    {"template": "How does {NPC}'s request connect to our main quest?", "slots": {}},
    {"template": "What did {NPC} promise us as a reward?", "slots": {}},
    {"template": "What objective did {PARTY_MEMBER} complete for their backstory?", "slots": {}},
    {"template": "Did we accept the bounty from {NPC}?", "slots": {}},
    {"template": "What's the deadline for {NPC}'s quest?", "slots": {}},
    {"template": "How does {CHARACTER}'s goal align with the party quest?", "slots": {}},
    {"template": "What did {NPC} reveal about our main objective?", "slots": {}},
]

# =============================================================================
# PUZZLE_SOLUTIONS - Puzzles encountered and solved
# =============================================================================

PUZZLE_SOLUTIONS_TEMPLATES = [
    {"template": "What puzzles did we encounter?", "slots": {}},
    {"template": "How did we solve the puzzle?", "slots": {}},
    {"template": "What riddles did we face?", "slots": {}},
    {"template": "What traps did we disarm?", "slots": {}},
    {"template": "How did we get past the obstacle?", "slots": {}},
    {"template": "What was the solution to the puzzle?", "slots": {}},
    {"template": "Did we miss any puzzles?", "slots": {}},
    {"template": "What challenges required thinking?", "slots": {}},
    {"template": "What clues did we find?", "slots": {}},
    {"template": "How did we figure it out?", "slots": {}},
    {"template": "What was the password or code?", "slots": {}},
    {"template": "What lever combination worked?", "slots": {}},
    {"template": "How did we open the locked door?", "slots": {}},
    {"template": "What patterns did we notice?", "slots": {}},
    {"template": "Who solved the puzzle?", "slots": {}},
    {"template": "What tools did we need for the puzzle?", "slots": {}},
    {"template": "What happens if we failed the puzzle?", "slots": {}},
    {"template": "Were there any hint inscriptions?", "slots": {}},
    {"template": "What mechanism did the puzzle control?", "slots": {}},
    {"template": "Did we brute force any puzzles?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "How did {CHARACTER} figure out the riddle?", "slots": {}},
    {"template": "What clue did {PARTY_MEMBER} notice that helped solve it?", "slots": {}},
    {"template": "Did {CHARACTER} disarm the trap successfully?", "slots": {}},
    {"template": "What puzzle hint did {NPC} give us?", "slots": {}},
    {"template": "How did {PARTY_MEMBER}'s backstory knowledge help with the puzzle?", "slots": {}},
    {"template": "What role did {CHARACTER} play in solving the puzzle?", "slots": {}},
    {"template": "Did {PARTY_MEMBER} trigger any traps?", "slots": {}},
    {"template": "What pattern did {CHARACTER} recognize?", "slots": {}},
    {"template": "How did {NPC}'s journal help us solve the riddle?", "slots": {}},
    {"template": "What happened when {PARTY_MEMBER} pulled the wrong lever?", "slots": {}},
]

# =============================================================================
# LOOT_REWARDS - Treasure and items obtained
# =============================================================================

LOOT_REWARDS_TEMPLATES = [
    {"template": "What loot did we get?", "slots": {}},
    {"template": "What treasure did we find?", "slots": {}},
    {"template": "How much gold did we earn?", "slots": {}},
    {"template": "What rewards were we given?", "slots": {}},
    {"template": "What magic items did we discover?", "slots": {}},
    {"template": "How did we divide the loot?", "slots": {}},
    {"template": "What valuable items did we obtain?", "slots": {}},
    {"template": "What did the {creature} drop?", "slots": {"creature": "creature"}},
    {"template": "What quest rewards did we receive?", "slots": {}},
    {"template": "What's the total value of our haul?", "slots": {}},
    {"template": "What gems or jewels did we find?", "slots": {}},
    {"template": "What art objects did we pick up?", "slots": {}},
    {"template": "Did we find any rare items?", "slots": {}},
    {"template": "What potions were in the loot?", "slots": {}},
    {"template": "How much XP did we gain?", "slots": {}},
    {"template": "What mundane items did we loot?", "slots": {}},
    {"template": "Was there any cursed loot?", "slots": {}},
    {"template": "What treasure hoard did we find?", "slots": {}},
    {"template": "Did we find any spell scrolls?", "slots": {}},
    {"template": "What was hidden in the chest?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "What magic item did {CHARACTER} claim from the loot?", "slots": {}},
    {"template": "How much gold did {PARTY_MEMBER} get from the split?", "slots": {}},
    {"template": "What did {NPC} pay us for completing the job?", "slots": {}},
    {"template": "Did {CHARACTER} and {PARTY_MEMBER} argue over the loot?", "slots": {}},
    {"template": "What special reward did {NPC} give to {CHARACTER}?", "slots": {}},
    {"template": "How did {PARTY_MEMBER} react to their share of treasure?", "slots": {}},
    {"template": "What did {CHARACTER} loot from the boss's body?", "slots": {}},
    {"template": "Did {NPC} try to shortchange us on the reward?", "slots": {}},
    {"template": "What gems did {PARTY_MEMBER} find in the hidden compartment?", "slots": {}},
    {"template": "What non-monetary favor did {NPC} offer instead of gold?", "slots": {}},
]

# =============================================================================
# DEATH_REVIVAL - Character deaths and revivals
# =============================================================================

DEATH_REVIVAL_TEMPLATES = [
    {"template": "Did anyone die in the session?", "slots": {}},
    {"template": "Who went down?", "slots": {}},
    {"template": "How did the death happen?", "slots": {}},
    {"template": "Was anyone revived?", "slots": {}},
    {"template": "What resurrection was used?", "slots": {}},
    {"template": "Who made death saving throws?", "slots": {}},
    {"template": "How close to death did we get?", "slots": {}},
    {"template": "What brought someone back?", "slots": {}},
    {"template": "Any near-death experiences?", "slots": {}},
    {"template": "What were the consequences of dying?", "slots": {}},
    {"template": "How many death saves did someone fail?", "slots": {}},
    {"template": "Who stabilized the downed party member?", "slots": {}},
    {"template": "Did we use {spell} to bring someone back?", "slots": {"spell": "spell"}},
    {"template": "What killed the character?", "slots": {}},
    {"template": "Did the soul return willingly?", "slots": {}},
    {"template": "What resurrection components did we need?", "slots": {}},
    {"template": "Was the death permanent?", "slots": {}},
    {"template": "Did we lose any NPCs?", "slots": {}},
    {"template": "How did the party react to the death?", "slots": {}},
    {"template": "What happened while unconscious?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "Did {CHARACTER} die during the battle?", "slots": {}},
    {"template": "How many times did {PARTY_MEMBER} go unconscious?", "slots": {}},
    {"template": "Who stabilized {CHARACTER} after they went down?", "slots": {}},
    {"template": "What were {PARTY_MEMBER}'s death saving throws?", "slots": {}},
    {"template": "Did we resurrect {CHARACTER}?", "slots": {}},
    {"template": "How did {PARTY_MEMBER} save {CHARACTER} from dying?", "slots": {}},
    {"template": "What killed {CHARACTER} in that encounter?", "slots": {}},
    {"template": "Can {NPC} help us bring {PARTY_MEMBER} back?", "slots": {}},
    {"template": "What was {CHARACTER}'s last moment before falling?", "slots": {}},
    {"template": "How much did {NPC} charge to resurrect {PARTY_MEMBER}?", "slots": {}},
]

# =============================================================================
# DIVINE_RELIGIOUS - Deity interactions
# =============================================================================

DIVINE_RELIGIOUS_TEMPLATES = [
    {"template": "Did any gods intervene?", "slots": {}},
    {"template": "What divine events occurred?", "slots": {}},
    {"template": "What religious significance was there?", "slots": {}},
    {"template": "Did we visit any temples?", "slots": {}},
    {"template": "What prayers were answered?", "slots": {}},
    {"template": "What holy symbols or artifacts did we find?", "slots": {}},
    {"template": "What divine guidance did we receive?", "slots": {}},
    {"template": "Did we interact with any clerics or priests?", "slots": {}},
    {"template": "What religious factions were involved?", "slots": {}},
    {"template": "Were there any omens or signs?", "slots": {}},
    {"template": "What deity blessed us?", "slots": {}},
    {"template": "Did we make any religious offerings?", "slots": {}},
    {"template": "Were there any holy or unholy places?", "slots": {}},
    {"template": "What divine magic was used?", "slots": {}},
    {"template": "Did we break any religious taboos?", "slots": {}},
    {"template": "What celestial or fiendish beings appeared?", "slots": {}},
    {"template": "Were we cursed by a deity?", "slots": {}},
    {"template": "What religious ceremonies occurred?", "slots": {}},
    {"template": "Did anyone have a crisis of faith?", "slots": {}},
    {"template": "What sacred texts did we find?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "Did {CHARACTER} receive a vision from their deity?", "slots": {}},
    {"template": "What prayer did {PARTY_MEMBER} make at the temple?", "slots": {}},
    {"template": "How did {CHARACTER}'s god respond to their actions?", "slots": {}},
    {"template": "What did the priest {NPC} tell us about the prophecy?", "slots": {}},
    {"template": "Did {PARTY_MEMBER} have a crisis of faith?", "slots": {}},
    {"template": "What blessing did {NPC} bestow on {CHARACTER}?", "slots": {}},
    {"template": "How did {CHARACTER}'s oath affect their decision?", "slots": {}},
    {"template": "What did {PARTY_MEMBER}'s patron demand of them?", "slots": {}},
    {"template": "Did {NPC} at the temple offer us sanctuary?", "slots": {}},
    {"template": "What religious artifact did {CHARACTER} find?", "slots": {}},
]

# =============================================================================
# MEMORY_VISION - Memories, visions, dreams
# =============================================================================

MEMORY_VISION_TEMPLATES = [
    {"template": "What visions did we see?", "slots": {}},
    {"template": "What memories were revealed?", "slots": {}},
    {"template": "Did anyone have dreams?", "slots": {}},
    {"template": "What flashbacks occurred?", "slots": {}},
    {"template": "What prophetic visions happened?", "slots": {}},
    {"template": "What did the vision show?", "slots": {}},
    {"template": "What past events were revealed?", "slots": {}},
    {"template": "What did we learn from the vision?", "slots": {}},
    {"template": "Who had the vision?", "slots": {}},
    {"template": "What supernatural experiences occurred?", "slots": {}},
    {"template": "What was the nightmare about?", "slots": {}},
    {"template": "Did we see glimpses of the future?", "slots": {}},
    {"template": "What memories were unlocked?", "slots": {}},
    {"template": "Was the vision magical or natural?", "slots": {}},
    {"template": "What warning did the vision contain?", "slots": {}},
    {"template": "Did we experience someone else's memories?", "slots": {}},
    {"template": "What was symbolic in the vision?", "slots": {}},
    {"template": "How did the vision guide us?", "slots": {}},
    {"template": "What trauma was revealed?", "slots": {}},
    {"template": "Did we have shared dreams?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "What vision did {CHARACTER} experience?", "slots": {}},
    {"template": "What did {PARTY_MEMBER}'s dream reveal?", "slots": {}},
    {"template": "What memory surfaced for {CHARACTER} during the ritual?", "slots": {}},
    {"template": "What premonition did {NPC} share with us?", "slots": {}},
    {"template": "Did {PARTY_MEMBER} see anything when they touched the artifact?", "slots": {}},
    {"template": "What flashback from {CHARACTER}'s past was triggered?", "slots": {}},
    {"template": "What did {NPC}'s prophecy say about {CHARACTER}?", "slots": {}},
    {"template": "What telepathic message did {PARTY_MEMBER} receive?", "slots": {}},
    {"template": "What did {CHARACTER} see when they used Divination?", "slots": {}},
    {"template": "What omen did {NPC} warn {PARTY_MEMBER} about?", "slots": {}},
]

# =============================================================================
# RULES_MECHANICS - Rule interpretations during play
# =============================================================================

RULES_MECHANICS_TEMPLATES = [
    {"template": "What rules questions came up?", "slots": {}},
    {"template": "How did we handle that mechanic?", "slots": {}},
    {"template": "What house rules did we use?", "slots": {}},
    {"template": "How did the DM rule on that?", "slots": {}},
    {"template": "What edge cases did we encounter?", "slots": {}},
    {"template": "How did {spell} work in that situation?", "slots": {"spell": "spell"}},
    {"template": "What mechanics were unclear?", "slots": {}},
    {"template": "How did we resolve the rules dispute?", "slots": {}},
    {"template": "What ruling did we go with?", "slots": {}},
    {"template": "Were there any contested rolls?", "slots": {}},
    {"template": "Did we use flanking rules?", "slots": {}},
    {"template": "How did grappling work?", "slots": {}},
    {"template": "What skill check was required?", "slots": {}},
    {"template": "Did we use optional rules?", "slots": {}},
    {"template": "How did cover work in combat?", "slots": {}},
    {"template": "What saving throw was needed?", "slots": {}},
    {"template": "Did we use variant rules?", "slots": {}},
    {"template": "How did concentration work?", "slots": {}},
    {"template": "What ability check was contested?", "slots": {}},
    {"template": "How did opportunity attacks work?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "How did the DM rule on {CHARACTER}'s ability?", "slots": {}},
    {"template": "What mechanical interaction did {PARTY_MEMBER}'s spell have?", "slots": {}},
    {"template": "What DC did {CHARACTER} face on that saving throw?", "slots": {}},
    {"template": "Did {PARTY_MEMBER} get advantage on that attack?", "slots": {}},
    {"template": "How did {CHARACTER}'s feature interact with the environment?", "slots": {}},
    {"template": "What ruling benefited {PARTY_MEMBER} during combat?", "slots": {}},
    {"template": "Did {CHARACTER} break concentration on their spell?", "slots": {}},
    {"template": "What homebrew rule did the DM use for {PARTY_MEMBER}'s action?", "slots": {}},
    {"template": "How was {CHARACTER}'s grapple attempt resolved?", "slots": {}},
    {"template": "What skill check did {PARTY_MEMBER} have to make?", "slots": {}},
]

# =============================================================================
# HUMOR_MOMENTS - Funny moments
# =============================================================================

HUMOR_MOMENTS_TEMPLATES = [
    {"template": "What funny moments happened?", "slots": {}},
    {"template": "What made everyone laugh?", "slots": {}},
    {"template": "What were the best jokes?", "slots": {}},
    {"template": "Any memorable quotes?", "slots": {}},
    {"template": "What silly things happened?", "slots": {}},
    {"template": "What was the funniest part?", "slots": {}},
    {"template": "What critical fails were entertaining?", "slots": {}},
    {"template": "What unexpected humor occurred?", "slots": {}},
    {"template": "What running jokes continued?", "slots": {}},
    {"template": "What was the most ridiculous thing that happened?", "slots": {}},
    {"template": "What puns were made?", "slots": {}},
    {"template": "What character quirks were funny?", "slots": {}},
    {"template": "What comedic misunderstandings happened?", "slots": {}},
    {"template": "What inside jokes did we create?", "slots": {}},
    {"template": "What embarrassing moments occurred?", "slots": {}},
    {"template": "What absurd plans did we try?", "slots": {}},
    {"template": "What one-liners were memorable?", "slots": {}},
    {"template": "Did anyone break character laughing?", "slots": {}},
    {"template": "What NPC interactions were hilarious?", "slots": {}},
    {"template": "What creative solutions were unexpectedly funny?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "What hilarious thing did {CHARACTER} say?", "slots": {}},
    {"template": "What was {PARTY_MEMBER}'s epic fail moment?", "slots": {}},
    {"template": "What funny quote did {CHARACTER} deliver?", "slots": {}},
    {"template": "Did {NPC} say anything that made everyone laugh?", "slots": {}},
    {"template": "What silly decision did {PARTY_MEMBER} make?", "slots": {}},
    {"template": "What absurd thing did {CHARACTER} attempt?", "slots": {}},
    {"template": "How badly did {PARTY_MEMBER} roll on that check?", "slots": {}},
    {"template": "What running joke involves {CHARACTER}?", "slots": {}},
    {"template": "What pun did {PARTY_MEMBER} make during combat?", "slots": {}},
    {"template": "What was the funniest interaction between {CHARACTER} and {NPC}?", "slots": {}},
]

# =============================================================================
# UNRESOLVED_MYSTERIES - Ongoing mysteries
# =============================================================================

UNRESOLVED_MYSTERIES_TEMPLATES = [
    {"template": "What mysteries remain unsolved?", "slots": {}},
    {"template": "What questions do we still have?", "slots": {}},
    {"template": "What's still unknown?", "slots": {}},
    {"template": "What plot threads are hanging?", "slots": {}},
    {"template": "What didn't make sense?", "slots": {}},
    {"template": "What are we still trying to figure out?", "slots": {}},
    {"template": "What secrets weren't revealed?", "slots": {}},
    {"template": "What was left unexplained?", "slots": {}},
    {"template": "What suspicious things happened?", "slots": {}},
    {"template": "What unanswered questions came up?", "slots": {}},
    {"template": "Who is the mysterious figure?", "slots": {}},
    {"template": "What's the hidden agenda?", "slots": {}},
    {"template": "What clues haven't we connected?", "slots": {}},
    {"template": "What's the real motivation behind events?", "slots": {}},
    {"template": "What doors haven't we opened?", "slots": {}},
    {"template": "What's the villain's true plan?", "slots": {}},
    {"template": "What symbols keep appearing?", "slots": {}},
    {"template": "What patterns are we missing?", "slots": {}},
    {"template": "What's behind the locked door?", "slots": {}},
    {"template": "What rumors need investigation?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "What is {NPC} hiding from us?", "slots": {}},
    {"template": "What mystery about {CHARACTER}'s backstory came up?", "slots": {}},
    {"template": "Why did {NPC} react so strangely to {PARTY_MEMBER}?", "slots": {}},
    {"template": "What did {NPC} mean by that cryptic warning?", "slots": {}},
    {"template": "What is the connection between {CHARACTER} and {NPC}?", "slots": {}},
    {"template": "What secret is {PARTY_MEMBER} keeping from the group?", "slots": {}},
    {"template": "What did {NPC} do when we weren't watching?", "slots": {}},
    {"template": "What unexplained item did {CHARACTER} find?", "slots": {}},
    {"template": "Why did {NPC} suddenly disappear?", "slots": {}},
    {"template": "What does {PARTY_MEMBER}'s vision mean?", "slots": {}},
]

# =============================================================================
# FUTURE_IMPLICATIONS - Setup for future sessions
# =============================================================================

FUTURE_IMPLICATIONS_TEMPLATES = [
    {"template": "What's the cliffhanger?", "slots": {}},
    {"template": "What happens next?", "slots": {}},
    {"template": "What should we prepare for?", "slots": {}},
    {"template": "What threats are looming?", "slots": {}},
    {"template": "What did we set up for next time?", "slots": {}},
    {"template": "What consequences will we face?", "slots": {}},
    {"template": "What's coming in future sessions?", "slots": {}},
    {"template": "What foreshadowing happened?", "slots": {}},
    {"template": "What plans did we make?", "slots": {}},
    {"template": "Where are we heading next?", "slots": {}},
    {"template": "What enemies are still out there?", "slots": {}},
    {"template": "What promises will come due?", "slots": {}},
    {"template": "What deadlines are approaching?", "slots": {}},
    {"template": "What should we buy before next session?", "slots": {}},
    {"template": "What spells should I prepare?", "slots": {}},
    {"template": "What allies might help us?", "slots": {}},
    {"template": "What's the next logical destination?", "slots": {}},
    {"template": "What long-term consequences did we trigger?", "slots": {}},
    {"template": "What revenge plots are brewing?", "slots": {}},
    {"template": "What opportunities did we create?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "What consequences will {CHARACTER} face for their actions?", "slots": {}},
    {"template": "Will {NPC} seek revenge on us?", "slots": {}},
    {"template": "What obligation does {CHARACTER} now have to {NPC}?", "slots": {}},
    {"template": "How will {PARTY_MEMBER}'s decision affect the group later?", "slots": {}},
    {"template": "What deadline did {NPC} give us?", "slots": {}},
    {"template": "Will {CHARACTER}'s reputation change affect how {NPC} treats us?", "slots": {}},
    {"template": "What threat is growing because of {PARTY_MEMBER}'s choice?", "slots": {}},
    {"template": "When might {NPC} call in the favor we owe them?", "slots": {}},
    {"template": "What political fallout will {CHARACTER}'s actions cause?", "slots": {}},
    {"template": "What should {PARTY_MEMBER} prepare for next session?", "slots": {}},
]

# =============================================================================
# CROSS_SESSION - Multi-session patterns
# =============================================================================

CROSS_SESSION_TEMPLATES = [
    {"template": "How does this connect to previous sessions?", "slots": {}},
    {"template": "What recurring themes are there?", "slots": {}},
    {"template": "What callbacks happened?", "slots": {}},
    {"template": "How has the story evolved?", "slots": {}},
    {"template": "What long-term plots are developing?", "slots": {}},
    {"template": "What patterns have emerged?", "slots": {}},
    {"template": "How did past events influence this session?", "slots": {}},
    {"template": "What character arcs are progressing?", "slots": {}},
    {"template": "What story threads connected?", "slots": {}},
    {"template": "How does this fit the bigger picture?", "slots": {}},
    {"template": "What NPCs from before returned?", "slots": {}},
    {"template": "What items from earlier sessions were useful?", "slots": {}},
    {"template": "What consequences from earlier caught up?", "slots": {}},
    {"template": "How has my character grown?", "slots": {}},
    {"template": "What recurring villains appeared?", "slots": {}},
    {"template": "What prophecies are being fulfilled?", "slots": {}},
    {"template": "What locations did we revisit?", "slots": {}},
    {"template": "What old allies came back?", "slots": {}},
    {"template": "How is the main plot advancing?", "slots": {}},
    {"template": "What seeds planted earlier are blooming?", "slots": {}},
    # {CHARACTER}, {PARTY_MEMBER}, {NPC} placeholder templates
    {"template": "How did {CHARACTER}'s backstory connect to this session?", "slots": {}},
    {"template": "Did we see {NPC} from a previous session?", "slots": {}},
    {"template": "What callback to {CHARACTER}'s earlier decision happened?", "slots": {}},
    {"template": "How has {PARTY_MEMBER}'s character arc developed since we started?", "slots": {}},
    {"template": "Did {NPC} remember what we did to them before?", "slots": {}},
    {"template": "What old enemy of {CHARACTER} resurfaced?", "slots": {}},
    {"template": "How did {PARTY_MEMBER}'s promise from earlier sessions come up?", "slots": {}},
    {"template": "What connection does {NPC} have to {CHARACTER}'s past?", "slots": {}},
    {"template": "What item {PARTY_MEMBER} picked up sessions ago finally mattered?", "slots": {}},
    {"template": "How did {CHARACTER}'s relationship with {NPC} develop over multiple sessions?", "slots": {}},
]

# =============================================================================
# CONSOLIDATED TEMPLATES
# =============================================================================

SESSION_TEMPLATES = {
    "character_status": CHARACTER_STATUS_TEMPLATES,
    "event_sequence": EVENT_SEQUENCE_TEMPLATES,
    "npc_info": NPC_INFO_TEMPLATES,
    "location_details": LOCATION_DETAILS_TEMPLATES,
    "item_tracking": ITEM_TRACKING_TEMPLATES,
    "combat_recap": COMBAT_RECAP_TEMPLATES,
    "spell_ability_usage": SPELL_ABILITY_USAGE_TEMPLATES,
    "character_decisions": CHARACTER_DECISIONS_TEMPLATES,
    "party_dynamics": PARTY_DYNAMICS_TEMPLATES,
    "quest_tracking": QUEST_TRACKING_TEMPLATES,
    "puzzle_solutions": PUZZLE_SOLUTIONS_TEMPLATES,
    "loot_rewards": LOOT_REWARDS_TEMPLATES,
    "death_revival": DEATH_REVIVAL_TEMPLATES,
    "divine_religious": DIVINE_RELIGIOUS_TEMPLATES,
    "memory_vision": MEMORY_VISION_TEMPLATES,
    "rules_mechanics": RULES_MECHANICS_TEMPLATES,
    "humor_moments": HUMOR_MOMENTS_TEMPLATES,
    "unresolved_mysteries": UNRESOLVED_MYSTERIES_TEMPLATES,
    "future_implications": FUTURE_IMPLICATIONS_TEMPLATES,
    "cross_session": CROSS_SESSION_TEMPLATES,
}

# Intent descriptions
SESSION_INTENT_DESCRIPTIONS = {
    "character_status": "Current state of characters: HP, conditions, location, alive/dead status",
    "event_sequence": "Chronological events: what happened when, timeline of the session",
    "npc_info": "NPC interactions: who we met, relationships, conversations",
    "location_details": "Places visited: descriptions, notable features, dangers",
    "item_tracking": "Items: found, lost, used, traded, who has what",
    "combat_recap": "Combat encounters: fights, tactics, outcomes, damage",
    "spell_ability_usage": "Spells and abilities: what was cast, effects, resource usage",
    "character_decisions": "Important choices: decisions made, reasoning, consequences",
    "party_dynamics": "Group interactions: conflicts, bonding, teamwork",
    "quest_tracking": "Quest progress: completed objectives, new quests, status",
    "puzzle_solutions": "Puzzles: encountered challenges, solutions, clues",
    "loot_rewards": "Treasure: items found, gold earned, quest rewards",
    "death_revival": "Deaths and revivals: who died, how, resurrection",
    "divine_religious": "Divine events: deity interactions, temples, religious significance",
    "memory_vision": "Visions and dreams: prophetic visions, flashbacks, memories",
    "rules_mechanics": "Rules: interpretations, house rules, contested mechanics",
    "humor_moments": "Funny moments: jokes, memorable quotes, silly events",
    "unresolved_mysteries": "Mysteries: unanswered questions, plot threads, secrets",
    "future_implications": "Future setup: cliffhangers, foreshadowing, upcoming threats",
    "cross_session": "Multi-session: recurring themes, callbacks, story evolution",
}

# Slot mappings
SLOT_MAPPINGS = {
    "creature": "creature",
    "location": "location",
    "item": "item",
    "spell": "spell",
    "feature": "feature",
}


def get_all_session_templates():
    """Return all session templates as a flat list with intent labels."""
    all_templates = []
    for intent, templates in SESSION_TEMPLATES.items():
        for template in templates:
            all_templates.append({
                "template": template["template"],
                "slots": template["slots"],
                "tool": "session_notes",
                "intent": intent,
            })
    return all_templates


def get_intent_templates(intent: str):
    """Get all templates for a specific intent."""
    return SESSION_TEMPLATES.get(intent, [])
