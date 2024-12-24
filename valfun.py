# valfun.py
import requests
import base64
import os
import sys
import json
import time
import logging
import concurrent.futures

logging.basicConfig(filename='./logs/pengtrackerlogs.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


try:
    region = sys.argv[2].lower()
    glz_url = f"https://glz-{region}-1.{region}.a.pvp.net"
    pd_url = f"https://pd.{region}.a.pvp.net"
except:
    pass
headers = {}

def get_lockfile():
    try:
        with open(os.path.join(os.getenv('LOCALAPPDATA'), R'Riot Games\Riot Client\Config\lockfile')) as lockfile:
            data = lockfile.read().split(':')
            keys = ['name', 'PID', 'port', 'password', 'protocol']
            logging.info("Lockfile found.")
            return dict(zip(keys, data))
    except:
        print("VALORANT is not running. (Lockfile not found)")
        logging.error("Lockfile not found.")
        input("Press enter to exit.")
        exit()        
        # raise Exception("Lockfile not found")

lockfile = get_lockfile()

def get_current_version():
    data = requests.get('https://valorant-api.com/v1/version')
    data = data.json()['data']
    version = f"{data['branch']}-shipping-{data['buildVersion']}-{data['version'].split('.')[3]}"
    logging.info(f"Current version: {version}")
    return version

def get_headers():
    global headers
    if headers == {}:
        local_headers = {}
        local_headers['Authorization'] = 'Basic ' + base64.b64encode(
            ('riot:' + lockfile['password']).encode()).decode()
        response = requests.get(f"https://127.0.0.1:{lockfile['port']}/entitlements/v1/token", headers=local_headers,
                                verify=False)
        entitlements = response.json()
        headers = {
            'Authorization': f"Bearer {entitlements['accessToken']}",
            'X-Riot-Entitlements-JWT': entitlements['token'],
            'X-Riot-ClientPlatform': "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9",
            'X-Riot-ClientVersion': get_current_version()
        }
        logging.info("Headers created.")
    return headers

def get_puuid():
    local_headers = {}
    local_headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('riot:' + lockfile['password']).encode()).decode()
    try:
        response = requests.get(f"https://127.0.0.1:{lockfile['port']}/entitlements/v1/token", headers=local_headers,
                            verify=False)
    except:
        print("no puuid?")
    entitlements = response.json()
    puuid = entitlements['subject']
    return puuid

def get_all_agents(reverse=False):
    agent_dict = {}
    response = requests.get("https://valorant-api.com/v1/agents")
    if reverse == False:
        for agent in response.json()['data']:
            agent_dict.update({agent['displayName']: agent['uuid']})
    else:
        for agent in response.json()['data']:
            agent_dict.update({agent['uuid']: agent['displayName']})
    logging.info("Agents fetched.")
    return agent_dict

def get_coregame_match_id():
    glz_url = f"https://glz-na-1.na.a.pvp.net"
    try:
        response = requests.get(
            glz_url + f"/core-game/v1/players/{get_puuid()}", headers=get_headers(), verify=False).json()
        match_id = response['MatchID']
        logging.info(f"Match ID: {match_id}")
        return match_id
    except KeyError:
        print(f"No match id found. {response}")
        logging.error(f"No match id found. {response}")
        return 0

def get_coregame_stats():
    glz_url = f"https://glz-na-1.na.a.pvp.net"
    response = requests.get(
        glz_url + f"/core-game/v1/matches/{get_coregame_match_id()}", headers=get_headers(), verify=False).json()
    logging.info("Core game stats fetched.")
    return response


def get_pregame_match_id():
    glz_url = f"https://glz-na-1.na.a.pvp.net"
    try:
        response = requests.get(
            glz_url + f"/pregame/v1/players/{get_puuid()}", headers=get_headers(), verify=False).json()
        match_id = response['MatchID']
        logging.info(f"Pregame match ID: {match_id}")
        return match_id
    except KeyError:
        print(f"No match id found. {response}")
        logging.error(f"No match id found. {response}")
        return 0

def get_pregame_stats():
    glz_url = f"https://glz-na-1.na.a.pvp.net"
    response = requests.get(
        glz_url + f"/pregame/v1/matches/{get_pregame_match_id()}", headers=get_headers(), verify=False).json()
    logging.info("Pregame stats fetched.")
    return response

def get_most_recent_match():
    pd_url = f"https://pd.na.a.pvp.net"
    response = requests.get(
        pd_url + f"/match-history/v1/history/{get_puuid()}?startIndex=0&endIndex=1", headers=get_headers(),
        verify=False).json()
    logging.info("Most recent match fetched.")
    return response['History'][0]['MatchID']

