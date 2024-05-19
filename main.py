import requests
import json
from colorama import Fore

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
            else:
                print(f"{Fore.RED}Error fetching thumbnail {item['requestId']}{Fore.RESET}")
        
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

cursor = None
server_count = 0
page_count = 0

all_thumbs = []

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
        server_count += 1
        print(f"{Fore.YELLOW}Thumbnails cached: {Fore.BLUE}{len(all_thumbs)}{Fore.RESET}")
        print(f"{Fore.YELLOW}Indexing server: {Fore.BLUE}{server_count} | {server['id']}{Fore.RESET}")
        thumbs = fetch_thumbs(server["playerTokens"])

        if thumbs == None:
            print(f"{Fore.RED}Failed to fetch player thumbnails{Fore.RESET}")
            continue

        for thumb in thumbs:
            all_thumbs.append([thumb, server["id"]])

    print(f"{Fore.YELLOW}Checking for match in {Fore.BLUE}{len(all_thumbs)}{Fore.YELLOW} thumbnails...{Fore.RESET}")
    for thumb in all_thumbs:
        if thumb[0] == thumbnail_url:
            print(f"{Fore.GREEN}Match found{Fore.RESET}")
            print(f"{Fore.YELLOW}Server: {Fore.BLUE}{server['id']}{Fore.RESET} | {server['ping']}ms | {server['playing']}/{server['maxPlayers']} players")
            print(f"{Fore.YELLOW}Server URL: {Fore.BLUE}roblox://experiences/start?placeId={placeId}&gameInstanceId={thumb[1]}{Fore.RESET}")
            exit(0)

    if data["nextPageCursor"] == None:
        print(f"{Fore.RED}All servers indexed, no match found :({Fore.RESET}")
        break
    else:
        cursor = data["nextPageCursor"]