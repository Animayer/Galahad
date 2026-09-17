# Galahad Discord emoji pack

Upload-ready **animated GIFs** for Ryan Mayer’s Galahad (original IP).

These are **new bust / head+crest / shield-Mark close-ups**, authored at 64×64 and nearest-neighbor scaled to **128×128**. They are **not** rescaled `walk2` / run / reaction full-body sheets — those stay too small at Discord emoji size.

Preview: [https://animayer.github.io/Galahad/assets/discord-emojis/](https://animayer.github.io/Galahad/assets/discord-emojis/)

## Background (pack-wide)

**Opaque dark navy `#0b1220`.** Same night-watch fill as the other Galahad GIF packs. GIF only has 1-bit transparency, which fringes pixel edges, so every frame is composited onto navy before palettizing. Do not mix transparent and navy files in this folder.

## Discord constraints

| Rule | This pack |
|---|---|
| Format | GIF |
| Canvas | 128×128 square |
| File size | Discord cap **256 KB**; target ≪ 150 KB (these land ~7–17 KB) |
| Scale | Nearest-neighbor only — no blurry upscale |
| Loop | Infinite (`loop=0`) except `galahad_shocked.gif` (play once, `loop=1`) |

Animated emojis require a boosted server to *upload*, and Nitro to *use* everywhere. Static PNG fallbacks are not in this pack.

## Upload steps

1. Open the Discord server → **Server Settings → Emoji**.
2. Under **Animated Emoji**, **Upload Emoji** (or drag the `.gif` in).
3. Name each file to match the shortcode **without** colons (Discord adds those). Suggested names below.
4. Confirm each tile is square, animates in the picker, and is listed under the 256 KB cap.

Do not upload the PNGs in `frames/` — those are rebuild sources.

## Files

Source animation PNGs: [`frames/<name>/`](frames/). Rebuild:

```bash
python3 -m pip install Pillow
python3 scripts/make-discord-emojis.py --author   # redraw PNGs, then GIFs
python3 scripts/make-discord-emojis.py            # GIFs from committed PNGs only
```

Pillow may coalesce consecutive identical hold frames when writing the GIF; the PNG folders are the source of truth for pose counts.

| GIF | Beat | Shortcode | Loop |
|---|---|---|---|
| `galahad_wave.gif` | Open palm by the crest | `:galahad_wave:` | yes |
| `galahad_nod.gif` | Approving nod | `:galahad_nod:` | yes |
| `galahad_shake.gif` | Head shake “no” | `:galahad_shake:` | yes |
| `galahad_shrug.gif` | “Not my cohort” | `:galahad_shrug:` | yes |
| `galahad_salute.gif` | Spear + gauntlet to brow | `:galahad_salute:` | yes |
| `galahad_hold.gif` | Shield brace. “Hold.” | `:galahad_hold:` | yes |
| `galahad_victory.gif` | Crest + spear; the line held | `:galahad_victory:` | yes |
| `galahad_facepalm.gif` | Helm visor facepalm | `:galahad_facepalm:` | yes |
| `galahad_think.gif` | Head tilt, gauntlet on beard | `:galahad_think:` | yes |
| `galahad_shocked.gif` | Recoil + **one magenta eye** | `:galahad_shocked:` | once |
| `galahad_laugh.gif` | Dry chuckle (closed eyes) | `:galahad_laugh:` | yes |
| `galahad_mark.gif` | Shield emblem pulse | `:galahad_mark:` | yes |

Magenta visor glow is **only** on `galahad_shocked` (portrait oath/curse state). The Mark pulse stays teal/steel.

## Visual lock

- Teal / blue-grey lorica + pauldrons, tall **red crest**, red cape accents
- Beard, open galea, three-prong Mark on shield and pauldron
- Battle-worn (scratches, blood specks) — not a shiny holy knight
- Original pixels; no ripped Discord/Twitch emotes
