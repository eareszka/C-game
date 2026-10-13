"""Install the verified enemy 83 replacement sheets and matching part anchors.

Run after 83_beast_of_barrisdale_design.py. Keeps backups before replacing assets.
"""
from pathlib import Path
import importlib.util
import json
import shutil
import subprocess
import sys
from datetime import datetime
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'art/enemies'
sys.path.insert(0,str(ROOT/'tools'))
import enemy_sheet
spec=importlib.util.spec_from_file_location('design83',HERE/'83_beast_of_barrisdale_design.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)


def cpp_anchors():
    lines=['    struct PartFrame { float mouth[2]; float wings[2][2]; float feet[3][2]; };',
           '    // Exact pixel positions in the padded 100x65 cells, matching the shown frame.',
           '    static constexpr PartFrame ART[2][10] = {']
    pair=lambda p:'{'+','.join(f'{n:.1f}f' for n in p)+'}'
    for name,frames in [('grounded',d.anchors()),('airborne',d.anchors(True))]:
        lines.append('        { // '+name)
        for a in frames:
            lines.append('            {'+pair(a['mouth'])+', {'+', '.join(pair(p) for p in a['wings'])+'}, {'+', '.join(pair(p) for p in a['feet'])+'}},')
        lines.append('        },')
    lines+=['    };','    int draw_frame = 0;','    const PartFrame& art() const { return ART[ENRAGED ? 1 : 0][draw_frame]; }']
    return '\n'.join(lines)+'\n'


def update_code():
    battle=ROOT/'src/battle.cpp'
    before=battle.read_bytes()
    old=b'{ "assets/enemies/83_beast_of_barrisdale.png",    {}, 5, false, "assets/enemies/83_beast_of_barrisdale_fly.png" },  // big, 8 dirs: massive three-legged bat-winged beast; frame 2 rears and roars; flap = flying, legs swept back'
    new=b'{ "assets/enemies/83_beast_of_barrisdale.png",    {}, 10, true, nullptr, "assets/enemies/83_beast_of_barrisdale_fly.png", nullptr, 1, 1, nullptr, 130 },  // 100x65, 10 frames at 130 ms: planted breathing idle; alt = tucked airborne pose for all phase two; one left-facing view'
    assert before.count(old)==1,'Inspect enemy 83 sprite entry before reinstalling'
    path=ROOT/'src/enemies.cpp'
    raw=path.read_bytes();nl='\r\n' if b'\r\n' in raw else '\n'
    text=raw.decode('utf-8').replace('\r\n','\n')
    start=text.index('class BeastOfBarrisdale : public Enemy {')
    end=text.index('\n};',start)+3
    original=text[start:end]
    c=original
    def change(old,new):
        nonlocal c
        assert c.count(old)==1,('Enemy 83 source changed',old[:75])
        c=c.replace(old,new)
    change('    float loop_t = 0.0f, talon_t = 0.0f, state_t = 0.0f;',cpp_anchors()+'    float loop_t = 0.0f, talon_t = 0.0f, state_t = 0.0f;')
    change('art px (98x65, drawn 2x about its middle)','art px (100x65, drawn 2x about its middle)')
    change('*ox = x + (fx - 49.0f) * 2.0f;', '*ox = x + (fx - 50.0f) * 2.0f;')
    change('    float       flap_phase()    const override { return ENRAGED && (!aloft || flying) ? fmodf(state_t / 0.7f, 1.0f) : -1.0f; }   // a slow, heavy wingbeat',
           '    bool        alt_pose()      const override { return ENRAGED; }   // tucked flight sheet during ascent, flight AND hover')
    change('''    int         move_facing()   const override {
        if (!ENRAGED || hanging()) return FACE_DOWN;
        if (!aloft) return FACE_UP;                               // rising
        return facing_toward(LOOP_X * cosf(loop_t * LOOP_W), LOOP_Y * 2.0f * cosf(loop_t * 2.0f * LOOP_W));
    }''','''    int         move_facing()   const override { return FACE_DOWN; }   // the one authored view already faces left''')
    change('''            if (hypotf(x - px, y - py) >= ROAR_CLEAR) n += roar(x, y - 10.0f, out + n, max - n);''','''            float mx, my;
            at(art().mouth[0], art().mouth[1], &mx, &my);
            if (hypotf(mx - px, my - py) >= ROAR_CLEAR) n += roar(mx, my, out + n, max - n);''')
    change('''            float lx = x, ly = y + 40.0f;
            if (hypotf(lx - px, ly - py) < CLEAR) continue;
            for (int k = -1; k <= 1; k++) {
                BulletSpawn b = mk(PI / 2 + k * 0.4f, SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = lx; b.oy = ly;
                out[n++] = b;
            }''','''            for (int k = -1; k <= 1; k++) {
                float lx, ly;
                at(art().feet[k + 1][0], art().feet[k + 1][1], &lx, &ly);
                if (hypotf(lx - px, ly - py) < CLEAR) continue;
                BulletSpawn b = mk(PI / 2 + k * 0.4f, SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = lx; b.oy = ly;
                out[n++] = b;
            }''')
    change('''    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int max) override {
        if (ENRAGED && !hanging()) return 0;''','''    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int max) override {
        draw_frame = frame;   // both sheets use the same clock as these attacks
        if (frame % 2 != 0) return 0;   // in-betweens: keep the original 5 attack beats
        frame /= 2;
        if (ENRAGED && !hanging()) return 0;''')
    change('''            float wy = frame == 1 ? 29.0f : 37.0f;
            for (int side = -1; side <= 1; side += 2) {
                float wx, wyy;
                at(side < 0 ? 21.0f : 68.0f, wy, &wx, &wyy);''','''            for (int side = -1; side <= 1; side += 2) {
                float wx, wyy;
                const float* tip = art().wings[side < 0 ? 0 : 1];
                at(tip[0], tip[1], &wx, &wyy);''')
    change('''            static const float FX[3] = { 40.0f, 58.0f, 49.0f }, FY[3] = { 63.0f, 63.0f, 59.0f };
            float turn = ernd() * TAU;''','''            float turn = ernd() * TAU;''')
    change('                at(FX[f], FY[f], &fx, &fy);','                at(art().feet[f][0], art().feet[f][1], &fx, &fy);')
    change('            at(54.0f, 35.0f, &mx, &my);                          // its mouth, reared up roaring',
           '            at(art().mouth[0], art().mouth[1], &mx, &my);        // the edited mouth, on the frame shown')
    updated=text[:start]+c+text[end:]
    # Comments immediately above this class describe the final replacement art.
    updated=updated.replace('// frame 2 it rears, wings thrown high, roaring); flap = 83_..._fly. Every',
                            '// gentle wing motion and breathing); alt = 83_..._fly, tucked in flight. Every',1)
    updated=updated.replace('//   Roar      -- rearing (idle frame 2) it ROARS: three rings close behind',
                            '//   Roar      -- idle frame 2, from its open mouth: three rings close behind',1)
    updated=updated.replace('//   Hanging -- HANG_T s still in the air (the idle sheet: wings beating, the',
                            '//   Hanging -- HANG_T s still in the air (the airborne sheet: wings beating, the',1)
    return {battle:before.replace(old,new),path:updated.replace('\n',nl).encode('utf-8')}


def main():
    # Validate every stage before replacing a playable asset.
    for air,name in [(False,'83_beast_of_barrisdale_idle_draft'),(True,'83_beast_of_barrisdale_air_draft')]:
        strip=Image.open(HERE/(name+'.png')).convert('RGBA')
        for i,g in enumerate(d.frames(air)):
            assert strip.crop((i*d.W,0,(i+1)*d.W,d.H)).tobytes()==d.image(g).tobytes()
    code_updates=update_code()   # check all source expectations before replacing any asset
    backup=ROOT/'art/_backup'/('83_before_install_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True,exist_ok=False)
    for rel in ['assets/enemies/83_beast_of_barrisdale.png','assets/enemies/83_beast_of_barrisdale.aseprite',
                'assets/enemies/83_beast_of_barrisdale_fly.png','assets/enemies/83_beast_of_barrisdale_fly.aseprite',
                'assets/enemies/built.json','src/battle.cpp','src/enemies.cpp']:
        dest=backup/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dest)
    for air,stage,name in [(False,'83_beast_of_barrisdale_idle_draft','83_beast_of_barrisdale'),
                           (True,'83_beast_of_barrisdale_air_draft','83_beast_of_barrisdale_fly')]:
        strip=Image.open(HERE/(stage+'.png')).convert('RGBA')
        sheet=Image.new('RGBA',(10*d.W,8*d.H))
        for view in range(8):sheet.paste(strip,(0,view*d.H))
        png=ROOT/'assets/enemies'/(name+'.png');ase=png.with_suffix('.aseprite')
        sheet.save(png)
        tags=enemy_sheet.pack(sheet,str(ase),10,True)
        px=d.Pixel()
        try:px.call('set_palette',sprite_path=str(ase).replace('\\','/'),colors=['#'+h for h in d.PAL.values()])
        finally:px.p.terminate()
        # Pack's generic editor duration is 250ms. Match the game's 130ms clock.
        lua=ROOT/'art/_work/83_set_duration.lua'
        lua.write_text('local s=app.open(app.params.source)\nfor _, f in ipairs(s.frames) do f.duration=0.13 end\ns:saveAs(app.params.source)\n')
        subprocess.run([enemy_sheet.ASEPRITE,'-b','--script-param','source='+str(ase).replace('\\','/'),'--script',str(lua)],check=True)
        enemy_sheet.export(str(ase))
        assert Image.open(png).convert('RGBA').tobytes()==sheet.tobytes()
        enemy_sheet.built(str(png))
        print('Installed',name,'tags',tags,'100x65, 10 frames, 130ms, no mirrored views')
    for path,data in code_updates.items():path.write_bytes(data)
    print('Prior game assets/source backed up in',backup)


if __name__=='__main__':main()
