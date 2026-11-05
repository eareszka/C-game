import sys, numpy as np
t=np.fromfile(sys.argv[1],dtype=np.int32).reshape(3000,3000)
def integ(m):
    s=np.zeros((3001,3001),np.int64); s[1:,1:]=m.astype(np.int64).cumsum(0).cumsum(1); return s
def box(s,y,x,h,w): return s[y+h,x+w]-s[y,x+w]-s[y+h,x]+s[y,x]
snow=integ(t==18)
water=integ(t==3); river=integ(t==6)
cl=((t>=4)&(t<=16)&(t!=6))|((t>=24)&(t<=58))
cliff=integ(cl)
TW=156; CORE=68; PAD=int(sys.argv[2]) if len(sys.argv)>2 else 10
o=(TW-CORE)//2-PAD; inner=TW-2*o
res={'ok':0,'river_only':0,'cliff_only':0,'water':0,'both':0}; n=0
for y in range(0,3000-TW,4):
    for x in range(0,3000-TW,4):
        if box(snow,y+44,x+44,68,68)<0.90*68*68: continue
        f=box(snow,y,x,TW,TW)/TW/TW
        if f<0.40 or f>0.95: continue
        n+=1
        w=box(water,y+o,x+o,inner,inner); r=box(river,y+o,x+o,inner,inner); c=box(cliff,y+o,x+o,inner,inner)
        if w: res['water']+=1
        elif r and c: res['both']+=1
        elif r: res['river_only']+=1
        elif c: res['cliff_only']+=1
        else: res['ok']+=1
print('cands',n,res)
cs=[]
for y in range(0,3000-TW,4):
    for x in range(0,3000-TW,4):
        if box(snow,y+44,x+44,68,68)<0.90*68*68: continue
        f=box(snow,y,x,TW,TW)/TW/TW
        if f<0.40 or f>0.95: continue
        if box(water,y+o,x+o,inner,inner) or box(river,y+o,x+o,inner,inner): continue
        cs.append(box(cliff,y+o,x+o,inner,inner))
cs=np.array(cs); print('no-river cands',len(cs),'cliff pct',np.percentile(cs,[0,5,25,50]))
