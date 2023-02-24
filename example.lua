local Link = "https://raw.githubusercontent.com/sangwriter/Roblox-Bot-Wrapper/main/Bot%20Wrapper%20Main.lua"
local BotAPI = loadstring(game:HttpGet(Link))()

local Poopity = BotAPI:Launch(game.PlaceId, game.JobId)

Poopity:Chat("bot wrapper test")

Poopity:Execute([[print("🗿")]])

wait(5)

Poopity:Disconnect()
