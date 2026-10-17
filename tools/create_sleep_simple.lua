-- Exact edits to approved NPCs. No image generation or paid service.
local root = 'C:/Users/emery/OneDrive/Desktop/projects/C-game/'
for _, name in ipairs({'girl','fisher','sailor','woodcutter'}) do
  local original = app.open(root .. 'assets/npcs/' .. name .. '.png')
  local source = original.cels[1].image
  local sprite = Sprite(14,20,ColorMode.RGB)
  for side = 0,1 do
    local y0 = 40+side*20
    local skin = source:getPixel(side==0 and 4 or 10,y0+9)
    for breath = 0,1 do
      local index = side*2+breath+1
      if index>1 then sprite:newEmptyFrame() end
      local image = Image(14,20,ColorMode.RGB)
      for y=0,19 do for x=0,13 do image:putPixel(x,y,source:getPixel(x,y0+y)) end end
      -- Remove both pixels of the visible eye; fill the mouth notch.
      local eye = side==0 and 5 or 9
      image:putPixel(eye,10,skin)
      image:putPixel(eye,11,skin)
      image:putPixel(side==0 and 4 or 10,12,skin)
      if breath==1 then
        -- Lift only the chest by one art pixel; head and feet stay planted.
        for y=14,15 do
          local edge = side==0 and 4 or 10
          local outside = side==0 and 3 or 11
          local inside = side==0 and 5 or 9
          image:putPixel(outside,y,image:getPixel(edge,y))
          image:putPixel(edge,y,image:getPixel(inside,y))
        end
      end
      if index==1 then sprite.cels[1].image=image
      else sprite:newCel(sprite.layers[1],sprite.frames[index],image,Point(0,0)) end
      sprite.frames[index].duration=0.9
    end
  end
  local left=sprite:newTag(1,2);left.name='sleep_left'
  local right=sprite:newTag(3,4);right.name='sleep_right'
  sprite:saveAs(root .. 'art/npcs/' .. name .. '_sleep_simple.aseprite')
  app.command.ExportSpriteSheet{ui=false,type=SpriteSheetType.HORIZONTAL,
    textureFilename=root .. 'assets/npcs/' .. name .. '_sleep_simple.png',
    dataFilename=root .. 'assets/npcs/' .. name .. '_sleep_simple.json',
    dataFormat=SpriteSheetDataFormat.JSON_ARRAY, listTags=true}
end
