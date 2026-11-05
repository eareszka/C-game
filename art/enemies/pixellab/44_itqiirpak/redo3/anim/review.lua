-- Itqiirpak: 8 tags, one a view, three poses each at 260 ms.   Aseprite -b --script-param dir=<this folder> --script review.lua
local dir = app.params["dir"]
local spr = Sprite(130, 88, ColorMode.RGB)
local order = { "D", "DR", "R", "UR", "U", "UL", "L", "DL" }
local n = 0
for _, v in ipairs(order) do
  for i = 0, 2 do
    n = n + 1
    local fr = n == 1 and spr.frames[1] or spr:newEmptyFrame()
    fr.duration = 0.26
    spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/" .. v .. "_" .. i .. ".png" }, Point(0, 0))
  end
  spr:newTag(n - 2, n).name = v
end
spr:saveAs(dir .. "/44_review.aseprite")
