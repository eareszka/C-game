-- Lay a strip of cells out as an .aseprite's frames, tagged (enemy_sheet.py pack).
-- params: strip (a png, cells side by side), fw (cell width), tags "D:3,DR:3", out.
local strip = Image{ fromFile = app.params.strip }
local fw = tonumber(app.params.fw)
local n = strip.width // fw
local spr = Sprite(fw, strip.height, ColorMode.RGB)
for i = 2, n do spr:newEmptyFrame() end
for i = 1, n do
  local img = Image(fw, strip.height, ColorMode.RGB)
  img:drawImage(strip, Point(-(i - 1) * fw, 0))
  spr:newCel(spr.layers[1], i, img, Point(0, 0))
  spr.frames[i].duration = 0.25
end
local at = 1
for name, len in app.params.tags:gmatch("(%w+):(%d+)") do
  local t = spr:newTag(at, at + tonumber(len) - 1)
  t.name = name
  at = at + tonumber(len)
end
spr:saveAs(app.params.out)
