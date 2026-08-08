# receipts

**A step is not done because the command exited 0. It is done when the
artifact exists and passes a check.**

A Claude Code plugin with two skills and two scripts. It exists because of
one number:

> A pipeline reported **169 successes out of 169 steps** and left
> **zero files on disk.** Every exit code was 0.

And a second one:

> **Fifteen green gates passed a broken film.** Every intermediate step was
> verified. Nothing verified the finished file.

## Install

```
/plugin marketplace add anonim31337-glitch/receipts
/plugin install receipts
```

Or point Claude Code at the repository directly with **Add plugin → Add from
repository**.

## What you get

| Skill | Fires when | What it does |
|---|---|---|
| `receipts` | you are about to report something as done | forces every claimed step to name a command, an artifact, and a check that a *plausible failure* would trip |
| `video-receipts` | before publishing or exporting a rendered video | checks the finished file the way a viewer experiences it |

And one command, for when you want the discipline on demand rather than by
habit:

```
/receipts:verify the migration script I just ran
```

It makes the agent name the artifact, check it with a predicate a plausible
failure would trip, and say **"I don't know"** instead of "OK" when a check
cannot run.

Two scripts you can also run standalone, with no agent involved:

```bash
# any build step
python scripts/gate.py --cmd "npm run build" --artifact dist/index.js --min-bytes 1000
python scripts/gate.py --cmd "python export.py" --artifact out/d.json --json-keys rows,total

# a finished video
python scripts/video_gate.py out/film.mp4
python scripts/video_gate.py out/film.mp4 --expect-seconds 308
```

Exit codes are the same everywhere: `0` done, `1` rejected,
`2` **don't know — which is not approval**.

## The one idea

Every gate that has ever broken in practice broke toward "OK". Nobody
notices a gate that wrongly passes; everybody notices one that wrongly
fails. So the design is biased against itself:

- A missing tool, report, or credential produces **"I don't know"**, never a
  pass. Absence of evidence is not evidence of success.
- Test every threshold against a **known failure**, not only a known
  success. A gate you have only ever watched pass is not a gate.
- Prefer a check a *plausible failure* would trip. "The file exists" passes
  for empty files, truncated downloads, and black frames.

Both scripts in this repo are tested both ways — they pass a known-good
input and reject a known-bad one. That is the minimum bar for shipping a
gate, and it is not a high one.

## Where this came from

[Laufer 108](https://www.youtube.com/@Laufer108) — a Polish YouTube channel
where an agent builds the channel on camera. These gates are not a demo;
they are what stands between a render and the publish button, and each one
is a defect that shipped before it existed.

Episode that produced this repo:
<https://youtu.be/PcXVv4hLRqA>

## Licence

MIT. Take it. If it saves you one evening, that was the point.
