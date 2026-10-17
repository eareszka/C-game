local root = 'C:/Users/emery/OneDrive/Desktop/projects/C-game/'
local source = app.open(root .. 'pixellab-out/girl-sleep/sprites/v8/girl-sleep-pixellab.png')
local sheet = source.cels[1].image
local sprite = Sprite(14, 20, ColorMode.RGB)
for index = 0, 2 do
  if index > 0 then sprite:newEmptyFrame() end
  local image = Image(14, 20, ColorMode.RGB)
  image:drawImage(sheet, Point(-1-index*14, 0))
  sprite:newCel(sprite.layers[1], sprite.frames[index+1], image, Point(0, 0))
  sprite.frames[index+1].duration = 0.7
end
local tag = sprite:newTag(1, 3)
tag.name = 'sleep_side_draft'
tag.aniDir = AniDir.PING_PONG
sprite:saveAs(root .. 'art/npcs/girl_sleep_pixellab_draft.aseprite')
