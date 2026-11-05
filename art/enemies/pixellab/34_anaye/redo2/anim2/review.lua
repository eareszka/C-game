-- Anaye: tags idle (0-1), lift (1-6), slam (7-13).   Aseprite -b --script-param dir=<this folder> --script review.lua
local dir = app.params["dir"]
local spr = Sprite(130, 118, ColorMode.RGB)
for i = 0, 13 do
  local fr = i == 0 and spr.frames[1] or spr:newEmptyFrame()
  fr.duration = i <= 6 and 0.15 or 0.11
  spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/c_" .. i .. ".png" }, Point(0, 0))
end
spr.frames[1].duration = 0.3
spr.frames[7].duration = 0.7
spr.frames[14].duration = 0.8
spr:newTag(2, 7).name = "lift"
spr:newTag(8, 14).name = "slam"
spr:saveAs(dir .. "/34_review.aseprite")
