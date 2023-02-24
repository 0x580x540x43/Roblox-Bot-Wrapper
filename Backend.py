import json, threading, time, os, requests, random, logging, websockets, asyncio, traceback
from os import path
import ctypes

ctypes.windll.kernel32.CreateMutexW(None, True, "ROBLOX_singletonMutex")

RobloxProcessName = "RobloxPlayerBeta.exe"
CLIENTS = set()




class PersistentDict: # Lazy, original code was becoming too complicated 
    def UpdateMain(self):
      while True:
        with open(self.FileName, "w") as file:
          file.write(json.dumps(self.Dict))
          file.close()
        self.Start = True
        time.sleep(1)

    def Update(self):
      threading.Thread(target=self.UpdateMain).start()
  
    def __init__(self, identifier):
        self.FileName = f"{identifier}.json"
        self.Start = False
        if not os.path.exists(self.FileName):
            with open(self.FileName, 'w') as file:
                file.write("{}")
        with open(self.FileName, 'r') as file:
            self.Dict = json.load(file)
        self.Update()
        while not self.Start:
            continue
    def retrieve(self):
        return self.Dict



BotBanList = PersistentDict("BotBanList").retrieve()


Configuration = {
    "PlaceID" : None,
    "TimeoutLength" : 35,
    "AmountOfBotsToRun" : 6,
    "MasterPlaceId" : None,
    "MasterJobId" : None,
    "MainAccountName" : None
}

UserIDsToCookies = {

}

WebsocketConnections = {

}

Timeouts = {

}


def RemoveDictValue(dict, Value):
    for Key in dict.keys():
        if dict[Key] == Value:
            del dict[Value]


def UpdateBotBanList(UserId):
    global Configuration
    print("Updated", UserId, Configuration["MasterPlaceId"])
    BotBanList[UserId].append(Configuration["MasterPlaceId"])

def run(cmd):
    return os.popen(cmd).read().replace("\n", "")

def download(url,name):
    f = open(name, "wb")
    f.write(requests.get(url).content)
    f.close()
    return os.getcwd()+f"\\{name}"

def GetLatestClientPath():
    version_url = "https://s3.amazonaws.com/setup.roblox.com/version"
    version = requests.get(version_url).text.rstrip()
    
    paths = (
        os.environ["LOCALAPPDATA"] + "\\" + f"Roblox\\Versions\\{version}",
        os.environ["SYSTEMDRIVE"] + "\\" + f"Program Files (x86)\\Roblox\\Versions\\{version}",
        os.environ["SYSTEMDRIVE"] + "\\" + f"Program Files\\Roblox\\Versions\\{version}"
    )
    for path in paths:
        if os.path.isdir(path):
            return "'" + os.path.join(path, "RobloxPlayerBeta.exe") + "'"
        
    raise FileNotFoundError("Could not find path to Roblox client")

def ThreadFunction(target, Args = None):
    t = Args and threading.Thread(target=target, args=Args) or threading.Thread(target=target)
    t.daemon = True
    t.start()

def KillAllRobloxProcesses():
    return os.system("taskkill /IM RobloxPlayerBeta.exe")

def KillUserId(UserId):
    PID = Timeouts[UserId]["ProcessId"]
    if PID == 0:
        return
    return os.system(f"taskkill /F /PID {PID}")

def ReadFileLines(file):
    str = None
    with open(file, "r") as file:
        str = file.readlines()
        file.close()
    return str

def Get_XSRF_Token(token):
    xsrf = requests.post('https://auth.roblox.com/', cookies = {'.ROBLOSECURITY': token}).headers.get('x-csrf-token')
    return xsrf


def GetCookieData(Cookie):
    data = requests.get("https://users.roblox.com/v1/users/authenticated",
        cookies = {'.ROBLOSECURITY': Cookie},
        headers = {'x-csrf-token': Get_XSRF_Token(Cookie), "referer": "https://www.roblox.com"}
    ).json()
    return data

def EnsureGet(url):
    try:
        print("attempt to get cookie")
        return requests.get(url).text
    except Exception:
        print("failed, retrying")
        return EnsureGet(url)

with open("cookies.txt","r") as file:
    asd = file.readlines()



def GetAccountCookie():
    Cookie = asd.pop().replace("\n","")
    CookieData = GetCookieData(Cookie)
    UserId = CookieData.get("id")
    if not UserId:
        print("Failed to load cookie, using another")
        return GetAccountCookie()
    return Cookie, UserId

