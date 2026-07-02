# valfun.py
import requests
import base64
import os
import json
import time
import logging
import concurrent.futures
import re
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if os.path.exists(os.path.join(BASE_DIR, "logs")):
    logging.basicConfig(filename=os.path.join(BASE_DIR, "logs", 'pt.log'), filemode = 'w', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
else:
    logging.disable(logging.CRITICAL)

headers = {}
partyMembers = []
partyLevels = {}
_cached_puuid = None

TIMEOUT = 5

RANKS = {0: "Unranked", 1: "Unranked", 2: "Unused 1", 3: "Iron 1", 4: "Iron 2", 5: "Iron 3", 6: "Bronze 1", 7: "Bronze 2", 8: "Bronze 3", 9: "Silver 1", 10: "Silver 2", 11: "Silver 3", 12: "Gold 1", 13: "Gold 2", 14: "Gold 3", 15: "Platinum 1", 16: "Platinum 2", 17: "Platinum 3", 18: "Diamond 1", 19: "Diamond 2", 20: "Diamond 3", 21: "Ascendant 1", 22: "Ascendant 2", 23: "Ascendant 3", 24: "Immortal 1", 25: "Immortal 2", 26: "Immortal 3", 27: "Radiant"}
RANKS_PREASC = {0: "Unranked", 1: "Unranked", 2: "Unused 1", 3: "Iron 1", 4: "Iron 2", 5: "Iron 3", 6: "Bronze 1", 7: "Bronze 2", 8: "Bronze 3", 9: "Silver 1", 10: "Silver 2", 11: "Silver 3", 12: "Gold 1", 13: "Gold 2", 14: "Gold 3", 15: "Platinum 1", 16: "Platinum 2", 17: "Platinum 3", 18: "Diamond 1", 19: "Diamond 2", 20: "Diamond 3", 21: "Immortal 1", 22: "Immortal 2", 23: "Immortal 3", 24: "Radiant"}
PREASC_SEASONS = ["0df5adb9-4dcb-6899-1306-3e9860661dd3", "3f61c772-4560-cd3f-5d3f-a7ab5abda6b3", "0530b9c4-4980-f2ee-df5d-09864cd00542", "46ea6166-4573-1128-9cea-60a15640059b", "fcf2c8f4-4324-e50b-2e23-718e4a3ab046", "97b6e739-44cc-ffa7-49ad-398ba502ceb0", "ab57ef51-4e59-da91-cc8d-51a5a2b9b8ff", "52e9749a-429b-7060-99fe-4595426a0cf7", "71c81c67-4fae-ceb1-844c-aab2bb8710fa", "2a27e5d2-4d30-c9e2-b15a-93b8909a442c", "4cb622e1-4244-6da3-7276-8daaf1c01be2", "a16955a5-4ad0-f761-5e9e-389df1c892fb", "97b39124-46ce-8b55-8fd1-7cbf7ffe173f", "573f53ac-41a5-3a7d-d9ce-d6a6298e5704", "d929bc38-4ab6-7da4-94f0-ee84f8ac141e", "3e47230a-463c-a301-eb7d-67bb60357d4f", "808202d6-4f2b-a8ff-1feb-b3a0590ad79f"]


def basic_auth(password):
    return 'Basic ' + base64.b64encode(f'riot:{password}'.encode()).decode()

def get_lockfile():
    try:
        with open(os.path.join(os.getenv('LOCALAPPDATA'), R'Riot Games\Riot Client\Config\lockfile')) as lockfile:
            data = lockfile.read().split(':')
            keys = ['name', 'PID', 'port', 'password', 'protocol']
            logging.info("Lockfile found.")
            return dict(zip(keys, data))
    except Exception:
        print("VALORANT is not running. (Lockfile not found)")
        logging.error("Lockfile not found.")
        input("Press enter to exit.")
        exit()        
        # raise Exception("Lockfile not found")

lockfile = get_lockfile()

def get_current_version():
    try:
        path = os.path.join(os.getenv('LOCALAPPDATA'), R'VALORANT\Saved\Logs\ShooterGame.log')
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.search(r'CI server version: (.+)', line)
                if match:
                    version = match.group(1).strip()
                    logging.info(f"Current version (from log): {version}")
                    return version
    except Exception as e:
        logging.warning(f"Could not read version from log: {e}")
    data = requests.get('https://valorant-api.com/v1/version', timeout=TIMEOUT).json()['data']
    version = f"{data['branch']}-shipping-{data['buildVersion']}-{data['version'].split('.')[3]}"
    logging.info(f"Current version (from API): {version}")
    return version

def get_headers(update=False):
    global headers
    if headers == {} or update == True:
        local_headers = {}
        local_headers['Authorization'] = basic_auth(lockfile['password'])
        response = requests.get(f"https://127.0.0.1:{lockfile['port']}/entitlements/v1/token", headers=local_headers, verify=False, timeout=TIMEOUT)
        entitlements = response.json()
        headers = {
            'Authorization': f"Bearer {entitlements['accessToken']}",
            'X-Riot-Entitlements-JWT': entitlements['token'],
            'X-Riot-ClientPlatform': "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9",
            'X-Riot-ClientVersion': globVersion,
        }
        if update == True:
            logging.info("Headers updated.")
        else:
            logging.info("Headers created.")
    return headers

def get_puuid():
    global _cached_puuid
    if _cached_puuid:
        return _cached_puuid
    local_headers = {'Authorization': basic_auth(lockfile['password'])}
    try:
        response = requests.get(f"https://127.0.0.1:{lockfile['port']}/entitlements/v1/token", headers=local_headers, verify=False, timeout=TIMEOUT)
        _cached_puuid = response.json()['subject']
        return _cached_puuid
    except Exception as e:
        logging.error(f"Could not get puuid: {e}")
        return None

def get_all_agents():
    agent_dict = {}
    response = requests.get("https://valorant-api.com/v1/agents?isPlayableCharacter=true", timeout=TIMEOUT)
    for agent in response.json()['data']:
        agent_dict.update({agent['uuid']: agent['displayName']})
    logging.info("Agents fetched.")
    return agent_dict

def get_coregame_match_id():
    try:
        response = requests.get(f"https://glz-{globRegion}-1.{globRegion}.a.pvp.net/core-game/v1/players/{get_puuid()}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
        match_id = response['MatchID']
        logging.info(f"Match ID: {match_id}")
        return match_id
    except KeyError:
        print(f"No match id found. {response}")
        logging.error(f"No match id found. {response}")
        return 0

def get_coregame_stats(match_id):
    response = requests.get(f"https://glz-{globRegion}-1.{globRegion}.a.pvp.net/core-game/v1/matches/{match_id}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
    logging.info("Core game stats fetched.")
    return response


def get_pregame_match_id():
    try:
        response = requests.get(f"https://glz-{globRegion}-1.{globRegion}.a.pvp.net/pregame/v1/players/{get_puuid()}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
        match_id = response['MatchID']
        logging.info(f"Pregame match ID: {match_id}")
        return match_id
    except KeyError:
        print(f"No match id found. {response}")
        logging.error(f"No match id found. {response}")
        return 0

def get_pregame_stats(match_id):
    response = requests.get(f"https://glz-{globRegion}-1.{globRegion}.a.pvp.net/pregame/v1/matches/{match_id}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
    logging.info("Pregame stats fetched.")
    return response

def get_most_recent_match():
    response = requests.get(f"https://pd.{globRegion}.a.pvp.net/match-history/v1/history/{get_puuid()}?startIndex=0&endIndex=1", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
    logging.info("Most recent match fetched.")
    return response['History'][0]['MatchID']

def get_match_by_id():
    response = requests.get(f"https://pd.{globRegion}.a.pvp.net/match-details/v1/matches/{get_most_recent_match()}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
    logging.info("Match by ID fetched.")
    return response

def get_players_in_lobby_puuid(currgame="post", match_id=None):
    players = []
    if currgame == "core":
        coregame_stats = get_coregame_stats(match_id)
        logging.info("getting coregame stats")
    elif currgame == "pregame":
        coregame_stats = get_pregame_stats(match_id)
        logging.info("getting pregame stats")
    else:
        coregame_stats = get_match_by_id()
        logging.info("getting match by id")
    try:
        if currgame == "core":
            for player in coregame_stats["Players"]:
                players.append([
                    player["Subject"],
                    player["CharacterID"],
                    player["PlayerIdentity"]["Incognito"],
                    player["TeamID"],
                    player["PlayerIdentity"]["AccountLevel"],
                    player["PlayerIdentity"]["HideAccountLevel"],
                ])
                logging.info("got a player in coregame")
        elif currgame == "pregame":
            for idx, player in enumerate(coregame_stats["AllyTeam"]["Players"]):
                players.append([
                    player["Subject"],
                    player["CharacterID"],
                    player["PlayerIdentity"]["Incognito"],
                    player["PlayerIdentity"]["AccountLevel"],
                    player["PlayerIdentity"]["HideAccountLevel"],
                    idx,
                ])
                logging.info("got a player in pregame")
        else:
            for player in coregame_stats["players"]:
                players.append([
                    player["subject"],
                    player["characterId"],
                    player["teamId"],
                    player["accountLevel"],
                ])
                logging.info("got a player in match by id")
    except KeyError:
        logging.error(f"something went wrong in getting stats")
        return players
    return players

def get_current_rank(puuid):
    try:
        response = requests.get(f"https://pd.{globRegion}.a.pvp.net/mmr/v1/players/{puuid}/competitiveupdates?startIndex=0&endIndex=20&queue=competitive", headers=get_headers(), verify=False, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json() 

        if "Matches" in data:
            if data["Matches"]:
                logging.info(f"got rank data for {puuid}")
                rank = RANKS[data["Matches"][0]["TierAfterUpdate"]]
                return [rank, data["Matches"][0]["RankedRatingAfterUpdate"]]
            else:
                return ["Unranked", 0]
        else:
            print(f"Unexpected response format: {data}")
            return ["Unranked", 0]

    except requests.exceptions.RequestException as e:
        print(f"Ratelimited! (Some ranks will show as unranked)")
        logging.error(f"ratelimited!!!!!!!!! {e}")
        return ["Unranked", 0]

    except json.decoder.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return ["Unranked", 0]

def get_name_tag_from_puuid(puuid):
    response = requests.put(f"https://pd.{globRegion}.a.pvp.net/name-service/v2/players", headers=get_headers(), json=[puuid], verify=False, timeout=TIMEOUT)
    entry = response.json()[0]
    logging.info(f"got name/tag for {puuid} ({entry['GameName']}#{entry['TagLine']})")
    return entry["GameName"], entry["TagLine"]

def get_name_from_puuid(puuid):
    return get_name_tag_from_puuid(puuid)[0]

def get_tag_from_puuid(puuid):
    return get_name_tag_from_puuid(puuid)[1]

def get_peak_rank(puuid):
    try:
        response = requests.get(f"https://pd.{globRegion}.a.pvp.net/mmr/v1/players/{puuid}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
        if not response['QueueSkills']['competitive']['SeasonalInfoBySeasonID']:
            logging.info(f"No peak rank data for {puuid}")
            return "Unranked"
    except json.decoder.JSONDecodeError as e:
        logging.error(f"Error decoding JSON, shows as unranked: {e}")
        return "Unranked"
    except requests.exceptions.RequestException as e:
        print("Ratelimited! (Some peak ranks will show as unranked)")
        logging.error(f"request exception, shows as unranked: {e}")
        return "Unranked"
    try:
        maxRank = float('-inf')
        for season_id, season_data in response['QueueSkills']['competitive']['SeasonalInfoBySeasonID'].items():
            rank = season_data['Rank']
            if rank > maxRank:
                maxRank = rank
                maxRankSeason = season_id
        allRanks = RANKS_PREASC if maxRankSeason in PREASC_SEASONS else RANKS
        peakRank = allRanks[maxRank]
        
        for season in globSeasons['data']:
            if season['uuid'] == maxRankSeason:
                rq = season
                break
        seasonName = rq['assetPath'].replace("ShooterGame/Content/Seasons/Season_Episode", "e").replace("_Act", "a").split("_")[0]
        seasonName = re.sub(r'-.', '', seasonName)
        logging.info(f"Peak rank for {puuid}: {peakRank} ({seasonName})")
        return peakRank + f" [bright_white]({seasonName})"
    
    except Exception as e:
        logging.error(f"catch all, shows as unranked: {e}")
        return "Unranked"

loadouts = {}

def get_loadouts(match_id):
    global loadouts
    vanskin = requests.get(f"https://glz-{globRegion}-1.{globRegion}.a.pvp.net/core-game/v1/matches/{match_id}/loadouts", headers=get_headers(), verify=False, timeout=TIMEOUT)
    if vanskin.status_code == 200:
        loadouts = vanskin.json()
        logging.info("Loadouts fetched.")

def fetch_skin(skinID):
    response = globSkins['data']
    skin_name = "New Skin"
    for skin in response:
        if skin['uuid'] == skinID:
            skin_name = skin['displayName']

    skin_name = skin_name.replace("Vandal", "").replace("Phantom", "").strip()
    return skin_name

def get_skins():
    skins = {}
    
    vandal_ids = []
    phantom_ids = []
    subjects = []
    
    for character in loadouts['Loadouts']:
        vandalID = character['Loadout']['Items']['9c82e19d-4575-0200-1a81-3eacf00cf872']['Sockets']['bcef87d6-209b-46c6-8b19-fbe40bd95abc']['Item']['ID']
        phantomID = character['Loadout']['Items']['ee8e8d15-496b-07ac-e5f6-8fae5d4c7b1a']['Sockets']['bcef87d6-209b-46c6-8b19-fbe40bd95abc']['Item']['ID']
        vandal_ids.append(vandalID)
        phantom_ids.append(phantomID)
        subjects.append(character['Loadout']['Subject'])
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        vandal_results = list(executor.map(fetch_skin, vandal_ids))
        phantom_results = list(executor.map(fetch_skin, phantom_ids))
    
    for subject, vandal_skin, phantom_skin in zip(subjects, vandal_results, phantom_results):
        skin_str = f"{vandal_skin} / {phantom_skin}"
        skins[subject] = skin_str[0:30] + "..." if len(skin_str) > 30 else skin_str
        logging.info(f"Got skins for {subject} - Vandal: {vandal_skin}, Phantom: {phantom_skin}")
    
    logging.info("Skins fetched.")
    return skins
       
def get_map_name(match_id):
    try:
        response = requests.get(f"https://glz-{globRegion}-1.{globRegion}.a.pvp.net/core-game/v1/matches/{match_id}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
        map_name = response['MapID']
        server = response['GamePodID']
        servername = globServers[server]
        logging.info(f"Server: {servername}")
        response = globMaps
        for map in response['data']:
            if map['mapUrl'] == map_name:
                logging.info(f"Map name: {map['displayName']}")
                return map['displayName'], servername
        logging.warning(f"Map ID {map_name} not found in API data.")
        return "New Map", servername
    except KeyError as e:
        logging.error(f"Error fetching map name: {e}")
        return "New Map", "Unknown Server"

def get_rank_color(rank):
    rank_colors = {
        "Iron": "rgb(175,175,175)",
        "Bronze": "rgb(175,135,135)",
        "Silver": "rgb(255,255,255)",
        "Gold": "rgb(215,175,0)",
        "Platinum": "rgb(135,215,255)",
        "Diamond": "rgb(175,135,255)",
        "Ascendant": "rgb(95,255,175)",
        "Immortal": "rgb(255,0,0)",
        "Radiant": "rgb(255,255,215)",  
    }
    return rank_colors.get(rank, "rgb(255,255,255)")

def check_coregame():
        try:
            response = requests.get(f"https://glz-{globRegion}-1.{globRegion}.a.pvp.net/core-game/v1/players/{get_puuid()}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
        except Exception:
            exit()
        if "httpStatus" in response:
            logging.info("Not in core game.")
            return False
        else:
            logging.info("In core game.")
            return True

def check_pregame():
        try:
            response = requests.get(f"https://glz-{globRegion}-1.{globRegion}.a.pvp.net/pregame/v1/players/{get_puuid()}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
        except Exception:
            exit()
        if "httpStatus" in response:
            logging.info("Not in pregame.")
            return False
        else:
            logging.info("In pregame.")
            return True

def get_party_members():
    global partyMembers, partyLevels
    partyMembers = []
    partyLevels = {}
    try:
        partyID = requests.get(f"https://glz-{globRegion}-1.{globRegion}.a.pvp.net/parties/v1/players/{get_puuid()}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
        logging.info(f"Party ID: {partyID['CurrentPartyID']}")
        partydetails = requests.get(f"https://glz-{globRegion}-1.{globRegion}.a.pvp.net/parties/v1/parties/{partyID['CurrentPartyID']}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
        members = partydetails['Members']
        logging.info(f"Party details found")
        for member in members:
            partyMembers.append(member['Subject'])
            partyLevels[member['Subject']] = member['PlayerIdentity']['AccountLevel']
        logging.info(f"Party members: {partyMembers}")
        return partyMembers

    except Exception as e:
        logging.exception(f"Could not fetch party members: {e}")

def get_level_from_puuid(puuid):
    response = requests.get(f"https://pd-{globRegion}-1.{globRegion}.a.pvp.net/account-xp/v1/players/{puuid}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
    logging.info("got level")
    return response['Progress']['Level']

def get_specific_users_match(puuid):
    response = requests.get(
        f"https://pd-{globRegion}-1.{globRegion}.a.pvp.net/match-history/v1/history/{puuid}?startIndex=0&endIndex=1", headers=get_headers(),
        verify=False, timeout=TIMEOUT).json()
    logging.info("got specific user's match")
    matchID = response['History'][0]['MatchID']

    response = requests.get(
        f"https://pd-{globRegion}-1.{globRegion}.a.pvp.net/match-details/v1/matches/{matchID}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()
    return response

def get_party_level(puuid):
    if puuid in partyLevels:
        return partyLevels[puuid]
    try:
        party_id = requests.get(f"https://glz-{globRegion}-1.{globRegion}.a.pvp.net/parties/v1/players/{get_puuid()}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()['CurrentPartyID']
        response = requests.get(f"https://glz-{globRegion}-1.{globRegion}.a.pvp.net/parties/v1/parties/{party_id}", headers=get_headers(), verify=False, timeout=TIMEOUT).json()

        for member in response['Members']:
            if member['Subject'] == puuid:
                partyLevels[puuid] = member['PlayerIdentity']['AccountLevel']
                return partyLevels[puuid]
    except Exception as e:
        logging.error(f"Error getting party level: {e}")
        return "XX"
    
def get_attdef(match_id):
    stats = get_pregame_stats(match_id)
    if stats['AllyTeam']['TeamID'] == "Blue":
        doing = "Defending"
    else:
        doing = "Attacking"
    logging.info(f"got attacking or defending: {doing}")
    return doing

def get_party_change():
    current = get_party_members()
    if current is not None and partyMembers != current:
        logging.info(f"Party members changed: {partyMembers} -> {current}")
        return True
    logging.info("No party change/None")
    return False

def getRegion():
    try:
        path = os.path.join(os.getenv('LOCALAPPDATA'), R'VALORANT\Saved\Logs\ShooterGame.log')
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.search(r'glz-(.+?)-1\.(.+?)\.a\.pvp\.net', line)
                if match:
                    region = match.group(2)
                    logging.info(f"Region found: {region}")
                    return region if region in {"eu", "ap", "kr"} else "na"
    except Exception as e:
        logging.warning(f"Could not determine region: {e}")

def preload_all():
    global globVersion, globSkins, globAgents, globMaps, globSeasons, globServers, globRegion
    globVersion = get_current_version()
    globAgents = get_all_agents()
    globSkins = requests.get("https://valorant-api.com/v1/weapons/skins/", timeout=TIMEOUT).json()
    globMaps = requests.get("https://valorant-api.com/v1/maps/", timeout=TIMEOUT).json()
    globSeasons = requests.get("https://valorant-api.com/v1/seasons/", timeout=TIMEOUT).json()
    globServers = requests.get("https://ptvs.vercel.app/servers.json", timeout=TIMEOUT).json()
    globRegion = getRegion()
    logging.info("Preloaded all data.")
