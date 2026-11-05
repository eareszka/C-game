-- Before and after: choppy frame 4, then PixelLab's cleanup.   Aseprite -b --script-param dir=<this folder> --script test.lua
local dir = app.params["dir"]
local spr = Sprite(98, 65, ColorMode.RGB)
local files = { dir .. "/../long/c_4.png", dir .. "/c4_clean.png" }
for i, f in ipairs(files) do
  local fr = i == 1 and spr.frames[1] or spr:newEmptyFrame()
  fr.duration = 0.7
  spr:newCel(spr.layers[1], fr, Image{ fromFile = f }, Point(0, 0))
end
spr:saveAs(dir .. "/93_tail_test.aseprite")
