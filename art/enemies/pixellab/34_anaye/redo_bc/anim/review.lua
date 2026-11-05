-- Anaye B+C: tags idle (0 1), lift (1 2 3 4), slam (5 6 7 8), each pose 260 ms.   Aseprite -b --script-param dir=<this folder> --script review.lua
local dir = app.params["dir"]
local spr = Sprite(130, 118, ColorMode.RGB)
local seq = { 0, 1, 1, 2, 3, 4, 5, 6, 7, 8 }
for n, i in ipairs(seq) do
  local fr = n == 1 and spr.frames[1] or spr:newEmptyFrame()
  fr.duration = 0.26
  spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/p_" .. i .. ".png" }, Point(0, 0))
end
spr:newTag(1, 2).name = "idle"
spr:newTag(3, 6).name = "lift"
spr:newTag(7, 10).name = "slam"
spr:saveAs(dir .. "/34_review.aseprite")
