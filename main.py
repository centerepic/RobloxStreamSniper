import requests
import json, os, threading, time, sys
from colorama import Fore

THUMBNAIL_THREADS_MAX = 12

cursor = None
server_count = 0
player_count = 0
players_scanned = 0
page_count = 0

all_thumbs = []
all_servers = []

class ProgressBar:
    def __init__(self, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill = fill
        self.printEnd = printEnd
        self.iteration = 0

    def print(self):
        percent = ("{0:." + str(self.decimals) + "f}").format(100 * (self.iteration / float(self.total)))
        filledLength = int(self.length * self.iteration // self.total)
        bar = self.fill * filledLength + '-' * (self.length - filledLength)
        print(f'\rProgress: |{bar}| {percent}% {self.suffix} ({players_scanned} / {player_count})', end = self.printEnd)
        if self.iteration == self.total: 
            print()

def fetch_thumbs(tokens):
    url = "https://thumbnails.roblox.com/v1/batch"
    
    body = []
    for token in tokens:
        body.append({
            "requestId": f"0:{token}:AvatarHeadshot:150x150:png:regular",
            "type": "AvatarHeadShot",
            "targetId": 0,
            "token": token,
            "format": "png",
            "size": "150x150"
        })
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(body))
    
    if response.status_code == 200:
        data = response.json()
        thumbs = []

        for item in data["data"]:
            if item["state"] == "Completed":
                thumbs.append(item["imageUrl"])
            #else:
                #print(f"{Fore.RED}Error fetching thumbnail {item['requestId']}{Fore.RESET}")
        
        return thumbs
    else:
        print(f"Error fetching thumbnails: {response.status_code}")
        print(response.text)
        return None

target = input("Username / UserId: ")
placeId = input("Place ID: ")

userName = None
userId = None

if target.isdigit():
    userId = target
else:
    print(f"{Fore.YELLOW}Getting userId from username...{Fore.RESET}")
    userName = target

if userName != None and userId == None:
    user_page = requests.get(f"https://www.roblox.com/users/profile?username={userName}")
    if user_page.status_code != 200:
        print("Invalid user")
        exit(-1)
    userId = user_page.url.split("users/")[1].split("/profile")[0]
elif userName == None and userId != None:
    user_page = requests.get(f"https://users.roblox.com/v1/users/{userId}")
    if user_page.status_code != 200:
        print("Invalid user")
        exit(-1)

    userName = user_page.json()["name"]


print()

print(f"{Fore.YELLOW}Username: {Fore.BLUE}{userName}{Fore.RESET}")
print(f"{Fore.YELLOW}UserId: {Fore.BLUE}{userId}{Fore.RESET}")
print(f"{Fore.YELLOW}Place ID: {Fore.BLUE}{placeId}{Fore.RESET}")

print()

print(f"{Fore.YELLOW}Getting user thumbnail...{Fore.RESET}")

thumbnail_request = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={userId}&format=Png&size=150x150")

if thumbnail_request.status_code != 200:
    print("Failed to get thumbnail")
    exit(-1)

thumbnail_data = thumbnail_request.json()

if thumbnail_data["data"][0]["state"] == "Completed":
    print(f"{Fore.GREEN}Thumbnail fetched{Fore.RESET}")
else:
    print(f"{Fore.RED}Failed to get thumbnail{Fore.RESET}")
    exit(-1)

thumbnail_url = thumbnail_data["data"][0]["imageUrl"]

print(f"{Fore.YELLOW}Initiating server scanning...{Fore.RESET}")

while True:
    page_count += 1
    print(f"{Fore.YELLOW}Page: {Fore.BLUE}{page_count}{Fore.RESET}")

    if cursor == None:
        response = requests.get(f"https://games.roblox.com/v1/games/{placeId}/servers/Public?limit=100")
    else:
        response = requests.get(f"https://games.roblox.com/v1/games/{placeId}/servers/Public?limit=100&cursor={cursor}")

    if response.status_code != 200:
        print(f"Failed to get servers: {response.status_code}")
        exit(-1)

    data = response.json()

    for server in data["data"]:
        all_servers.append(server)
        server_count += 1
        player_count += server["playing"]
        os.system("cls")
        print(f"{Fore.YELLOW}Indexing server: {Fore.BLUE}{server_count} | {server['id']}{Fore.RESET}")
        print(f"{Fore.YELLOW}Players indexed: {Fore.BLUE}{player_count}{Fore.RESET}")

    if data["nextPageCursor"] == None:
        print(f"{Fore.YELLOW}All servers indexed, scanning...{Fore.RESET}")
        break
    else:
        cursor = data["nextPageCursor"]

os.system("cls")
print(f"{Fore.YELLOW}Servers indexed: {Fore.BLUE}{server_count}{Fore.RESET}")
print(f"{Fore.YELLOW}Players indexed: {Fore.BLUE}{player_count}{Fore.RESET}")
print(f"{Fore.RED}Initiating thumbnail scanning, this may take a while...{Fore.RESET}")

time.sleep(2)
os.system("cls")

def check_thumb_match(thumbnail_link):
    if thumbnail_link == thumbnail_url:
        return True

lock = threading.Lock()
progress = ProgressBar(server_count, prefix = 'Progress:', suffix = 'Complete', length = 50)

def fetch_thumbs_threaded(server):
    global all_thumbs
    global players_scanned
    thumbs = fetch_thumbs(server["playerTokens"])
    lock.acquire()
    players_scanned += server["playing"]
    for thumb in thumbs:
        all_thumbs.append([thumb, server])

    lock.release()

threads = []

print("Enter scantype: ")
print(" 1. Largest to smallest")
print(" 2. Smallest to largest")
print(" 3. Interwoven (largest to smallest every other)")

scantype = input("Scantype: ")

if scantype == "1":
    all_servers = sorted(all_servers, key=lambda x: x["playing"], reverse=True)
elif scantype == "2":
    all_servers = sorted(all_servers, key=lambda x: x["playing"])
elif scantype == "3":
    temp_list = []
    for i in range(0, len(all_servers) // 2):
        temp_list.append(all_servers[i])
        temp_list.append(all_servers[-i])

    all_servers = temp_list

for server in all_servers:
    while True:
        if threading.active_count() - 1 < THUMBNAIL_THREADS_MAX:
            thread = threading.Thread(target=fetch_thumbs_threaded, args=(server,))
            thread.start()
            threads.append(thread)
            break
        else:
            time.sleep(0.1)

    progress.iteration += 1
    progress.print()

    for thread in threads:
        if not thread.is_alive():
            threads.remove(thread)
            break
    
    for thumb in all_thumbs:
        if check_thumb_match(thumb[0]):

            for thread in threads:
                thread.join()

            server = thumb[1]

            print(f"{Fore.GREEN}Match found{Fore.RESET}")
            print(f"{Fore.YELLOW}Server: {Fore.BLUE}{server['id']}{Fore.RESET} | {server['ping']}ms | {server['playing']}/{server['maxPlayers']} players")
            print(f"{Fore.YELLOW}Server URL: {Fore.BLUE}roblox://experiences/start?placeId={placeId}&gameInstanceId={server['id']}{Fore.RESET}")
            exit(0)
