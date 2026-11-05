-- Chipique's long idle: 16 frames at 150 ms, one tag.
--   Aseprite -b --script-param dir=<this folder> --script long.lua
local dir = app.params["dir"]
local spr = Sprite(98, 65, ColorMode.RGB)
for i = 0, 15 do
  local fr = i == 0 and spr.frames[1] or spr:newEmptyFrame()
  fr.duration = 0.15
  spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/f_" .. i .. ".png" }, Point(0, 0))
end
local tag = spr:newTag(1, 16)
tag.name = "idle"
spr:saveAs(dir .. "/93_long_review.aseprite")
print("frames", #spr.frames)
