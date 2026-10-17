"""Remove generated texture using deliberate flat material regions via pixel MCP."""
from pathlib import Path
import sys
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'art/direction'))
from mcpc import Pixel
from fcremap import lab_dist

SOURCE = ROOT/'pixellab-out/2026-10-17T0239-51-aspidochelone-original-frame0-redraw-the-sour/51-aspidochelone-frame0-draft.png'
OUT = ROOT/'art/enemies/51_aspidochelone_frame0_draft.aseprite'
PAL = dict(K='000000', D='463422', M='605028', L='8d6b4f',
           S='d0c078', H='f4ce80', Q='b2966a', G='235436',
           g='058f3a', l='4fa667', T='633e1b', B='84a7e9',
           b='3e91cc', W='dcf0ff', F='fc9838')


def inside(x, y, points):
    hit = False
    j = len(points)-1
    for i, (a,b) in enumerate(points):
        c,d = points[j]
        if (b>y) != (d>y) and x < (c-a)*(y-b)/(d-b)+a:
            hit = not hit
        j = i
    return hit


SKIN_LIGHTS = [
    [(73,61),(79,60),(85,63),(86,67),(82,66),(80,64),(75,65),(74,69),(72,68)],
    [(39,69),(50,65),(58,65),(54,68),(50,69),(45,73),(39,74)],
    [(91,61),(98,62),(106,62),(104,65),(96,65),(93,64)],
    [(25,59),(29,58),(35,60),(33,62),(27,61)],
]
SKIN_SHADOWS = [
    [(68,61),(73,61),(72,68),(77,73),(85,74),(89,71),(89,80),(71,80),(65,73)],
    [(32,74),(45,74),(54,70),(60,67),(64,69),(57,76),(43,80),(32,78)],
    [(88,67),(98,67),(110,63),(111,73),(92,74)],
]
SAND_LIGHT = [(34,54),(40,51),(45,52),(48,56),(62,58),(73,57),
              (83,56),(91,51),(97,52),(95,55),(85,60),(71,63),
              (53,64),(42,61),(34,58)]
GRASS_DARK = [(43,45),(53,42),(69,42),(78,46),(72,49),(60,50),(53,47),(46,49)]
GRASS_LIGHT = [(49,49),(58,51),(65,49),(73,48),(83,48),(87,51),
               (80,53),(73,54),(64,54),(58,53),(52,55)]


def main():
    if OUT.exists():
        raise RuntimeError(f'Refusing to overwrite {OUT}')
    im = Image.open(SOURCE).convert('RGBA')
    assert im.size == (130,81)
    pixels=[]
    for y in range(81):
        for x in range(130):
            r,g,b,a = im.getpixel((x,y))
            if not a:
                continue
            if max(r,g,b)<25:
                tone='K'
            elif b>r+30 and b>g+20:
                tone='B' if g>135 else 'b'
            elif min(r,g,b)>220:
                tone='W'
            elif r>200 and 100<g<170 and b<80:
                tone='F'
            elif g>r+12 and g>b+20:
                if y>=44:
                    tone='g'
                    if inside(x+.5,y+.5,GRASS_DARK):tone='G'
                    if inside(x+.5,y+.5,GRASS_LIGHT):tone='l'
                else:
                    # Canopy clusters remain individually composed; no grass speckles.
                    tone=min(('G','g','l'),key=lambda t:lab_dist((r,g,b),tuple(bytes.fromhex(PAL[t]))))
            elif y<46:
                if g>r and g>b+20:
                    tone='g' if r>90 else 'G'
                else:
                    tone='T'
            elif r>=140 and g>=100 and r>g and (y<62 or (x<69 and y<65)):
                tone='H' if inside(x+.5,y+.5,SAND_LIGHT) else 'S'
                if g<120:tone='Q'
            else:
                tone='M'
                if any(inside(x+.5,y+.5,poly) for poly in SKIN_SHADOWS):tone='D'
                if any(inside(x+.5,y+.5,poly) for poly in SKIN_LIGHTS):tone='L'
            boundary=any(not (0<=x+dx<130 and 0<=y+dy<81)
                         or not im.getpixel((x+dx,y+dy))[3]
                         for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)))
            if boundary and y>=46:
                tone='K'
            elif boundary and x>0 and x<129 and not im.getpixel((x-1,y))[3] and im.getpixel((x+1,y))[3]:
                # One-sided outline leaves one-pixel frond tips readable.
                tone='K'
            pixels.append(dict(x=x,y=y,color='#'+PAL[tone]))
    p=Pixel()
    canvas=p.call('create_canvas',width=130,height=81,color_mode='rgb')['file_path']
    p.call('save_as',sprite_path=canvas.replace('\\','/'),output_path=OUT.as_posix())
    info=p.call('get_sprite_info',sprite_path=OUT.as_posix())
    for i in range(0,len(pixels),1500):
        p.call('draw_pixels',sprite_path=OUT.as_posix(),layer_name=info['layers'][0],
               frame_number=1,pixels=pixels[i:i+1500])
    p.call('set_palette',sprite_path=OUT.as_posix(),colors=['#'+c for c in PAL.values()])
    p.call('export_sprite',sprite_path=OUT.as_posix(),output_path=OUT.with_suffix('.png').as_posix(),format='png',frame_number=1)
    print(json.dumps(p.call('get_sprite_info',sprite_path=OUT.as_posix())))
    p.p.terminate()


if __name__=='__main__':main()
