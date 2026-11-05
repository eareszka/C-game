-- Ebigane: idle in its game loop 0 1 0 2 (tag idle), then the fly frames (tag fly).   Aseprite -b --script-param dir=<this folder> --script review.lua
local dir = app.params["dir"]
local spr = Sprite(104, 68, ColorMode.RGB)
local seq = { "c_0", "c_1", "c_0", "c_2", "f_0", "f_1", "f_2", "f_3" }
for n, name in ipairs(seq) do
  local fr = n == 1 and spr.frames[1] or spr:newEmptyFrame()
  fr.duration = n <= 4 and 0.26 or 0.15
  spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/" .. name .. ".png" }, Point(0, 0))
end
spr:newTag(1, 4).name = "idle"
spr:newTag(5, 8).name = "fly"
spr:saveAs(dir .. "/12_review.aseprite")
