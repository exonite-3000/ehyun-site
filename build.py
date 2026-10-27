#!/usr/bin/env python3
"""Generate the static site in public/ from content/*.json.

  content/projects.json  project text (title, client, role, video link, description, credits)
  content/media.json     project order + media files (written by tools/build_media.py)
  content/site.json      name, reel, social links, About page, removed projects

Run:  python3 build.py
Then commit and push; Cloudflare Pages serves public/ as-is.
"""
import json, html, re, os
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(ROOT, 'public')
J = lambda p: json.load(open(os.path.join(ROOT, p), encoding='utf-8'))
import hashlib
ASSET_V = hashlib.md5(open('public/assets/site.css','rb').read() + open('public/assets/site.js','rb').read()).hexdigest()[:8]
SITE, ALL, MEDIA = J('content/site.json'), J('content/projects.json'), J('content/media.json')
BYSLUG = {p['slug']: p for p in ALL}
ORDER = [s for s in MEDIA['order'] if s in BYSLUG]
PROJECTS = [BYSLUG[s] for s in ORDER]
ASSETS = MEDIA['assets']
e = lambda s: html.escape(str(s or ''), quote=True)
A = lambda p: ASSETS.get(p['slug'], {})
PLAY = '<span class="play"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3l16 9-16 9z"/></svg></span>'


def embed_url(url):
    """Vimeo / YouTube page URL -> autoplaying embed URL (None if unknown)."""
    u = urlparse(url or '')
    if 'vimeo.com' in u.netloc:
        parts = [x for x in u.path.split('/') if x]
        if not parts or not parts[0].isdigit():
            return None
        q = f'?h={parts[1]}&autoplay=1' if len(parts) > 1 else '?autoplay=1'
        return f'https://player.vimeo.com/video/{parts[0]}{q}'
    if 'youtube.com' in u.netloc or 'youtu.be' in u.netloc:
        vid = parse_qs(u.query).get('v', [None])[0] if 'youtube.com' in u.netloc else u.path.strip('/')
        return f'https://www.youtube-nocookie.com/embed/{vid}?autoplay=1&rel=0' if vid else None
    return None


def vid(src, poster=None, base=''):
    p = f' poster="{base}{poster}"' if poster else ''
    return f'<video class="m" src="{base}{src}"{p} muted loop playsinline preload="none" data-auto></video>'


def img(src, base='', lazy=True, alt=''):
    return f'<img class="m" src="{base}{src}" alt="{e(alt)}"{" loading=\"lazy\"" if lazy else ""} decoding="async">'


def mframe(inner, extra='', cls='', ratio=''):
    st = f' style="aspect-ratio:{ratio}"' if ratio else ''
    return f'<div class="frame media {cls}"{st}>{inner}{extra}</div>'


def ghost(text, extra=''):
    return f'<div class="frame"><div class="ghost">{e(text)}</div>{extra}</div>'


def tile(p, base):
    a = A(p)
    second = p.get('subtitle') if (p.get('client') == p['title'] and p.get('subtitle')) else (p.get('client') or p.get('subtitle') or p.get('type') or '')
    label = f'<div class="label"><span class="t">{e(p["title"])}' + (f'<span class="sep"> / </span><span class="c">{e(second)}</span>' if second else '') + '</span></div>'
    if a.get('tile'):
        f = mframe(vid(a['tile'], a.get('poster'), base), label)
    elif a.get('poster'):
        f = mframe(img(a['poster'], base, alt=p['title']), label)
    else:
        f = ghost(p['title'], label)
    return f'<a class="tile" href="{base}work/{p["slug"]}/" aria-label="{e(p["title"])}">{f}</a>'


def page(title, body, base, desc='', og_img='', path='', nav=None):
    url = SITE['domain'] + '/' + path
    ogi = f'<meta property="og:image" content="{SITE["domain"]}/{og_img}">\n<meta name="twitter:card" content="summary_large_image">' if og_img else '<meta name="twitter:card" content="summary">'
    cur = lambda n: ' aria-current="page"' if nav == n else ''
    social = ''.join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)}</a>' for n, u in SITE['social'])
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
{ogi}
<meta name="theme-color" content="#0b0c0e">
<link rel="icon" href="{base}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300..800&family=JetBrains+Mono:wght@300..800&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="{base}assets/site.css?v={ASSET_V}">
</head>
<body>
<header class="site"><div class="wrap">
  <a class="brand" href="{base}"><span class="name">{e(SITE["name"])}</span><span class="title">{e(SITE["title_line"])}</span></a>
  <nav class="main" aria-label="Main"><a href="{base}"{cur("work")}>Work</a><a href="{base}about/"{cur("about")}>About</a></nav>
