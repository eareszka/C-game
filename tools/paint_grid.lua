-- Paint a letter grid (first line "K=000000 D=..." palette) into a new .aseprite.
local rows, C = {}, {}
for ln in io.lines(app.params.grid) do
  if next(C) == nil then
    for k, hex in ln:gmatch("(%w)=(%x+)") do
      C[k] = Color{r=tonumber(hex:sub(1,2),16), g=tonumber(hex:sub(3,4),16), b=tonumber(hex:sub(5,6),16)}
    end
  elseif #ln > 0 then rows[#rows+1] = ln end
end
local spr = Sprite(#rows[1], #rows, ColorMode.RGB)
local img = spr.cels[1].image
for y, r in ipairs(rows) do
  for x = 1, #r do
    local c = C[r:sub(x, x)]
    if c then img:drawPixel(x - 1, y - 1, c) end
  end
end
spr:saveAs(app.params.out)
