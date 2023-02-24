local WebSocket = (syn and syn.websocket or WebSocket).connect("ws://localhost:42069")

local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local PhysicsService = game:GetService("PhysicsService")
local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer
local CoreGui = game:GetService("CoreGui")
local NetworkClient = game:GetService("NetworkClient")
local PromptOverlay = CoreGui:WaitForChild("RobloxPromptGui"):WaitForChild("promptOverlay")
NetworkClient:SetOutgoingKBPSLimit(math.huge)


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

local function Ping()
	while true do task.wait(1)
		SendToMaster({
			["Operation"] = "Ping",
			["Arguments"] = {
				["UserId"] = LocalPlayer.UserId, 
			}
		})
	end
end

local function BannedFromGame()
    SendToMaster({
        ["Operation"] = "BotBanned",
        ["Arguments"] = {
            ["UserId"] = LocalPlayer.UserId
        }
    })
end

local function Disable(Object)
    if Object:IsA("BasePart") then
        Object.Material = "Plastic"
        Object.Reflectance = 0
        Object.Transparency = 1;
    elseif Object:IsA("Decal") then
        Object.Transparency = 1
    elseif Object:IsA("ParticleEmitter") or Object:IsA("Trail") then
        Object.Lifetime = NumberRange.new(0)
    elseif Object:IsA("Explosion") then
        Object.BlastPressure = 1
        Object.BlastRadius = 1
    end
end

local function DisableAllRendering()
    --settings()["Task Scheduler"].ThreadPoolConfig = Enum.ThreadPoolConfig.Threads1
    StarterGui:ClearAllChildren()
    Lighting:ClearAllChildren()

    RunService:Set3dRenderingEnabled(false)
    --RunService:setThrottleFramerateEnabled(true)
    Terrain.WaterWaveSize = 0
    Terrain.WaterWaveSpeed = 0
    Terrain.WaterReflectance = 0
    Terrain.WaterTransparency = 0

    Lighting.GlobalShadows = false
    Lighting.FogEnd = 9e9

    settings().Rendering.QualityLevel = 1

    for _, Object in ipairs(workspace:GetDescendants()) do -- 
        Disable(Object)
    end

    workspace.DescendantAdded:Connect(function(Object)
        Disable(Object)
    end)
end

local Operations = {
	["ChatMsg"] = function(Message)
		game.ReplicatedStorage.DefaultChatSystemChatEvents.SayMessageRequest:FireServer(Message, "All")
	end,
	["Execute"] = function(Code)
		warn(pcall(loadstring(Code)))
	end
}

local OutgoingMessages = {

}



local GlobalWSConnection = WebSocket.OnMessage:Connect(function(Data)
	local Response = HttpService:JSONDecode(Data)
	local Operation = Operations[Response[1]]
	if Operation then
		Operation(Response[2])
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

if AskServerTwoWay("GetMainAccount") == LocalPlayer.Name then 
	print("Main account")
	return
end

local Bot = {}

function Bot.GetMemory(Key)
	return AskServerTwoWay("GetMemory", {
		["Who"] = LocalPlayer.UserId
	})[Key]
end

function Bot.LoadToMemory(Key, Value)
	SendToMaster({
        ["Operation"] = "AddToMemory",
        ["Arguments"] = {
			["Key"] = Key,
			["Value"] = Value,
			["Who"] = LocalPlayer.UserId,
		}
    })
end

coroutine.wrap(Ping)()
DisableAllRendering()

GuiService.ErrorMessageChanged:Connect(BannedFromGame)
TeleportService.LocalPlayerArrivedFromTeleport:Connect(BannedFromGame)

for _, Child in ipairs(PromptOverlay:GetChildren()) do 
    if Child.Name == 'ErrorPrompt' and Child:FindFirstChild('MessageArea') and Child.MessageArea:FindFirstChild("ErrorFrame") then
        BannedFromGame()
        return
    end
end

return Bot