</div></header>
<main>
{body}
</main>
<footer class="site"><div class="wrap">
  <span>© <span id="yr">2026</span> {e(SITE["name"])}</span>
  <nav aria-label="Contact and social">
    <a href="mailto:{e(SITE["email"])}" style="text-transform:none">{e(SITE["email"])}</a>
    {social}
  </nav>
</div></footer>
<script src="{base}assets/site.js?v={ASSET_V}" defer></script>
</body>
</html>
'''


def write(rel, s):
    p = os.path.join(PUB, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s)


def player(url, poster_html, label, autoplay=False):
    em = embed_url(url)
    if em and autoplay:
        # browsers only allow autoplay when muted; viewers unmute with the player controls
        em += '&muted=1&loop=1' if 'vimeo' in em else '&mute=1&loop=1&playlist=' + em.split('/embed/')[1].split('?')[0]
    if not em:
        return f'<div class="player"><a href="{e(url)}" target="_blank" rel="noopener" aria-label="{e(label)}">{poster_html}</a></div>'
    return f'<div class="player"><button type="button" class="playbtn" data-embed="{e(em)}"{' data-autoplay' if autoplay else ''} aria-label="{e(label)}">{poster_html}</button></div>'


def build_home():
    base = ''
    reel = SITE['reel']
    reel_html = player(reel['url'], ghost(reel['label'], PLAY), 'Play demo reel', autoplay=True)
    body = f'''<div class="wrap">
  <section class="reel" aria-label="Demo reel">{reel_html}</section>
  <div class="work-head"><h1>{e(SITE["tagline"])}</h1></div>
  <div class="grid">{"".join(tile(p, base) for p in PROJECTS)}</div>
