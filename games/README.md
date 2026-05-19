# EBBY Games

> Create the best gaming experience. Bring back excitement in gaming.
> Drive innovation. Redefine what's possible. Learn from the unexpected.

**Values:** one studio, many voices — start development.

## What's here

| Path | Purpose |
|------|---------|
| `ebby-title-01/` | Week-1 grey-box prototype (Godot 4, web target) |
| `../docs/games/` | GDD brief, core loop, playtest checklist, happy-accidents log |

## Branching

```
main           shippable / demo builds only
dev            integration; nightly playable build (this branch)
feature/*      one voice, one slice
prototype/*    short-lived experiments
```

- PRs into `dev` need: green CI, one-line changelog, who playtested.
- `dev` is sacred: only merge when the game **boots and the core loop runs**.
- Friday: tag `playtest-YYYY-MM-DD` from `dev`.

## Week-1 mission

Playable grey-box of the **core loop** by Friday. No art. Lots of tuning.
See [`docs/games/GDD-brief.md`](../docs/games/GDD-brief.md).
