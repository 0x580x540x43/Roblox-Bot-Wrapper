
local WebSocket = (syn and syn.websocket or WebSocket).connect("ws://localhost:42069")

local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local PhysicsService = game:GetService("PhysicsService")
local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer



local function JsonDecode(Serialized)
    return HttpService:JSONDecode(Serialized)
end

local function JsonEncode(Serialized)
    return HttpService:JSONEncode(Serialized)
end

local function SendToMaster(Payload)
    Payload = JsonEncode(Payload)
    WebSocket:Send(Payload)
end

local OutgoingMessages = {

}

local AllBotObjects = {}

local Operations = {
	["ReplaceUserId"] = function(Fields)
		OldUserId = Fields["OldUserId"]
		NewUserId = Fields["NewUserId"]
		warn(string.format("Bot {%s} object persisted to {%s}", OldUserId, NewUserId))

		AllBotObjects[OldUserId] = NewUserId
	end,
}

local GlobalWSConnection = WebSocket.OnMessage:Connect(function(Data)
    local Response = HttpService:JSONDecode(Data)
	local Operation = Operations[Response["Opcode"]]
	if Operation then
		Operation(Response["Fields"])
		return
	end
    OutgoingMessages[Response["ID"]] = Response["Body"]
end)

local function AskServerTwoWay(Message, Args)
    local MessageId = HttpService:GenerateGUID(false)
    Args = Args or {}
    Args["ClientID"] = MessageId

    SendToMaster({
        ["Operation"] = Message,
        ["Arguments"] = Args
    })
    repeat
        task.wait()
    until OutgoingMessages[MessageId]
    local Message = OutgoingMessages[MessageId]
    OutgoingMessages[MessageId] = nil
    return Message
end

local Bot = {}

SendToMaster({
    ["Operation"] = "SetMainAccount",
    ["Arguments"] = {
        ["Username"] = LocalPlayer.Name
    }
})


function Bot:Launch(PlaceId, JobId)
    assert(PlaceId, "Missing PlaceId!")
    assert(JobId, "Missing JobId!")
    local a = {}

    setmetatable( a, self)
    self.__index = self


    a.UserId = AskServerTwoWay("NewBot", {
        ["PlaceId"] = PlaceId,
        ["JobId"] = JobId,
    })

	AllBotObjects[a.UserId] = a

    return  a
end

function Bot:GetBots()
    return AskServerTwoWay("GetBots")
end

function Bot:Disconnect()
    SendToMaster({
        ["Operation"] = "Disconnect",
        ["Arguments"] = {
            ["Who"] = self.UserId,
        }
    })
end

function Bot:Chat(Message)
    SendToMaster({
        ["Operation"] = "Chat",
        ["Arguments"] = {["Message"] = Message or ""},
        ["Who"] = self.UserId,
    })
end

function Bot:GetMemory(Key)
    assert(Key, "Missing key!")
    return AskServerTwoWay("GetMemory", {
        ["Who"] = self.UserId
    })[Key]
end

function Bot:LoadToMemory(Key, Value)
    assert(Key, "Missing key!")
    assert(Value, "Missing value!")

    SendToMaster({
        ["Operation"] = "AddToMemory",
        ["Arguments"] = {
            ["Key"] = Key,
            ["Value"] = Value,
            ["Who"] = self.UserId,
        }
    })
end

function Bot:GetPlayerInstance()
  for _, Player in pairs(Players:GetPlayers()) do
    if Player.UserId == self.UserId then 
      return Player
    end
  end
end

function Bot:Execute(Code)
    assert(Code, "Missing Code!")
    SendToMaster({
        ["Operation"] = "Execute",
        ["Arguments"] = {
            ["Code"] = Code,
            ["Who"] = self.UserId,
        }
    })
end



return Bot