def get_match_by_id():
    pd_url = f"https://pd.na.a.pvp.net"
    response = requests.get(
        pd_url + f"/match-details/v1/matches/{get_most_recent_match()}", headers=get_headers(), verify=False).json()
    logging.info("Match by ID fetched.")
    return response

def get_players_in_lobby_puuid(currgame="post"):
    players = []
    if currgame == "core":
        coregame_stats = get_coregame_stats()
        logging.info("getting coregame stats")
    elif currgame == "pregame":
        coregame_stats = get_pregame_stats()
        logging.info("getting pregame stats")
    else:
        coregame_stats = get_match_by_id()
        logging.info("getting match by id")
    i = 0
    try:
        if currgame == "core":
            for player in coregame_stats["Players"]:
                players.append([])
                players[i].append(player["Subject"])
                players[i].append(player["CharacterID"])
                players[i].append(player["PlayerIdentity"]["Incognito"])
                players[i].append(player["TeamID"])
                players[i].append(player["PlayerIdentity"]["AccountLevel"])
                i += 1
                logging.info("got a player in coregame")
        elif currgame == "pregame":
            for player in coregame_stats["AllyTeam"]["Players"]:
                players.append([])
                players[i].append(player["Subject"])
                players[i].append(player["CharacterID"])
                players[i].append(player["PlayerIdentity"]["Incognito"])
                players[i].append(player["PlayerIdentity"]["AccountLevel"])
                i += 1
                logging.info("got a player in pregame")
        else:
            for player in coregame_stats["players"]:
                players.append([])
                players[i].append(player["subject"])
                players[i].append(player["characterId"])
                players[i].append(player["teamId"])
                players[i].append(player["accountLevel"])
                i += 1
                logging.info("got a player in match by id")
    except KeyError:
        logging.error(f"something went wrong in getting stats")
        return players
    return players

def get_current_rank_from_puuid(puuid, all=False):
    pd_url = f"https://pd.na.a.pvp.net"
    try:
        response = requests.get(
            pd_url + f"/mmr/v1/players/{puuid}/competitiveupdates?startIndex=0&endIndex=20&queue=competitive",
            headers=get_headers(), verify=False)
        response.raise_for_status()
        data = response.json() 

        if "Matches" in data:
            if data["Matches"]:
                logging.info(f"got rank data for {puuid}")
                allRanks = {0: "Unranked", 1: "Unranked", 2: "Unused 1", 3: "Iron 1", 4: "Iron 2", 5: "Iron 3", 6: "Bronze 1", 7: "Bronze 2", 8: "Bronze 3", 9: "Silver 1", 10: "Silver 2", 11: "Silver 3", 12: "Gold 1", 13: "Gold 2", 14: "Gold 3", 15: "Platinum 1", 16: "Platinum 2", 17: "Platinum 3", 18: "Diamond 1", 19: "Diamond 2", 20: "Diamond 3", 21: "Ascendant 1", 22: "Ascendant 2", 23: "Ascendant 3", 24: "Immortal 1", 25: "Immortal 2", 26: "Immortal 3", 27: "Radiant"}
                rank = allRanks[data["Matches"][0]["TierAfterUpdate"]]
                return [rank, data["Matches"][0]["RankedRatingAfterUpdate"]]
            else:
                return ["Unranked", 0]
        else:
            print(f"Unexpected response format: {data}")
            return ["Unranked", 0]

    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e} (ratelimit?)")
        logging.error(f"ratelimited {e}")
        return ["Unranked", 0]

    except json.decoder.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return ["Unranked", 0]

def get_name_from_puuid(puuid):
    pd_url = f"https://pd.na.a.pvp.net"
    response = requests.put(pd_url + f"/name-service/v2/players",
                            headers=get_headers(), json=[puuid], verify=False)
    # + "#" + response.json()[0]["TagLine"]
    logging.info(f"got name for {puuid} ({response.json()[0]['GameName']})")
    return response.json()[0]["GameName"]

def get_tag_from_puuid(puuid):
    pd_url = f"https://pd.na.a.pvp.net"
    response = requests.put(pd_url + f"/name-service/v2/players",
                            headers=get_headers(), json=[puuid], verify=False)
    logging.info(f"got tag for {puuid} ({response.json()[0]['TagLine']})")
    return response.json()[0]["TagLine"]

def addRowTable(table, args):
    table.add_rows(args)

