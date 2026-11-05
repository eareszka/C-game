-- Anaye's appearance: tag walk (loops), tag raise (the last frame is held).   Aseprite -b --script-param dir=<seq folder> --script seq.lua
local dir = app.params["dir"]
local spr = Sprite(48, 48, ColorMode.RGB)
for i = 0, 6 do
  local fr = i == 0 and spr.frames[1] or spr:newEmptyFrame()
  fr.duration = i < 4 and 0.2 or 0.18
  spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/f_" .. i .. ".png" }, Point(0, 0))
end
spr.frames[7].duration = 0.9
spr:newTag(1, 4).name = "walk"
spr:newTag(5, 7).name = "raise"
spr:saveAs(dir .. "/34_mini_seq.aseprite")
