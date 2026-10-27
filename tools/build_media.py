"""Clean build: ehyun-site-assets -> site/m/<slug>/..., build.json
Naming: tile.mp4 / tile-p.jpg (poster) / tile.jpg (still), hero.mp4 / hero-p.jpg, g01.mp4|g01.jpg (no posters for gallery clips)
Usage: python3 build_media.py listing.json [exclude.json]"""
import os, re, json, subprocess, sys, hashlib, shutil
SRC='/mnt/user-data/uploads/ehyun-site-assets'
SITE='/home/claude/site'; ROOT='m'; OUT=f'{SITE}/{ROOT}'
listing=json.load(open(sys.argv[1]))
exclude=set(json.load(open(sys.argv[2]))) if len(sys.argv)>2 else set()
IMG=('.jpg','.jpeg','.png','.webp','.tif','.tiff'); VID=('.mp4','.mov','.gif','.webm')
def probe(f):
    o=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height:format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout.strip().split('\n')
    w,h=map(int,o[0].split(',')[:2]); d=float(o[1]) if len(o)>1 and o[1] not in ('','N/A') else 0
    return w,h,d
def ratio(w,h):
    r=w/h
    if abs(r-16/9)<0.02: return None
    if abs(r-1)<0.02: return 'sq'
    from math import gcd; g=gcd(w,h); return f'{w//g} / {h//g}'
def fhash(p):
    m=hashlib.md5()
    with open(p,'rb') as f:
        for b in iter(lambda: f.read(1<<20), b''): m.update(b)
    return m.hexdigest()
def sig(src): st=os.stat(src); return f'{src}|{st.st_size}|{int(st.st_mtime)}'
def fresh(dst,src): return os.path.exists(dst) and os.path.exists(dst+'.src') and open(dst+'.src').read()==sig(src)
def mark(dst,src): open(dst+'.src','w').write(sig(src))
def run(a): subprocess.run(a,check=True)
def rel(p): return p[len(SITE)+1:]
def venc(src,dst,crf=25,w=1280,poster=None):
    if not fresh(dst,src):
        run(['ffmpeg','-v','error','-y','-i',src,'-an','-map','0:v:0','-vf',f"scale='min({w},iw)':-2:flags=lanczos,fps=30,format=yuv420p",'-c:v','libx264','-profile:v','high','-level','4.0','-preset','slow','-crf',str(crf),'-movflags','+faststart',dst]); mark(dst,src)
    if poster and not fresh(poster,src):
        d=probe(dst)[2]
        run(['ffmpeg','-v','error','-y','-ss',str(max(0.0,d*0.5)),'-i',dst,'-frames:v','1','-q:v','3',poster]); mark(poster,src)
    return rel(dst)
def ienc(src,dst,w=1920):
    if fresh(dst,src): return rel(dst)
    from PIL import Image
    im=Image.open(src)
    if im.mode in ('RGBA','LA','P','PA'):
        im=im.convert('RGBA'); bg=Image.new('RGBA',im.size,(0,0,0,255)); bg.alpha_composite(im); im=bg
    im=im.convert('RGB'); im.thumbnail((w,w*4),Image.LANCZOS); im.save(dst,quality=85,optimize=True,progressive=True); mark(dst,src)
    return rel(dst)
def skey(f): return re.sub(r'[_\s]+','-',f.lower())
order=[]; removed=[]; assets={}; notes=[]
for folder in sorted(listing):
    if folder.startswith('_'): continue
    if folder.lower().startswith('xxx'):
        removed.append(re.sub(r'^xxx-?(\d+-)?','',folder)); continue
    slug=re.sub(r'^\d+-','',folder); order.append(slug)
    sd=f'{SRC}/{folder}'
    if not os.path.isdir(sd): continue
    files=sorted((f for f in os.listdir(sd) if not f.startswith('_') and not f.lower().startswith('xxx') and f'{folder}/{f}' not in exclude and f.lower().endswith(IMG+VID)),key=skey)
    if not files: continue
    od=f'{OUT}/{slug}'; os.makedirs(od,exist_ok=True)
    base=lambda f: re.sub(r'(\.[a-z0-9]+)+$','',f.lower())
    tile=[f for f in files if base(f)=='tile']; hero=[f for f in files if base(f)=='hero']
    gal=[f for f in files if f not in tile+hero]
    hero_motion=bool(hero) and hero[0].lower().endswith(VID)
    if not tile and not hero_motion:
        for f in gal:
            if f.lower().endswith(VID) and probe(f'{sd}/{f}')[2]<=25:
                tile.append(f); gal.remove(f); notes.append(f'{slug}: used {f} as the grid loop'); break
    # drop gallery files that are byte-identical to the tile/hero, or to an earlier gallery file
    seen={fhash(f'{sd}/{f}') for f in tile+hero}; g2=[]
    for f in gal:
        x=fhash(f'{sd}/{f}')
        if x in seen: notes.append(f'{slug}: skipped {f} (same file as another)'); continue
        seen.add(x); g2.append(f)
    gal=g2
    a={'gallery':[]}
    for f in tile:
        s=f'{sd}/{f}'
        if f.lower().endswith(VID): a['tile']=venc(s,f'{od}/tile.mp4',26,poster=f'{od}/tile-p.jpg'); a['poster']=rel(f'{od}/tile-p.jpg')
        else: a['still']=ienc(s,f'{od}/tile.jpg')
    if a.get('still'): a['poster']=a['still']
    for f in hero:
        s=f'{sd}/{f}'; w,h,_=probe(s); r=ratio(w,h)
        if f.lower().endswith(VID): a['heroVideo']=venc(s,f'{od}/hero.mp4',28,poster=f'{od}/hero-p.jpg'); a['heroPoster']=rel(f'{od}/hero-p.jpg')
        else: a['hero']=ienc(s,f'{od}/hero.jpg')
        if r and r!='sq': a['heroRatio']=r
    for i,f in enumerate(gal,1):
        s=f'{sd}/{f}'; w,h,d=probe(s); r=ratio(w,h)
        if f.lower().endswith(VID): g={'type':'video','src':venc(s,f'{od}/g{i:02d}.mp4',27 if d>30 else 25)}
        else: g={'type':'image','src':ienc(s,f'{od}/g{i:02d}.jpg')}
        if r=='sq': g['sq']=True
        elif r: g['ratio']=r
        a['gallery'].append(g)
    if not tile and a.get('heroVideo'):
        a['tile']=a['heroVideo']; a['poster']=a['heroPoster']; notes.append(f'{slug}: used the hero as the grid loop')
    if 'poster' not in a and a['gallery']:
        g=a['gallery'][0]
        if g['type']=='image': a['poster']=g['src']
    assets[slug]=a
# remove outputs no longer referenced
refs=set()
for a in assets.values():
    for k in ('tile','poster','still','hero','heroVideo','heroPoster'):
        if a.get(k): refs.add(a[k])
    for g in a['gallery']: refs.add(g['src'])
for dp,_,fs in os.walk(OUT):
    for f in fs:
        p=rel(os.path.join(dp,f))
        if not f.endswith('.src') and p not in refs: os.remove(os.path.join(dp,f)); notes.append(f'cleaned {p}')
json.dump({'order':order,'removed':removed,'assets':assets,'notes':notes},open(f'{SITE}/build.json','w'),indent=1)
print('order',len(order),'files',len(refs)); print('\n'.join(n for n in notes if not n.startswith('cleaned')))
