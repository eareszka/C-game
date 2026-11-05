-- Siehnam redo's review file: eight direction tags, the game's 0 1 0 2 loop at 400/250/400/250 ms.
--   Aseprite -b --script-param dir=<this folder> --script review.lua
local dir = app.params["dir"]
local spr = Sprite(98, 65, ColorMode.RGB)
local loop, ms = {0, 1, 0, 2}, {0.4, 0.25, 0.4, 0.25}
local n, first = 0, true
for _, v in ipairs({"D", "DR", "R", "UR", "U", "UL", "L", "DL"}) do
  local from = n + 1
  for k = 1, 4 do
    local fr = first and spr.frames[1] or spr:newEmptyFrame()
    first = false
    fr.duration = ms[k]
    spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/" .. v .. "_" .. loop[k] .. ".png" }, Point(0, 0))
    n = n + 1
  end
  local tag = spr:newTag(from, n)
  tag.name = v
end
spr:saveAs(dir .. "/92_redo_review.aseprite")
print("frames", #spr.frames, "tags", #spr.tags)
