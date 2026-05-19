# ebby-title-01 — week-1 grey-box

Godot 4 prototype. **One screen, one verb, one win condition.**

| | |
|---|---|
| Engine | Godot 4.3+ |
| Target | Web (HTML5) first, desktop second |
| Verb | Click the target |
| Win | 10 hits |
| Loop | Spawn → aim → hit → reward → repeat |

## Run locally

1. Install [Godot 4.3](https://godotengine.org/download).
2. Open `project.godot` in the editor.
3. Press <kbd>F5</kbd>.

## Headless import (matches CI)

```bash
godot --headless --import
```

## Export to web

In the editor: **Project → Export → HTML5 → Export Project**.
Output goes to `build/web/` (gitignored).

## What to change first

- `scripts/main.gd` — tune `win_score`, target size, spawn placement.
- `scenes/main.tscn` — swap the target `ColorRect` for any test art.

Keep diffs small. One PR = one tweak you can describe in a sentence.
