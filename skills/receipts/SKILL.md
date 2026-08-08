---
name: receipts
description: Use when a task claims to be finished, when running any multi-step build or pipeline, or when you are about to report success. Turns "the command exited 0" into "the artifact exists and passes a check". Triggers on "done", "finished", "it worked", "all tests pass", "build succeeded", "verify", "gate", "pipeline", "check the output".
---

# Receipts

A step is not done because the command exited 0. **A step is done when the
artifact exists and passes a check.**

This skill exists because of a real number: a pipeline once reported
**169 successes out of 169 steps and left zero files on disk.** Every exit
code was 0. Every step was a lie.

## The rule

For every step you claim to have completed, name three things:

1. **Command** — what ran.
2. **Artifact** — the exact path that must exist afterwards.
3. **Check** — a predicate on that artifact that would FAIL if the work
   were bad, not merely absent.

If you cannot name the artifact, the step is not verifiable and you may not
report it as done. Say "I ran X, I cannot verify the result" instead.

## Why the third item matters

"File exists" is the weakest possible check and it passes for empty files,
truncated downloads, and 4 KB black frames. Pick a check that a *plausible
failure* would trip:

| Weak | Strong |
|---|---|
| the mp4 exists | the mp4 is 5:07 long and its audio track is not silent |
| the JSON was written | the JSON parses and has 39 entries, not 0 |
| the archive was created | the correct password opens it AND a wrong one is rejected |
| the page returned 200 | the page contains the string we published |

Test every threshold against a **known failure**, not only against a known
success. A gate you have only ever seen pass is not a gate.

## Gates lie in one direction

Every gate that has ever broken in practice broke toward "OK". Nobody
notices a gate that wrongly passes; everybody notices one that wrongly
fails. So bias your design against yourself:

- Missing tool, missing report, missing credentials → **"I don't know"**,
  exit code 2. Never treat absence of evidence as approval.
- "I don't know" must be visibly different from "OK" in the output, and it
  must block the same as a failure when the next step is irreversible.

## Using the runner

`scripts/gate.py` runs a command and refuses to call it a success unless
the artifact check also passes.

```
python scripts/gate.py --cmd "npm run build" --artifact dist/index.js --min-bytes 1000
python scripts/gate.py --cmd "python export.py" --artifact out/data.json --json-keys rows,total
python scripts/gate.py --cmd "make video" --artifact out/film.mp4 --min-bytes 1000000 --newer-than 300
```

Exit codes: `0` done · `1` rejected · `2` don't know.

Never paper over a 2. Fix the missing check or say plainly that the step is
unverified.

## When reporting to a human

State the check, not the vibe.

- Bad: "Build succeeded, everything looks good."
- Good: "dist/index.js is 84 KB, written 3 s ago, exports `mount`."

If a step was skipped, say it was skipped. If a threshold was not tested
against a failure, say that too. A report that hides a gap is worse than
no report, because it teaches the reader to trust the next one.
