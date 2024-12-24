# commands.py
import sys
import urllib3
from rich.console import Console
from rich.table import Table
from valfun import *
from concurrent.futures import ThreadPoolExecutor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()

def print_core_table(players, header):
    console = Console()

    def process_player(player):
        rank_puuid = get_current_rank_from_puuid(player[0])
        peak_rank = get_peak_rank(player[0])
        playerAgent = agent_dict.get(player[1].lower(), 'N/A')
        partied = ""
        if str(player[2]) == "True" and player[0] != get_puuid() and player[0] not in party_members:
            player_name = playerAgent
        elif player[0] == party_members:
            player_name = get_name_from_puuid(player[0])
        else:
            player_name = get_name_from_puuid(player[0])
        if player[0] in party_members:
            partied = "[orange_red1]*[/]"
        else:
            partied = ""

        skin = skins.get(player[0], "Standard Vandal")

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
            f"{player[4]}",
            f"{skin}"
        )

    with ThreadPoolExecutor() as executor:
        rows = list(executor.map(process_player, players))

    table = Table(title=f"{header}")
    table.add_column("Name", style="blue_violet", justify="center", no_wrap=True)
    table.add_column("Agent", style="dark_orange", justify="center", no_wrap=True)
    table.add_column("Rank (RR)", style="green", justify="center", no_wrap=True)
    table.add_column("Peak Rank", style="yellow", justify="center", no_wrap=True)
    table.add_column("Level", style="blue_violet", justify="center", no_wrap=True)
    table.add_column("Vandal Skin", style="white", justify="center", no_wrap=True)

    for row in rows:
        table.add_row(*row)

    console.print(table)

def print_pre_table(players, header):
    console = Console()
    def pre_process_player(player):
        rank_puuid = get_current_rank_from_puuid(player[0])
        peak_rank = get_peak_rank(player[0])
        partied = ""
        if str(player[2]) == "True" and player[0] != get_puuid() and player[0] not in party_members:
            player_name = f"Player"
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
        if peak_rank == "Unranked" and rank_puuid[0] != "Unranked":
            peak_rank = rank_puuid[0]
            peak_rank_color = rank_color
            
        return (
            f"{player_name}{partied}",
            f"[{rank_color}]{rank_puuid[0]} ({rank_puuid[1]})",
            f"[{peak_rank_color}]{peak_rank}",
            f"{player[3]}",
        )
    
    with ThreadPoolExecutor() as executor:
        rows = list(executor.map(pre_process_player, players))

    table = Table(title=f"{header}")
    table.add_column("Name", style="cyan", justify="center", no_wrap=True)
    table.add_column("Rank (RR)", style="green", justify="center", no_wrap=True)
    table.add_column("Peak Rank", style="yellow", justify="center", no_wrap=True)
    table.add_column("Level", style="blue_violet", justify="center", no_wrap=True)

    for row in rows:
        table.add_row(*row)

    console.print(table)

def core():
    global current_game_match_id, skins, agent_dict, map, party_members
    current_game_match_id = get_coregame_match_id()
    get_loadouts()
    skins = get_skins()
    get_all_agents_and_uuids()
    map = get_map_name()
    agent_dict = get_all_agents(reverse=True)
    party_members = get_party_members()
    if map == "The Range":
        print("The Range")
    else: 
        all_players = [player for player in get_players_in_lobby_puuid(currgame="core")]
        print_core_table(all_players, f"In game - {map}")

def pre():
    global current_game_match_id, party_members
    current_game_match_id = get_pregame_match_id()
    players = [player for player in get_players_in_lobby_puuid(currgame="pregame")]
    attordef = get_attdef()
    party_members = get_party_members()
    print_pre_table(players, f"Agent Select ({attordef})")

def party():
    global party_puuids, party_members
    party_puuids = get_party_members()
    party_players = []
    party_members = get_party_members()
    for puuid in party_puuids:
        player_info = [
        puuid,
        "N/A",  
        "False",
        get_party_level(puuid)
        ]
        party_players.append(player_info)
    print_pre_table(party_players, "Party")

if len(sys.argv) > 1:
    if sys.argv[1].lower() == "--core":
        core()
    elif sys.argv[1].lower() == "--pre":
        pre()
    elif sys.argv[1].lower() == "--party":
        party()

else:
    pythonPath = sys.executable.split('\\')[-1]
    print(f"Usage: {pythonPath} commands.py [--core | --pre | --party]")
