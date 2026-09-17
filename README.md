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

Preview GIFs of those same canon clips live in [`assets/gifs/`](assets/gifs/) (idle / walk 4-dir, attack, hurt, death, corpse). Dark navy background, timings from `animations.json`. Rebuild with:

```bash
python3 scripts/make-gifs.py
```
