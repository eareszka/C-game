-- Replace one colour by another in every cel of a sprite, in place (a palette fix that keeps the drawing).
--   aseprite -b --script-param source=FILE --script-param from=0c0a12 --script-param to=000000 --script replace_colour.lua
local s = app.open(app.params.source)
local function rgba(h) return app.pixelColor.rgba(tonumber(h:sub(1, 2), 16), tonumber(h:sub(3, 4), 16), tonumber(h:sub(5, 6), 16), 255) end
assert(s.colorMode == ColorMode.RGB, 'replace_colour.lua: an RGB sprite is expected')
local from, to, n = rgba(app.params.from), rgba(app.params.to), 0
for _, cel in ipairs(s.cels) do
  local im = cel.image:clone()
  for it in im:pixels() do
    if it() == from then it(to); n = n + 1 end
  end
  cel.image = im
end
s:saveAs(app.params.source)
print(n)
