# Playtest Checklist

> Same questions every Friday. Trends matter more than any single answer.

**Build:** `playtest-YYYY-MM-DD` tag on `dev`.
**Length:** 5 min play + 5 min questions per tester.
**Recorder:** writes everything; no defending the design.

## Pre-flight (tech lead, before tester arrives)

- [ ] Latest `dev` builds clean with no warnings.
- [ ] Web build hosted at a fresh URL (itch.io / GitHub Pages / Render preview).
- [ ] Telemetry endpoint reachable (once it exists).
- [ ] Test on the laptop *and* a phone the tester doesn't own.

## During play (silent, just watch)

- [ ] Time from URL → first input.
- [ ] First moment they smiled / leaned in.
- [ ] First moment they sighed / leaned back.
- [ ] Did they discover the verb on their own? Y / N
- [ ] Did they reach the win condition? Y / N — in how long?
- [ ] Did they ask to play again unprompted? Y / N

## Questions (verbatim, in order)

1. In one sentence — what was this game about?
2. What was the best moment?
3. What was the most confusing moment?
4. Would you play this again right now? (Y / N — no maybe.)
5. If I could change one thing for next Friday, what should it be?
6. Out of 10, how excited are you about this build? Why that number?

## Post-test, same day

- [ ] Add three lines to `happy-accidents.md` (bugs, surprises, "ooh"s).
- [ ] File one issue per "play again = No".
- [ ] Update the Excitement score (median of question 6) in `RESULTS.md`.

## Don't

- Don't explain the controls. The build does or it doesn't.
- Don't apologise for missing features.
- Don't change anything mid-session, even if you see the fix.
