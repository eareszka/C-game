local root = 'C:/Users/emery/OneDrive/Desktop/projects/C-game/'
for _, name in ipairs({'girl', 'fisher', 'sailor', 'woodcutter'}) do
  local original = app.open(root .. 'art/npcs/' .. name .. '_sleep_exact.aseprite')
  local source = original.cels[1].image
  local sprite = Sprite(24, 16, ColorMode.RGB)
  local image = Image(24, 16, ColorMode.RGB)
  -- Keep the native pixel grid: head at the right/pillow end, feet left.
  for y = 0, 19 do
    for x = 0, 13 do image:putPixel(2+19-y, 1+x, source:getPixel(x,y)) end
  end
  sprite.cels[1].image = image
  sprite:saveAs(root .. 'art/npcs/' .. name .. '_sleep_lying_reference.png')
end
