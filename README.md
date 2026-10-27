# ehyun.design

Portfolio site for Eugene Hyun, motion designer. Static HTML, served by Cloudflare Pages from `public/`.

## How it's built

| Path | What it is |
| --- | --- |
| `content/projects.json` | Project text: title, client, type, role, video link, description, credits |
| `content/media.json` | Project order and the media files for each project |
| `content/site.json` | Name, reel link, social links, About page, removed projects |
| `public/` | The live site (generated pages + `m/` media + `assets/`) |
| `build.py` | Regenerates every page in `public/` from `content/` |
| `tools/build_media.py` | Converts the `ehyun-site-assets` folder into web media and `content/media.json` |

After changing anything in `content/`, run `python3 build.py` and commit `public/` with it.

## Asset folder rules (`ehyun-site-assets`)

- One folder per project, `NN-slug`. The number sets the order on the site.
- `xxx-` at the start of a folder or file name removes it from the site.
- `tile.mp4` / `tile.gif` = moving grid tile; `tile.jpg` = still tile.
- `hero.mp4` = video at the top of the project page.
- `gallery-01…` = gallery items, in name order. Transparent PNGs are placed on black.

## Hosting

Cloudflare Pages, connected to this repository: build command empty, output directory `public`.
`public/_redirects` sends the old Webflow `/project/...` URLs to the new `/work/.../` pages.
