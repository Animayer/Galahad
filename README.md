# Hold the Line

v0.1 browser arena for **Galahad** — Ryan Mayer original IP.

> Hold the line. If the line holds, we argue later.

Survive 45 seconds or put 15 raiders down. Galahad uses the canon Roman legionary pack (`idle` / `walk` 4-dir + `attack`). No accounts, no backend.

## Play locally

Serve the repo root (required so `animations.json` and the frames can load):

```bash
python3 -m http.server 8080
```

Open [http://localhost:8080](http://localhost:8080).

Any static server works (`npx serve`, `php -S localhost:8080`). Opening `index.html` as a `file://` URL will fail the pack fetch.

## Controls

| Input | Action |
|---|---|
| WASD or arrow keys | Move (4 directions, no mirrored side frames) |
| Space, click, or tap | Strike |
| On-screen pad (narrow viewports) | Move + Strike |

## GitHub Pages

This is a static root site (`index.html` + `css/` + `js/` + `assets/`). A `.nojekyll` file is included so GitHub does not run Jekyll.

1. Merge this branch to `main`.
2. Repo **Settings → Pages**.
3. **Build and deployment → Source:** Deploy from a branch.
4. Branch `main`, folder `/(root)`, then **Save**.

The project URL will be:

`https://<user-or-org>.github.io/Galahad/`

Optional: switch Source to **GitHub Actions** and use `.github/workflows/pages.yml` (same files, no build step).

Asset paths are relative, so the game works at the repo root or under that `/Galahad/` project path.

## Pack

Canon sprites live in `assets/roman_legionary/`:

- `frames_96/` — recommended 96px-tall frames
- `animations.json` — frame lists, timings, loop flags, bottom-center anchor

Do not flip left/right walk frames. Shield and spear stay in their drawn hands.

## GIF pack

Preview GIFs of canon and expanded clips live in [`assets/gifs/`](assets/gifs/) (idle / 4-frame walk, **8-frame walk2**, **run 4-dir**, block, thrust, cast, jump, …). Dark navy background. Rebuild with:

```bash
python3 scripts/make-gifs.py
```

`make-gifs.py` merges `animations.json` with [`assets/roman_legionary/animations_expanded.json`](assets/roman_legionary/animations_expanded.json). Existing `walk_*` names stay 4 frames so Hold the Line v0.1 is unchanged.

## Expanded sprite vocabulary

New poses (transparent 103×96 PNGs, same canvas as `frames_96/`):

| Clip | Frames | Loop | Notes |
|---|---|---|---|
| `walk2_*` (4-dir) | 8 | yes | Canon walk + authored in-betweens; 90 ms |
| `run_*` (4-dir) | 6 | yes | Dash / bob; left and right are distinct drawings |
| `turn` | 4 | yes | Pivot via canon idles (front→right→back→left) |
| `block` | 4 | no | Shield up |
| `thrust` | 5 | no | Front jab; not `attack_21–24` |
| `cast` | 4 | no | Magenta visor / Mark glow |
| `kneel` | 4 | no | Low brace |
| `wave` | 6 | yes | Beckon |
| `jump` | 5 | no | Crouch, tucked air, land |
| `cheer` | 5 | yes | Hop + spear present-arms |

Author PNGs and 128×128 showcase loops:

```bash
python3 scripts/make-expanded-gifs.py --author
```

PNG choice: **transparent** in `frames_96/` (and copies in `assets/sprites/expanded/`). GIFs composite onto opaque navy `#0b1220`. Do not flip side cycles.

## Reaction GIF pack

Meme-style **reaction loops** (nod, shrug, facepalm, salute, walk-off, “Hold.”, …) live in [`assets/gifs/reactions/`](assets/gifs/reactions/). Original Galahad poses composited from the legionary pack — not traced from other GIFs. Navy `#0b1220`, 128×128, Discord/X-small.

```bash
python3 scripts/make-reaction-gifs.py --author
```
