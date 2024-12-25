# Pengtracker

Pengtracker is a Python application that displays a user's game statistics inside of VALORANT. Based on the user's game state, Pengtracker will show Party, Pregame (Agent Select), or Coregame statistics.

Pengtracker utilizes the Websockets, Requests, Concurrent Futures, and Rich to create a clean visualization of the statistics of users in real time.

## Features
- Privacy: Recognizes name and level privacy.
- Speed: Concurrent processing allows for fast results
- Party: Distinction of current user's group

## Screenshots
![Party](https://github.com/sreekarpenikelapati/pengtracker/blob/main/Screenshots/Party.png?raw=true)
### Party: Name, Rank (Rank Rating), Peak Rank (Episode and Act), and Level.
#
![Agent Select](https://github.com/sreekarpenikelapati/pengtracker/blob/main/Screenshots/AgentSelect.png?raw=true)
### Agent Selection: Name, Rank (Rank Rating), Peak Rank (Episode and Act), and Level. Additionally includes whether user's team is attacking or defending in the beginning of the game in the title.
#
![Coregame](https://github.com/sreekarpenikelapati/pengtracker/blob/main/Screenshots/Coregame.png?raw=true)
### Coregame: Name, Agent, Rank (Rank Rating), Peak Rank (Episode and Act), Level, Vandal/Phantom Skin. Additionally includes map name and server in the title. Split into red and blue teams based on the players' team.
#
![Match](https://github.com/sreekarpenikelapati/pengtracker/blob/main/Screenshots/Match.png?raw=true)
### This is an example match. "*" indicates players in the user's group/party. Users with their name hidden will have their name shown as their agent. Users with their level hidden will be given "XX".

