-- The flop's review file: its six frames at 120 ms, tagged, from anim/flop_N.png. Run by Aseprite in batch mode:
--   Aseprite -b --script-param dir=<this folder> --script flop_aseprite.lua
local dir = app.params["dir"]
local spr = Sprite(98, 65, ColorMode.RGB)
for i = 0, 5 do
  local fr = i == 0 and spr.frames[1] or spr:newEmptyFrame()
  fr.duration = 0.12
  spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/anim/flop_" .. i .. ".png" }, Point(0, 0))
end
local tag = spr:newTag(1, 6)
tag.name = "flop"
spr:saveAs(dir .. "/flop.aseprite")
print("frames", #spr.frames)