def get_peak_rank(puuid):
    pd_url = f"https://pd.na.a.pvp.net"
    try:
        response = requests.get(pd_url + f"/mmr/v1/players/{puuid}", headers=get_headers(), verify=False).json()
    except json.decoder.JSONDecodeError as e:
        logging.error(f"Error decoding JSON, shows as unranked: {e}")
        return "Unranked"
    except requests.exceptions.RequestException as e:
        print("ratelimit?")
        logging.error(f"some other error, shows as unranked: {e}")
        return "Unranked"
    try:
        maxRank = float('-inf')
        for season_id, season_data in response['QueueSkills']['competitive']['SeasonalInfoBySeasonID'].items():
            rank = season_data['Rank']
            if rank > maxRank:
                maxRank = rank
                maxRankSeason = season_id
        preasc = ["0df5adb9-4dcb-6899-1306-3e9860661dd3", "3f61c772-4560-cd3f-5d3f-a7ab5abda6b3", "0530b9c4-4980-f2ee-df5d-09864cd00542", "46ea6166-4573-1128-9cea-60a15640059b", "fcf2c8f4-4324-e50b-2e23-718e4a3ab046", "97b6e739-44cc-ffa7-49ad-398ba502ceb0", "ab57ef51-4e59-da91-cc8d-51a5a2b9b8ff", "52e9749a-429b-7060-99fe-4595426a0cf7", "71c81c67-4fae-ceb1-844c-aab2bb8710fa", "2a27e5d2-4d30-c9e2-b15a-93b8909a442c", "4cb622e1-4244-6da3-7276-8daaf1c01be2", "a16955a5-4ad0-f761-5e9e-389df1c892fb", "97b39124-46ce-8b55-8fd1-7cbf7ffe173f", "573f53ac-41a5-3a7d-d9ce-d6a6298e5704", "d929bc38-4ab6-7da4-94f0-ee84f8ac141e", "3e47230a-463c-a301-eb7d-67bb60357d4f", "808202d6-4f2b-a8ff-1feb-b3a0590ad79f"]
        if maxRankSeason in preasc:
            allRanks = {
            0: "Unranked", 1: "Unranked", 2: "Unused 1", 3: "Iron 1", 4: "Iron 2", 5: "Iron 3", 6: "Bronze 1", 7: "Bronze 2", 8: "Bronze 3", 9: "Silver 1", 10: "Silver 2", 11: "Silver 3", 12: "Gold 1", 13: "Gold 2", 14: "Gold 3", 15: "Platinum 1", 16: "Platinum 2", 17: "Platinum 3", 18: "Diamond 1", 19: "Diamond 2", 20: "Diamond 3", 21: "Immortal 1", 22: "Immortal 2", 23: "Immortal 3", 24: "Radiant"
            }
            peakRank = allRanks[maxRank]
        else:
            allRanks = {
            0: "Unranked", 1: "Unranked", 2: "Unused 1", 3: "Iron 1", 4: "Iron 2", 5: "Iron 3", 6: "Bronze 1", 7: "Bronze 2", 8: "Bronze 3", 9: "Silver 1", 10: "Silver 2", 11: "Silver 3", 12: "Gold 1", 13: "Gold 2", 14: "Gold 3", 15: "Platinum 1", 16: "Platinum 2", 17: "Platinum 3", 18: "Diamond 1", 19: "Diamond 2", 20: "Diamond 3", 21: "Ascendant 1", 22: "Ascendant 2", 23: "Ascendant 3", 24: "Immortal 1", 25: "Immortal 2", 26: "Immortal 3", 27: "Radiant"
            }
            peakRank = allRanks[maxRank]
        
        return peakRank
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e} (ratelimit?)")
        logging.error(f"ratelimited {e}")
        time.sleep(10)
        return [1, 0]
    except Exception as e:
        logging.error(f"some other error, shows as unranked: {e}")
        return "Unranked"
    
agent_uuid_dict = {}

def get_all_agents_and_uuids():
    global agent_uuid_dict

    api_url = "https://valorant-api.com/v1/agents?isPlayableCharacter=true"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()

        for agent in data["data"]:
            agent_name = agent["displayName"]
            agent_uuid = agent["uuid"]
            agent_uuid_dict[agent_name] = agent_uuid
            # print(f"Agent Name: {agent_name}, UUID: {agent_uuid}")
    logging.info("Agents and UUIDs fetched.")

loadouts = {}

def get_loadouts():
    global loadouts
    current_game_match_id = get_coregame_match_id()
    glz_url = f"https://glz-na-1.na.a.pvp.net"
    vanskin = requests.get(
            glz_url + f"/core-game/v1/matches/{current_game_match_id}/loadouts", 
            headers=get_headers(),
        )
    if vanskin.status_code == 200:
        loadouts = vanskin.json()
        logging.info("Loadouts fetched.")

