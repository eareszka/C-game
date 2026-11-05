-- Chipique's review file: one view, the game's 0 1 0 2 loop at 400/250/400/250 ms.
--   Aseprite -b --script-param dir=<this folder> --script single.lua
local dir = app.params["dir"]
local spr = Sprite(98, 65, ColorMode.RGB)
local loop, ms = {0, 1, 0, 2}, {0.4, 0.25, 0.4, 0.25}
for k = 1, 4 do
  local fr = k == 1 and spr.frames[1] or spr:newEmptyFrame()
  fr.duration = ms[k]
  spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/single_" .. loop[k] .. ".png" }, Point(0, 0))
end
local tag = spr:newTag(1, 4)
tag.name = "idle"
spr:saveAs(dir .. "/93_single_review.aseprite")
print("frames", #spr.frames)
