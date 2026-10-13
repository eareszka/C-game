-- Set a packed enemy sheet's frame time and palette (tools/enemy_sheet.py install).
--   aseprite -b --script-param source=FILE --script-param ms=170 --script-param pal=000000,fcfcfc,... --script sheet_meta.lua
local s = app.open(app.params.source)
local ms = tonumber(app.params.ms or '')
if ms then
  for _, f in ipairs(s.frames) do f.duration = ms / 1000 end
end
local cols = {}
for h in string.gmatch(app.params.pal or '', '%x%x%x%x%x%x') do cols[#cols + 1] = h end
if #cols > 0 then
  local p = Palette(#cols)
  for i, h in ipairs(cols) do
    p:setColor(i - 1, Color{ r = tonumber(h:sub(1, 2), 16), g = tonumber(h:sub(3, 4), 16), b = tonumber(h:sub(5, 6), 16), a = 255 })
  end
  s:setPalette(p)
end
s:saveAs(app.params.source)
