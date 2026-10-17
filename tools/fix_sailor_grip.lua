-- Native Aseprite repair: retain all original opaque pixels and add the grip
-- shown by the imagegen repair reference, using only the game's own palette.
local sprite = app.activeSprite
assert(sprite and sprite.width == 40 and sprite.height == 28 and #sprite.frames == 2)
local black = app.pixelColor.rgba(0, 0, 0, 255)
local skin = app.pixelColor.rgba(215, 161, 117, 255)
local cuff = app.pixelColor.rgba(232, 224, 192, 255)
local blue = app.pixelColor.rgba(40, 80, 160, 255)
app.transaction(function()
  for index = 1, 2 do
    local cel = sprite.cels[index]
    assert(cel.position.x == 0 and cel.position.y == 0)
    local image = cel.image:clone()
    for x = 25, 30 do
      local color = x < 27 and skin or x == 27 and cuff or blue
      for _, p in ipairs({{x, 19 + index, black}, {x, 20 + index, color}, {x, 21 + index, black}}) do
        if app.pixelColor.rgbaA(image:getPixel(p[1], p[2])) == 0 then
          image:drawPixel(p[1], p[2], p[3])
        end
      end
    end
    cel.image = image
  end
end)
app.command.SaveFile()
