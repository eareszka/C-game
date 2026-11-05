-- Anaye: tags idle (0 1), lift (0 2 3), slam (3 4).   Aseprite -b --script-param dir=<this folder> --script review.lua
local dir = app.params["dir"]
local spr = Sprite(130, 110, ColorMode.RGB)
for i = 0, 4 do
  local fr = i == 0 and spr.frames[1] or spr:newEmptyFrame()
  fr.duration = 0.26
  spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/c_" .. i .. ".png" }, Point(0, 0))
end
spr:newTag(1, 2).name = "idle"
spr:newTag(3, 4).name = "lift"
spr:newTag(5, 5).name = "slam"
spr:saveAs(dir .. "/34_review.aseprite")