def UpdateRobloxProcessList(TargetBotId, processID):          
    Timeouts[TargetBotId]["ProcessId"] = processID

def Join_Game_Function(Cookie, PlaceID, JobID):
    try: 
        with requests.session() as session:
            session.cookies['.ROBLOSECURITY'] = Cookie
            session.headers['x-csrf-token'] = session.post('https://friends.roblox.com/v1/users/1/request-friendship').headers['x-csrf-token']
            auth_ticket = session.post('https://auth.roblox.com/v1/authentication-ticket/', headers={'referer':f'https://www.roblox.com/games/{PlaceID}'}).headers['rbx-authentication-ticket']
            BrowserId = random.randint(1000000, 10000000)
            print("Launching roblox instance..")
            JoinFlag = f"https://assetgame.roblox.com/game/PlaceLauncher.ashx?request=RequestGameJob&browserTrackerId={BrowserId}&placeId={PlaceID}&gameId={JobID}&isPlayTogetherGame=false"
            LaunchString = f'{GetLatestClientPath()} \'--app -t {auth_ticket} -j {JoinFlag} -b {BrowserId} --launchtime={time.time()*1000:0.0f} --rloc en_us --gloc en_us\' '
            Command = f"powershell \"(Start-Process  {LaunchString} -passthru).ID\" "
            return run(Command)
    except Exception:
        Join_Game_Function(Cookie, PlaceID, JobID)
        

def LoadBot(PlaceId, JobId, Memory = {}):
    Cookie, UserID = GetAccountCookie()

    UserIdString = str(UserID)
    if BotBanList.get(UserIdString) == None:
        print("new bot to banlists")
        BotBanList[UserIdString] = []

    if Configuration["PlaceID"] in BotBanList[UserIdString]:
        print("Bot was previously banned from this game. Using another.")
        LoadBot()
        return

    UserIDsToCookies[UserID] = Cookie

    Timeouts[UserID] = { # Who needs classes anyway?
        "LastPingTimestamp" : int(time.time()),
        "TimeoutStarted" : False,
        "FailedAttempts" : 0,
        "ProcessId" : 0,
        "PlaceId" : PlaceId,
        "JobId" : JobId, 
        "Storage" : Memory
    }
    JoinNewServer(UserID, PlaceId, JobId)
    return UserID

def RemoveBotData(UserID):
    del UserIDsToCookies[UserID]
    del Timeouts[UserID]

def DestroyAndReplaceBot(UserID):
    print(f"Instance with bot UserId of {UserID} was banned from a game. Replacing with a new account")
    BotBanList[str(UserID)].append(Configuration["MasterPlaceId"])
    KillUserId(UserID)
    OldBotData = Timeouts[UserID]
    RemoveBotData(UserID)

    LoadBot(OldBotData["PlaceId"], OldBotData["JobId"], OldBotData["Storage"])

async def NewBot(Arguments, websocket):
    global Configuration
    PlaceId = Arguments["PlaceId"]
    JobId = Arguments["JobId"]
    BotId = LoadBot(PlaceId, JobId)
    while not Timeouts[BotId]["Injected"]:
        continue
    await websocket.send(json.dumps({
        "ID" : Arguments["ClientID"],
        "Body" : BotId

    }))


async def Ping(Arguments, websocket):
    UserIDOfBot = Arguments["UserId"]
    if Timeouts.get(UserIDOfBot):
        if not WebsocketConnections.get(UserIDOfBot) or WebsocketConnections[UserIDOfBot] != websocket:
            WebsocketConnections[UserIDOfBot] = websocket
            Timeouts[UserIDOfBot]["Injected"] = True
        Timeouts[UserIDOfBot]["LastPingTimestamp"] = int(time.time())

def JoinNewServer(UserIDOfBot, PlaceId, JobId):
    KillUserId(UserIDOfBot)
    BotData = Timeouts[UserIDOfBot]
    BotData["TimeoutStarted"] = True

    Cookie = UserIDsToCookies[UserIDOfBot]

    ProcessId = Join_Game_Function(Cookie, PlaceId, JobId)
    UpdateRobloxProcessList(UserIDOfBot, ProcessId)

