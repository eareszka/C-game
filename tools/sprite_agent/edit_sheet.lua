-- Builds or updates an edit sheet's .aseprite. Run in batch mode, by edit_sheet.py only.
local p = app.params

local function find_layer(spr, name)
  for _, layer in ipairs(spr.layers) do
    if layer.name == name then return layer end
  end
end

if p.mode == "fill" then
  -- Makes the saved sheet's sprites layer match the picture given. Everything else in the file stays.
  local spr = Sprite{ fromFile = p.sheet }
  local layer = find_layer(spr, "sprites")
  if not layer then
    layer = spr:newLayer()
    layer.name = "sprites"
  end
  local cel = layer:cel(1)
  if cel then
    cel.image = Image{ fromFile = p.sprites }
    cel.position = Point(0, 0)
  else
    spr:newCel(layer, 1, Image{ fromFile = p.sprites }, Point(0, 0))
  end
  spr:saveAs(p.sheet)
  return
end

local first = Image{ fromFile = p.sprites }
local spr = Sprite(first.width, first.height, ColorMode.RGB)

local black = spr.layers[1]
black.name = "black"
spr:newCel(black, 1, Image{ fromFile = p.black }, Point(0, 0))
black.isVisible = false
black.isEditable = false

local guides = spr:newLayer()
guides.name = "guides"
spr:newCel(guides, 1, Image{ fromFile = p.guides }, Point(0, 0))
guides.isEditable = false

local sprites = spr:newLayer()
sprites.name = "sprites"
spr:newCel(sprites, 1, first, Point(0, 0))

local colours = Image{ fromFile = p.colours }
local pc = app.pixelColor
local palette = Palette(colours.width)
for x = 0, colours.width - 1 do
  local v = colours:getPixel(x, 0)
  palette:setColor(x, Color{ r = pc.rgbaR(v), g = pc.rgbaG(v), b = pc.rgbaB(v), a = 255 })
end
spr:setPalette(palette)

spr:saveAs(p.out)
