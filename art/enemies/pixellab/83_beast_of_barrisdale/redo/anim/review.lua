-- 83 redo's review file: all three sheets at game timing, tagged. Run by Aseprite in batch mode:
--   Aseprite -b --script-param dir=<this folder> --script review.lua
local dir = app.params["dir"]
local spr = Sprite(100, 65, ColorMode.RGB)
local sheets = { {"idle", 10, 0.13}, {"fly", 10, 0.13}, {"block", 7, 0.29} }
local n, first = 0, true
for _, s in ipairs(sheets) do
  local from = n + 1
  for i = 0, s[2] - 1 do
    local fr = first and spr.frames[1] or spr:newEmptyFrame()
    first = false
    fr.duration = s[3]
    spr:newCel(spr.layers[1], fr, Image{ fromFile = dir .. "/" .. s[1] .. "_" .. i .. ".png" }, Point(0, 0))
    n = n + 1
  end
  local tag = spr:newTag(from, n)
  tag.name = s[1]
end
spr:saveAs(dir .. "/83_redo_review.aseprite")
print("frames", #spr.frames, "tags", #spr.tags)
