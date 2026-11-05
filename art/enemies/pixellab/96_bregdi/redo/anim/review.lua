-- Bregdi's 3 poses in their game loop 0 1 0 2, 260 ms.   Aseprite -b --script-param dir=<this folder> --script review.lua
local dir = app.params["dir"]
local spr = Sprite(98, 72, ColorMode.RGB)
local order = { 0, 1, 0, 2 }
for n, i in ipairs(order) do
  local fr = n == 1 and spr.frames[1] or spr:newEmptyFrame()
  fr.duration = 0.26
  spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/c_" .. i .. ".png" }, Point(0, 0))
end
spr:newTag(1, 4).name = "idle"
spr:saveAs(dir .. "/96_review.aseprite")
