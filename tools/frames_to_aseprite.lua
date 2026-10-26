-- Build an animated .aseprite from a numbered frame sequence, every frame one duration.
--   aseprite -b --script-param first=dir/name_0.png --script-param out=x.aseprite
--            --script-param ms=90 --script tools/frames_to_aseprite.lua
local first, out, ms = app.params["first"], app.params["out"], tonumber(app.params["ms"] or "100")
local spr = app.open(first)                 -- a numbered sequence opens as its frames
for _, f in ipairs(spr.frames) do f.duration = ms / 1000 end
spr:saveAs(out)
print(out .. ": " .. #spr.frames .. " frames at " .. ms .. " ms")
