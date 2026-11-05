-- Chipique's long idle: 8 poses at 260 ms, one tag.
--   Aseprite -b --script-param dir=<this folder> --script long.lua
local dir = app.params["dir"]
local spr = Sprite(98, 65, ColorMode.RGB)
for i = 0, 7 do
  local fr = i == 0 and spr.frames[1] or spr:newEmptyFrame()
  fr.duration = 0.26
  spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/c_" .. i .. ".png" }, Point(0, 0))
end
local tag = spr:newTag(1, 8)
tag.name = "idle"
spr:saveAs(dir .. "/93_choppy_review.aseprite")
print("frames", #spr.frames)
