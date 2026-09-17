# Expanded Galahad frames

Copies of the **new** transparent 103×96 poses also written to
`assets/roman_legionary/frames_96/`. Canon idle/walk/attack names are
not duplicated here.

- Background: **transparent** (GIFs composite onto `#0b1220`)
- Anchor: bottom-center, same as the legionary pack
- Do not flip `*_left` / `*_right`

Rebuild:

```bash
python3 scripts/make-expanded-gifs.py --author
```

Spec: [`../../roman_legionary/animations_expanded.json`](../../roman_legionary/animations_expanded.json)