def ReduceLife():
    while True:
        for UserIDOfBot in Timeouts.copy().keys():
            BotStatus = Timeouts.get(UserIDOfBot)
            
            if not BotStatus or not BotStatus["TimeoutStarted"]:
                continue 
            print(Configuration["TimeoutLength"] - (int(time.time()) - BotStatus["LastPingTimestamp"]))
            if int(time.time()) - BotStatus["LastPingTimestamp"] > Configuration["TimeoutLength"]:
                if BotStatus["FailedAttempts"] >= 1:
                    print("Bot failed", BotStatus["FailedAttempts"], "times")
                    DestroyAndReplaceBot(UserIDOfBot)
                    continue
                JoinNewServer(UserIDOfBot)
                BotStatus["LastPingTimestamp"] = int(time.time())
                BotStatus["FailedAttempts"] += 1
            time.sleep(1)

ThreadFunction(ReduceLife)

async def send(websocket, message):
    try:
        await websocket.send(message)
    except Exception:
        pass

async def GetSlots(Arguments, websocket):
    BotUserId = Arguments["UserId"]
    BotInformation = Timeouts[BotUserId]
    Response = json.dumps(["Slots", BotInformation["LimbType"]])
    await send(websocket, Response)

async def BotBanned(Arguments, websocket):
    UserId = Arguments["UserId"]
    DestroyAndReplaceBot(UserId)


async def broadcast(message):
    global CLIENTS
    for websocket in CLIENTS:
        await send(websocket, message)

async def SendToUserId(UserId, message):
    await WebsocketConnections[UserId].send(message)

async def Execute(Arguments, websocket):
    CodeData = Arguments["Code"]
    Targets = Arguments["Who"]
    CodeMsg = json.dumps(["Execute", CodeData])
    if Targets == "all":
        await broadcast(CodeMsg)
    else:
        await SendToUserId(Targets, CodeMsg)

async def GetBots(Arguments, websocket):
    await websocket.send(json.dumps({
        "Body" : Timeouts.keys(),
        "ID" : Arguments["ClientID"]
    }))

async def Chat(Arguments, websocket):
    ChatData = Arguments["Message"]
    ChatMsg = json.dumps(["ChatMsg", ChatData])
    await broadcast(ChatMsg)

async def AddToMemory(Arguments, websocket):
    global Timeouts
    UserId = Arguments["Who"]
    Key = Arguments["Key"]
    Value = Arguments["Value"]

    Timeouts[UserId]["Storage"][Key] = Value

async def GetMemory(Arguments, websocket):
    await websocket.send(json.dumps({
        "Body" : Timeouts[Arguments["Who"]]["Storage"],
        "ID" : Arguments["ClientID"]
    }))

async def Disconnect(Arguments, websocket):
    UserID = Arguments["Who"]
    KillUserId(UserID)
    RemoveBotData(UserID)
    print(f":Disconnect called on {UserID}")

async def GetMainAccount(Arguments, websocket):
    global Configuration

    await websocket.send(json.dumps({
        "ID" : Arguments["ClientID"],
        "Body" : Configuration["MainAccountName"]
    }))

async def SetMainAccount(Arguments, websocket):
    global Configuration
    Configuration["MainAccountName"] = Arguments["Username"]

Operations = {
    "Ping" : Ping,
    "GetMainAccount": GetMainAccount, # Two Way Function
    "SetMainAccount": SetMainAccount,
    "BotBanned" : BotBanned,
    "NewBot" : NewBot, # Two Way Function
    "Chat": Chat,
    "GetBots" : GetBots, # Two Way Function
    "Execute": Execute,
    "AddToMemory" :  AddToMemory,
    "GetMemory" : GetMemory, # Two Way Function
    "Disconnect" : Disconnect,
}



async def MessageCallback(Payload, websocket):
    Payload = json.loads(Payload)
    Operation = Payload.get("Operation")
    Arguments = Payload.get("Arguments")
    await Operations[Operation](Arguments, websocket)


async def Handler(websocket):
    CLIENTS.add(websocket)
    while True: 
        try:
            Message = await websocket.recv()
            await MessageCallback(Message, websocket)
        except websockets.ConnectionClosed:
            RemoveDictValue(WebsocketConnections, websocket) 
            CLIENTS.remove(websocket)
            break
        except Exception:
            print(traceback.format_exc())


async def main():
    async with websockets.serve(Handler, "localhost", 42069):
        await asyncio.Future()  

asyncio.run(main())
