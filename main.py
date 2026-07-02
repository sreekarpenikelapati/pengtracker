import websockets
import ssl
import base64
import json
import os
import asyncio
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from rich.console import Console
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from valfun import *
import time
import logging
from commands import *

os.system('cls')

urllib3.disable_warnings(InsecureRequestWarning)

if os.path.exists(os.path.join(BASE_DIR, "logs")):
    logging.basicConfig(filename=os.path.join(BASE_DIR, "logs", 'pt.log'), filemode = 'w', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
else:
    logging.disable(logging.CRITICAL)

class ValorantWs:
    def __init__(self, lockfile):
        self.lockfile = lockfile
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self.running = True
        self.user_puuid = None
        self.in_game = False
        self.previous_state = None
        self.loading_printed = False
        self.console = Console()

    async def connect_to_websocket(self):
        local_headers = {
            'Authorization': basic_auth(self.lockfile['password'])
        }
        url = f"wss://127.0.0.1:{self.lockfile['port']}"

        self.user_puuid = self.get_user_puuid()

        async with websockets.connect(url, ssl=self.ssl_context, extra_headers=local_headers) as websocket:
            await websocket.send('[5, "OnJsonApiEvent_chat_v4_presences"]')
            print('\033[92m' + "Websocket connection established." + '\033[0m')
            try:
                preload_all()
            except Exception as e:
                print(f"Error during preload: {str(e)}")
                logging.error(f"Error during preload: {str(e)}")
            try:
                if check_coregame():
                    self.handle_coregame()
                elif check_pregame():
                    self.handle_pregame()
                else:
                    self.handle_menus()

            except Exception as e:
                await asyncio.sleep(3)
                self.handle_menus()
                logging.error(f"error during check: {str(e)}")
            while self.running:
                response = await websocket.recv()
                self.handle(response)

    def get_user_puuid(self):
        endpoints = {
            'session': f'https://127.0.0.1:{self.lockfile["port"]}/chat/v1/session'
        }
        headers = {
            'Authorization': basic_auth(self.lockfile['password'])
        }
        try:
            response = requests.get(endpoints['session'], headers=headers, verify=False, timeout=TIMEOUT)
        except Exception:
            self.console.print("[bold red]VALORANT is not running. Please start VALORANT and try again.")
            exit()
        logging.info(f"get_user_puuid")
        return response.json()['puuid']

    def handle(self, message):
        try:
            parsed_message = json.loads(message)
            if parsed_message[1] == "OnJsonApiEvent_chat_v4_presences" and parsed_message[2]['data']['presences'] and parsed_message[2]['data']['presences'][0]['puuid'] == self.user_puuid:
                presence = parsed_message[2]['data']['presences'][0]
                private = json.loads(base64.b64decode(presence['private']))
                new_state = private['matchPresenceData']['sessionLoopState']
                if new_state != self.previous_state:
                    self.previous_state = new_state
                    if new_state == "MENUS":
                        logging.info(f"handling MENUS")
                        self.handle_menus()
                    elif new_state == "PREGAME":
                        logging.info(f"handling PREGAME")
                        self.handle_pregame()
                    if new_state == "INGAME":
                        logging.info(f"handling INGAME")
                        self.handle_coregame()

                if new_state == "MENUS" and self.previous_state == "MENUS":
                    if get_party_change():
                        logging.info(f"handling MENUS (update)")
                        self.handle_menus()

        except json.JSONDecodeError as e:
            pass
        except Exception as e:
            print(f"Error handling message: {str(e)}")

    def handle_pregame(self):
        os.system('cls')
        self.console.print(f"[dodger_blue2]Pengtracker v{version}")
        pre()

    def handle_coregame(self):
        if not self.in_game:
            self.in_game = True
            self.loading_printed = True
            os.system('cls')
            self.console.print(f"[dodger_blue2]Pengtracker v{version}")
            core()

    def handle_menus(self):
        os.system('cls')
        self.console.print(f"[dodger_blue2]Pengtracker v{version}")
        party()
        self.in_game = False
        self.loading_printed = False

    def stop(self):
        self.running = False

if __name__ == "__main__":
    version = "4.9.5"
    logging.info(f"Pengtracker v{version}")
    Console().print(f"[dodger_blue2]Pengtracker v{version}")
    try:
        lockfile_path = os.path.join(os.getenv('LOCALAPPDATA'), R'Riot Games\Riot Client\Config\lockfile')
        with open(lockfile_path) as lockfile:
            data = lockfile.read().split(':')
            keys = ['name', 'PID', 'port', 'password', 'protocol']
            lockfile_data = dict(zip(keys, data))
    except FileNotFoundError:
        raise Exception("Lockfile not found")

    valorant_ws = ValorantWs(lockfile_data)
    try:
        asyncio.run(valorant_ws.connect_to_websocket())
    except KeyboardInterrupt:
        valorant_ws.stop()
        print("Websocket connection stopped.")
    except Exception as e:
        Console().print("[bold red]VALORANT is not running.")
        input("Press enter to exit.")
        os._exit(0)
