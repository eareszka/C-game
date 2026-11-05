-- Runs inside the Aseprite window edit_sheet.py opens. Selects the sprites layer, so the first stroke lands there, then
-- paints in each new drawing that edit_sheet.py leaves in the sheet's inbox folder. Aseprite wouldn't notice them otherwise.
local p = app.params
local spr = app.sprite
if not spr then return end

local function sprites_layer()
  for _, layer in ipairs(spr.layers) do
    if layer.name == "sprites" then return layer end
  end
end

local layer = sprites_layer()
if layer then app.layer = layer end

local inbox = p.inbox
if not inbox or inbox == "" then return end
local last = tonumber(p.seq) or 0

-- The oldest patch not painted yet, or nil. Its name is seq_x_y_w_h.png.
local function next_patch()
  local best, best_seq
  for _, name in ipairs(app.fs.listFiles(inbox)) do
    local seq = tonumber(name:match("^(%d+)_"))
    if seq and seq > last and (not best_seq or seq < best_seq) then
      best, best_seq = name, seq
    end
  end
  return best, best_seq
end

local function paint(name)
  local x, y, w, h = name:match("^%d+_(%d+)_(%d+)_(%d+)_(%d+)%.png$")
  x, y, w, h = tonumber(x), tonumber(y), tonumber(w), tonumber(h)
  local target = sprites_layer()
  if not target then return end
  local cel = target:cel(1)
  local full = Image(spr.spec)
  if cel then full:drawImage(cel.image, cel.position) end
  full:clear(Rectangle(x, y, w, h))
  full:drawImage(Image{ fromFile = app.fs.joinPath(inbox, name) }, Point(x, y))
  app.transaction("New drawing", function()
    if cel then
      cel.image = full
      cel.position = Point(0, 0)
    else
      spr:newCel(target, 1, full, Point(0, 0))
    end
  end)
  app.refresh()
end

-- A global, so the timer outlives this script. One patch a tick, and only while the sheet is the tab showing.
editSheetTimer = Timer{
  interval = 5.0,
  ontick = function()
    local alive = pcall(function() return spr.filename end)
    if not alive then
      editSheetTimer:stop()
      return
    end
    if app.sprite ~= spr then return end
    local name, seq = next_patch()
    if name then
      last = seq
      pcall(paint, name)
    end
  end,
}
editSheetTimer:start()
