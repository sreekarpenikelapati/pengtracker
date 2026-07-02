# commands.py
import sys
import urllib3
from rich.console import Console
from rich.table import Table
import valfun
from valfun import *
from concurrent.futures import ThreadPoolExecutor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()

def print_core_table(players, header):
    with console.status("", spinner="aesthetic"):
        def process_player(player):
            rank_puuid = get_current_rank(player[0])
            peak_rank = get_peak_rank(player[0])
            playerAgent = agent_dict.get(player[1].lower(), 'N/A')

            if player[2] and player[0] not in party_members:
                player_name = playerAgent
            else:
                player_name = get_name_from_puuid(player[0])
            partied = "[orange_red1]*[/]" if player[0] in party_members else ""

            skin = skins.get(player[0], "Standard Vandal")
            if player[0] in party_members:
                level = get_party_level(player[0])
            elif player[5] == True:
                level = "XX"
            else:
                level = player[4]
            name_color = "bright_red" if player[3].lower() == "red" else "dodger_blue2"
            splitrank = rank_puuid[0].split(" ")[0]
            peaksplitrank = peak_rank.split(" ")[0]
            rank_color = get_rank_color(splitrank)
            peak_rank_color = get_rank_color(peaksplitrank)
            if peak_rank == "Unranked" and rank_puuid[0] != "Unranked":
                peak_rank = rank_puuid[0]
                peak_rank_color = rank_color

            return (
                f"[{name_color}]{player_name}{partied}[/{name_color}]",
                f"{agent_dict.get(player[1].lower(), 'N/A')}",
                f"[{rank_color}]{rank_puuid[0]} ({rank_puuid[1]})[/]",
                f"[{peak_rank_color}]{peak_rank}[/]",
                f"{level}",
                f"{skin}"
            )

        with ThreadPoolExecutor() as executor:
            rows = list(executor.map(process_player, players))

        table = Table(title=f"{header}")
        table.add_column("Name", style="blue_violet", justify="left", no_wrap=True)
        table.add_column("Agent", style="dark_orange", justify="left", no_wrap=True)
        table.add_column("Rank (RR)", style="green", justify="left", no_wrap=True)
        table.add_column("Peak Rank (SZN)", style="yellow", justify="left", no_wrap=True)
        table.add_column("Level", style="blue_violet", justify="left", no_wrap=True)
        table.add_column("Vandal/Phantom Skin", style="white", justify="left", no_wrap=True)

        for row in rows:
            table.add_row(*row)

    console.print(table)

def print_pre_table(players, header):
    with console.status("", spinner="aesthetic"):
        def pre_process_player(player):
            rank_puuid = get_current_rank(player[0])
            peak_rank = get_peak_rank(player[0])
            partied = ""
            if str(player[2]) == "True" and player[0] != get_puuid() and player[0] not in party_members:
                player_name = f"Player {player[5]+1}"
            else:
                player_name = get_name_from_puuid(player[0])
            if player[0] in party_members:
                partied = "[orange_red1]*[/]"
            else:
                partied = ""
            splitrank = rank_puuid[0].split(" ")[0]
            peaksplitrank = peak_rank.split(" ")[0]
            rank_color = get_rank_color(splitrank)
            peak_rank_color = get_rank_color(peaksplitrank)
            if player[0] in party_members:
                player[3] = get_party_level(player[0])
            elif player[4] == True:
                player[3] = "XX"
            return (
                f"{player_name}{partied}",
                f"[{rank_color}]{rank_puuid[0]} ({rank_puuid[1]})",
                f"[{peak_rank_color}]{peak_rank}",
                f"{player[3]}",
            )
        
        with ThreadPoolExecutor() as executor:
            rows = list(executor.map(pre_process_player, players))

        table = Table(title=f"{header}")
        table.add_column("Name", style="cyan", justify="left", no_wrap=True)
        table.add_column("Rank (RR)", style="green", justify="left", no_wrap=True)
        table.add_column("Peak Rank (SZN)", style="yellow", justify="left", no_wrap=True)
        table.add_column("Level", style="blue_violet", justify="left", no_wrap=True)

        for row in rows:
            table.add_row(*row)

    console.print(table)

def core():
    get_headers(update=True)
    global current_game_match_id, skins, agent_dict, map, party_members
    current_game_match_id = get_coregame_match_id()
    get_loadouts(current_game_match_id)
    skins = get_skins()
    map, server = get_map_name(current_game_match_id)
    agent_dict = valfun.globAgents
    party_members = get_party_members()
    all_players = [player for player in get_players_in_lobby_puuid(currgame="core", match_id=current_game_match_id)]
    all_players.sort(key=lambda x: x[3].lower())
    print_core_table(all_players, f"{map} - {server}")

def pre():
    get_headers(update=True)
    global current_game_match_id, party_members
    current_game_match_id = get_pregame_match_id()
    players = [player for player in get_players_in_lobby_puuid(currgame="pregame", match_id=current_game_match_id)]
    what = get_attdef(current_game_match_id)
    party_members = get_party_members()
    print_pre_table(players, f"Agent Select ({what})")

def party():
    get_headers(update=True)
    global party_members
    party_players = []
    party_members = get_party_members()
    if not party_members:
        for _ in range(5):
            party_members = get_party_members()
            if party_members:
                break
            time.sleep(3)
    for puuid in party_members:
        player_info = [
        puuid,
        "N/A",  
        "False",
        get_party_level(puuid)
        ]
        party_players.append(player_info)
    print_pre_table(party_players, "Party")