</div>'''
    og = next((A(p).get('poster') for p in PROJECTS if A(p).get('poster')), '')
    write('index.html', page(f'{SITE["name"]} · Motion Designer', body, base,
                             f'{SITE["name"]} is a motion designer based in Los Angeles. Selected work for Electronic Arts, FX, Netflix, WhatsApp and more.', og, '', 'work'))


def build_project(i, p):
    base = '../../'
    a = A(p)
    sub = ' · '.join(x for x in [p.get('subtitle'), p.get('type'), p.get('client')] if x)
    paras = [x for x in re.split(r'\n\n+', p.get('description') or '') if x.strip()]
    credits = [['Client', p.get('client')]] + [c for c in p.get('credits', [])]
    credits = [c for c in credits if c[1]]
    # hero
    if a.get('heroVideo'):
        hero = mframe(vid(a['heroVideo'], a.get('heroPoster'), base), '', '', a.get('heroRatio', ''))
    elif a.get('tile'):
        hero = mframe(vid(a['tile'], a.get('poster'), base))
    elif a.get('hero') or a.get('still'):
        hero = mframe(img(a.get('hero') or a['still'], base, lazy=False, alt=p['title']))
    else:
        hero = ''
    # main video
    pv = a.get('hero') or a.get('still') or a.get('poster') or a.get('heroPoster')
    pframe = mframe(img(pv, base, alt=''), PLAY) if pv else ghost(p['title'], PLAY)
    main_video = player(p['video'], pframe, f'Play {p["title"]}') if p.get('video') else ''
    # gallery
    def item(g):
        cls = 'sq' if g.get('sq') else ''
        r = g.get('ratio', '')
        if r:
            w, h = (float(x) for x in r.split('/'))
            if w / h < 1:
                cls = 'tall'
        inner = vid(g['src'], g.get('poster'), base) if g['type'] == 'video' else img(g['src'], base)
        return mframe(inner, '', cls, r)
    G = a.get('gallery', [])
    rows = []
    sq = [g for g in G if g.get('sq')]
    wide = [g for g in G if not g.get('sq')]
    if sq:
        rows.append('<div class="row4">' + ''.join(item(g) for g in sq) + '</div>')
    for k in range(0, len(wide), 2):
        rows.append(f'<div class="row2">{item(wide[k])}{item(wide[k + 1])}</div>' if k + 1 < len(wide) else item(wide[k]))
    gallery = f'<section class="gallery" aria-label="Gallery">{"".join(rows)}</section>' if rows else ''
    more = [PROJECTS[(i + k) % len(PROJECTS)] for k in range(1, 5)]
    body = f'''<div class="wrap">
  <div class="p-head">
    <h1>{e(p["title"])}</h1>
    {f'<div class="sub">{e(sub)}</div>' if sub else ''}
    {f'<div class="role">{e(p.get("role"))}</div>' if p.get('role') else ''}
  </div>
  <div class="p-body">
    {hero}
    {f'<section class="intro"><h2>Overview</h2><div class="txt">' + ''.join(f'<p>{e(t)}</p>' for t in paras) + '</div></section>' if paras else ''}
    {main_video}
    {gallery}
    {'<section class="credits"><h2>Credits</h2><dl>' + ''.join(f'<div style="display:contents"{" class=\"client-row\"" if k == "Client" else ""}><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in credits) + '</dl></section>' if credits else ''}
  </div>
  <section class="more">
    <div class="more-head"><h2>More work</h2><a href="{base}">All work →</a></div>
    <div class="grid4">{"".join(tile(m, base) for m in more)}</div>
  </section>
</div>'''
    desc = paras[0] if paras else f'{p["title"]} — {p.get("role", "")}'
    write(f'work/{p["slug"]}/index.html', page(f'{p["title"]} · {SITE["name"]}', body, base, desc[:300], a.get('poster') or a.get('heroPoster') or '', f'work/{p["slug"]}/'))


def build_about():
    base = '../'
    ab = SITE['about']
    def entries(L):
        out = '<ul class="cv">'
        for x in L:
            meta = ' · '.join(v for v in [x['dates'], x.get('location')] if v)
            out += (f'<li><div class="cv-h"><span class="org">{e(x["org"])}</span><span class="r">{e(meta)}</span></div>'
                    f'<div class="cv-t">{e(x["title"])}</div>' + (f'<p>{e(x["desc"])}</p>' if x.get('desc') else '') + '</li>')
        return out + '</ul>'
    rec = '<ul>' + ''.join(f'<li><span>{e(n)}</span><span class="r">{e(d)}</span></li>' for n, d in ab['recognition']) + '</ul>'
    gal = '<p class="sub-h">ArtCenter Student Gallery</p><ul>' + ''.join(f'<li><span>{e(g)}</span></li>' for g in ab['student_gallery']) + '</ul>'
    body = f'''<div class="wrap">
  <div class="p-head"><h1>About</h1><div class="sub">{e(SITE["title_line"])}</div></div>
  <div class="about">
    <section><h2>Experience</h2>{entries(ab["experience"])}</section>
    <section><h2>Education</h2>{entries(ab["education"])}</section>
    <section><h2>Recognition</h2><div class="stack">{rec}{gal}</div></section>
    <section><h2>Public Speaking</h2>{entries(ab["speaking"])}</section>
    <section><h2>Contact</h2><div class="txt"><p><a class="u" href="mailto:{e(SITE["email"])}">{e(SITE["email"])}</a></p></div></section>
  </div>
</div>'''
    write('about/index.html', page(f'About · {SITE["name"]}', body, base, f'{SITE["name"]}: motion designer based in Los Angeles. Experience, education and recognition.', '', 'about/', 'about'))


def build_extras():
    body = '<div class="wrap e404"><h1 style="margin:0;font-family:var(--display);text-transform:uppercase;letter-spacing:.12em">Page not found</h1><p><a class="u" href="/">Back to work →</a></p></div>'
    write('404.html', page(f'Not found · {SITE["name"]}', body, '/', ''))
    # old Webflow URLs -> new pages
    lines = ['/project/' + s + ' /work/' + s + '/ 301' for s in ORDER]
    lines += ['/project/' + s + ' / 301' for s in SITE.get('removed_slugs', [])]
    lines += ['/project/nier-automata-v01 /work/nier-automata/ 301', '/project/canoo-built-for-you-2 /work/canoo-built-for-you/ 301',
              '/contact /about/ 301', '/project/* / 301']
    seen, out = set(), []
    for l in lines:
        k = l.split()[0]
        if k not in seen:
            seen.add(k); out.append(l)
    write('_redirects', '\n'.join(out) + '\n')
    write('_headers', '/m/*\n  Cache-Control: public, max-age=31536000\n/assets/*\n  Cache-Control: public, max-age=3600\n')
    write('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {SITE["domain"]}/sitemap.xml\n')
    urls = [''] + ['about/'] + [f'work/{p["slug"]}/' for p in PROJECTS]
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{SITE["domain"]}/{u}</loc></url>\n' for u in urls) + '</urlset>\n')
    write('assets/favicon.svg', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#0b0c0e"/><text x="32" y="42" font-family="monospace" font-size="26" font-weight="700" fill="#eceef1" text-anchor="middle" letter-spacing="1">EH</text></svg>\n')


if __name__ == '__main__':
    # clear old generated pages (keep media + assets)
    import shutil
    if os.path.isdir(os.path.join(PUB, 'work')):
        shutil.rmtree(os.path.join(PUB, 'work'))
    build_home()
    for i, p in enumerate(PROJECTS):
        build_project(i, p)
    build_about()
    build_extras()
    print(f'built {len(PROJECTS)} project pages + home, about, 404')