def fetch_skin(vandalID):
    response = requests.get(f"https://valorant-api.com/v1/weapons/skins/{vandalID}").json()
    return response['data']['displayName']

def get_skins():
    data = loadouts
    skins = {}
    
    vandal_ids = []
    subjects = []
    for character in data['Loadouts']:
        vandalID = character['Loadout']['Items']['9c82e19d-4575-0200-1a81-3eacf00cf872']['Sockets']['bcef87d6-209b-46c6-8b19-fbe40bd95abc']['Item']['ID']
        vandal_ids.append(vandalID)
        subjects.append(character['Loadout']['Subject'])

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(fetch_skin, vandal_ids))
        
    for subject, skin_name in zip(subjects, results):
        skins[subject] = skin_name
        logging.info(f"got skin for {subject} ({skin_name})")
    
    logging.info("Skins fetched.")
    return skins
       
def get_map_name():
    glz_url = f"https://glz-na-1.na.a.pvp.net"
    try:
        response = requests.get(
            glz_url + f"/core-game/v1/matches/{get_coregame_match_id()}", headers=get_headers(), verify=False).json()
        map_name = response['MapID']
        # print(map_name)
        response = requests.get("https://valorant-api.com/v1/maps/")
        for map in response.json()['data']:
            if map['mapUrl'] == map_name:
                logging.info(f"Map name: {map['displayName']}")

                return map['displayName']
    except KeyError:
        logging.error(f"Map name not found.")
        pass

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
        "Radiant": "rgb(255,0,0)",  
    }
    return rank_colors.get(rank, "rgb(255,255,255)")

def check_coregame():
        glz_url = f"https://glz-na-1.na.a.pvp.net"
        try:
            response = requests.get(
            glz_url + f"/core-game/v1/players/{get_puuid()}", headers=get_headers(), verify=False).json()
        except:
            exit()
        if "httpStatus" in response:
            logging.info("Not in core game.")
            return False
        else:
            logging.info("In core game.")
            return True

def check_pregame():
        glz_url = f"https://glz-na-1.na.a.pvp.net"
        try:
            response = requests.get(
            glz_url + f"/pregame/v1/players/{get_puuid()}", headers=get_headers(), verify=False).json()
        except:
            exit()
        if "httpStatus" in response:
            logging.info("Not in pregame.")
            return False
        else:
            logging.info("In pregame.")
            return True

def get_party_members():
    glz_url = f"https://glz-na-1.na.a.pvp.net"
    partyMembers = []
    try:
        partyID = requests.get(
            glz_url + f"/parties/v1/players/{get_puuid()}", headers=get_headers(), verify=False).json()
        # print(partyID['CurrentPartyID'])
        logging.info(f"Party ID: {partyID['CurrentPartyID']}")
        partydetails = requests.get(
            glz_url + f"/parties/v1/parties/{partyID['CurrentPartyID']}", headers=get_headers(), verify=False).json()
        members = partydetails['Members']
        # print(json.dumps(partydetails, indent=2))
        logging.info(f"Party details found")
        for member in members:
            partyMembers.append(member['Subject'])
        logging.info(f"Party members: {partyMembers}")
        return partyMembers
    
    except:
        pass

def get_level_from_puuid(puuid):
    pd_url = f"https://pd.na.a.pvp.net"
    response = requests.get(pd_url + f"/account-xp/v1/players/{puuid}", headers=get_headers(), verify=False).json()
    logging.info("got level")
    return response['Progress']['Level']

def get_specific_users_match(puuid):
    pd_url = f"https://pd.na.a.pvp.net"
    response = requests.get(
        pd_url + f"/match-history/v1/history/{puuid}?startIndex=0&endIndex=1", headers=get_headers(),
        verify=False).json()
    logging.info("got specific user's match")
    matchID = response['History'][0]['MatchID']

    response = requests.get(
        pd_url + f"/match-details/v1/matches/{matchID}", headers=get_headers(), verify=False).json()
    return response

def get_party_level(puuid):
    try:
        match = get_specific_users_match(puuid)
        for player in match['players']:
            if player['subject'] == puuid:
                logging.info(f"got party level for {puuid}")
                return player['accountLevel']
    except:
        logging.error(f"couldn't get party level for {puuid}")
        return "Unranked"

def get_attdef():
    stats = get_pregame_stats()

    if stats['AllyTeam']['TeamID'] == "Blue":
        doing = "Defending"
    else:
        doing = "Attacking"
    logging.info(f"got attacking or defending: {doing}")
    return doing