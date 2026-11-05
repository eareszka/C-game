-- Anaye stepped: tags idle (c_0 c_1), lift (c_1 c_3 c_4 c_6), slam (c_7 c_9 c_11 c_13), each pose 260 ms.   Aseprite -b --script-param dir=<this folder> --script stepped.lua
local dir = app.params["dir"]
local spr = Sprite(130, 118, ColorMode.RGB)
local seq = { 0, 1, 1, 3, 4, 6, 7, 9, 11, 13 }
for n, i in ipairs(seq) do
  local fr = n == 1 and spr.frames[1] or spr:newEmptyFrame()
  fr.duration = 0.26
  spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/c_" .. i .. ".png" }, Point(0, 0))
end
spr:newTag(1, 2).name = "idle"
spr:newTag(3, 6).name = "lift"
spr:newTag(7, 10).name = "slam"
spr:saveAs(dir .. "/34_review.aseprite")
