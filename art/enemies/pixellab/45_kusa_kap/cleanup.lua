-- Separate cleanup of the PixelLab draft, preserving every input file.
local dir = app.params.dir
local s = app.open(app.params.input or (dir .. '/idle_frame0_draft.png'))
local im = s.cels[1].image
local pc = app.pixelColor
local colors = {
  {0,0,0}, {52,30,16}, {141,107,79}, {252,252,252},
  {240,188,60}, {89,89,101}, {132,134,148}
}
local function dist(r,g,b,c)
  return (r-c[1])^2 + (g-c[2])^2 + (b-c[3])^2
end
app.transaction(function()
  -- Restore the carried animal when the generated angled view reduced it
  -- to an unreadable fleck. Reference is an original directional creature
  -- silhouette; the approved front uses its own approved prey drawing.
  if app.params.prey then
    local ref = Image{fromFile=app.params.prey}
    local function grey(v)
      local r,g,b=pc.rgbaR(v),pc.rgbaG(v),pc.rgbaB(v)
      if pc.rgbaA(v)==0 then return false end
      if app.params.front=='1' then return r==89 and g==89 and b==101 end
      return (r==140 and g==148 and b==156) or (r==92 and g==100 and b==108)
    end
    local minx,miny,maxx,maxy=ref.width,ref.height,-1,-1
    local mask={}
    for y=0,ref.height-1 do for x=0,ref.width-1 do
      if grey(ref:getPixel(x,y)) and (app.params.front~='1' or y>=35) then
        mask[x..','..y]=true
        minx=math.min(minx,x); miny=math.min(miny,y)
        maxx=math.max(maxx,x); maxy=math.max(maxy,y)
      end
    end end
    local top,bottom=im.height,0
    for y=0,im.height-1 do for x=0,im.width-1 do
      if pc.rgbaA(im:getPixel(x,y))>0 then top=math.min(top,y);bottom=math.max(bottom,y) end
    end end
    local sx,n,legy=0,0,0
    for y=math.floor((top+bottom)/2),im.height-1 do for x=0,im.width-1 do
      local v=im:getPixel(x,y)
      if pc.rgbaA(v)>0 and pc.rgbaR(v)>160 and pc.rgbaG(v)>100 and pc.rgbaB(v)<100 then
        sx=sx+x;n=n+1;legy=math.max(legy,y)
      end
    end end
    if n==0 then
      local gy=im.height
      for y=math.floor((top+bottom)/2),im.height-1 do for x=0,im.width-1 do
        local v=im:getPixel(x,y)
        if pc.rgbaA(v)>0 and pc.rgbaR(v)==89 and pc.rgbaG(v)==89 and pc.rgbaB(v)==101 then
          sx=sx+x;n=n+1;gy=math.min(gy,y)
        end
      end end
      if n>0 then legy=gy+1 end
    end
    if n==0 then
      sx=im.width/2;n=1;legy=bottom-4
    end
    -- Fixed reference placement prevents the carried animal sliding between
    -- wingbeat poses. Bird pixels remain in front where the wings overlap it.
    sx=(minx+maxx)/2+16;n=1;legy=miny+17
    if app.params.back=='1' then legy=legy+8 end
    if n>0 and maxx>=minx then
      local old=im:clone()
      for y=math.floor((top+bottom)/2),im.height-1 do for x=0,im.width-1 do
        local v=old:getPixel(x,y)
        if pc.rgbaA(v)>0 and pc.rgbaR(v)==pc.rgbaG(v) and pc.rgbaB(v)>pc.rgbaR(v) then
          im:drawPixel(x,y,0)
          for _,d in ipairs({{1,0},{-1,0},{0,1},{0,-1}}) do
            local xx,yy=x+d[1],y+d[2]
            if xx>=0 and xx<im.width and yy>=0 and yy<im.height then
              if old:getPixel(xx,yy)==pc.rgba(0,0,0,255) then im:drawPixel(xx,yy,0) end
            end
          end
        end
      end end
      local dx=math.floor(sx/n-(maxx-minx)/2)-minx
      local dy=legy-1-miny
      for y=miny,maxy do for x=minx,maxx do
        if mask[x..','..y] then
          local xx,yy=x+dx,y+dy
          assert(xx>0 and xx<im.width-1 and yy>0 and yy<im.height-1,'prey outside canvas')
          local q=im:getPixel(xx,yy)
          if pc.rgbaA(q)==0 or (pc.rgbaR(q)==pc.rgbaG(q) and pc.rgbaB(q)>pc.rgbaR(q)) then
            im:drawPixel(xx,yy,pc.rgba(89,89,101,255))
          end
        end
      end end
    end
  end
  if app.params.native=='1' then
    -- Redraw only overshooting wing tips inward on the padded working canvas.
    -- Keep a pixel for the outline inside the original 78x59 runtime cell.
    local old=im:clone()
    im:clear()
    for y=0,old.height-1 do for x=0,old.width-1 do
      local v=old:getPixel(x,y)
      if pc.rgbaA(v)>0 then
        im:drawPixel(math.max(18,math.min(91,x)),math.max(18,math.min(72,y)),v)
      end
    end end
  end
  -- Restrict materials to the shared game ramp, retaining raw provider output.
  for p in im:pixels() do
    local v=p()
    if pc.rgbaA(v)>0 then
      local best, score=1, math.huge
      for k,c in ipairs(colors) do
        local d=dist(pc.rgbaR(v),pc.rgbaG(v),pc.rgbaB(v),c)
        if d<score then best,score=k,d end
      end
      local c=colors[best]
      p(pc.rgba(c[1],c[2],c[3],255))
    else p(0) end
  end
  -- Add a single black pixel along exposed material edges, without eroding anatomy.
  local old=im:clone()
  for y=0,im.height-1 do for x=0,im.width-1 do
    if pc.rgbaA(old:getPixel(x,y))==0 then
      local edge=false
      for _,d in ipairs({{1,0},{-1,0},{0,1},{0,-1}}) do
        local xx,yy=x+d[1],y+d[2]
        if xx>=0 and xx<im.width and yy>=0 and yy<im.height then
          local q=old:getPixel(xx,yy)
          if pc.rgbaA(q)>0 and (pc.rgbaR(q)>0 or pc.rgbaG(q)>0 or pc.rgbaB(q)>0) then edge=true end
        end
      end
      if edge then im:drawPixel(x,y,pc.rgba(0,0,0,255)) end
    end
  end end
  -- Three material colors plus black in each native 16px cell.
  for ty=0,im.height-1,16 do for tx=0,im.width-1,16 do
    local counts={}
    for y=ty,math.min(ty+15,im.height-1) do for x=tx,math.min(tx+15,im.width-1) do
      local v=im:getPixel(x,y)
      if pc.rgbaA(v)>0 and v~=pc.rgba(0,0,0,255) then counts[v]=(counts[v] or 0)+1 end
    end end
    local ranked={}
    for v,n in pairs(counts) do table.insert(ranked,{v=v,n=n}) end
    local yellow=pc.rgba(240,188,60,255)
    table.sort(ranked,function(a,b)
      if a.v==yellow then return true end
      if b.v==yellow then return false end
      if a.n==b.n then return a.v<b.v else return a.n>b.n end
    end)
    if #ranked>3 then
      local keep={}
      for k=1,3 do keep[ranked[k].v]=true end
      for y=ty,math.min(ty+15,im.height-1) do for x=tx,math.min(tx+15,im.width-1) do
        local v=im:getPixel(x,y)
        if counts[v] and not keep[v] then
          local best,score=ranked[1].v,math.huge
          for k=1,3 do
            local q=ranked[k].v
            local d=dist(pc.rgbaR(v),pc.rgbaG(v),pc.rgbaB(v),{pc.rgbaR(q),pc.rgbaG(q),pc.rgbaB(q)})
            if d<score then best,score=q,d end
          end
          im:drawPixel(x,y,best)
        end
      end end
    end
  end end
end)
s:saveAs(app.params.output or (dir .. '/idle_frame0_clean_v3.png'))
s:close()
