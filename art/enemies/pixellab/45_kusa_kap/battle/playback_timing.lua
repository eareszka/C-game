local s=app.open(app.params.source)
local t={0.4,0.25,0.4,0.25}
for i,f in ipairs(s.frames) do f.duration=t[(i-1)%4+1] end
s:saveAs(app.params.source)
s:close()
