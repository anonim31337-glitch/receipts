---
name: video-receipts
description: Use before publishing, exporting, or handing over any rendered video, and whenever a render "succeeded" but nobody watched the result. Checks the finished file the way a viewer experiences it — desync, frozen or black frames, variable frame rate, clipping, silence. Triggers on "render", "export", "ffmpeg", "publish the video", "upload", "the video is ready", "remotion", "final cut".
---

# Video receipts

Fifteen green gates once passed a broken film. Every intermediate step was
checked. **Nothing checked the finished file.** That is the whole idea here:
measure the product, not the parts.

## Run it

```
python scripts/video_gate.py out/film.mp4
python scripts/video_gate.py out/film.mp4 --expect-seconds 308 --tolerance 2
```

`0` ship it · `1` rejected · `2` don't know — and **2 is not approval**.

## What it checks, and the defect each one comes from

| Check | The defect that created it |
|---|---|
| image vs sound | 289 s of picture under 528 s of audio; the montage silently dropped shots |
| header vs content | container advertised a length its content did not have |
| constant frame rate | `concat` with `-c:v copy` produced `r_frame_rate 375/1`; a duration check then read 49 s instead of 737 s |
| frozen picture | a shot stretched past the end of its source; `tpad` cloned the last frame for 30 s |
| black frames | a whole scene rendered black at 4 MB — the file was big, the picture was not there |
| clipping | a peak above −1 dB distorts after the platform re-encodes |
| not silent | a film shipped with no audio at all and every step reported success |

## Three lessons that cost the most time

**1. A freeze usually means the frame is EMPTY, not that the shot is slow.**
Seven reported freezes were traced to a camera move that walked the crop
onto the composition's blank margin. Three rebuilds went the wrong way
because the diagnosis was "too slow". Pulling one frame and looking at it
settled it in a minute.

```
ffmpeg -ss 190.92 -i film.mp4 -frames:v 1 frame.jpg     # then OPEN it
```

**2. Scaling up before cropping eats text at the edge.** A 1.10 upscale
turned `AbsoluteFill` into `teFill`. Pad first with the background colour,
then crop inside that padding — nothing is lost and the frame still moves.

**3. `zoompan` drops frames.** It shortened a finished film by 69 seconds.
A pan expressed as a `crop x=` expression does not touch the frame count.

## Before you report success

Sample frames across the whole film and look at the smallest ones. An empty
1080p frame compresses to roughly 10–15 KB; a real one is far larger.

```
for t in 5 60 120 180 240 300; do ffmpeg -ss $t -i film.mp4 -frames:v 1 -q:v 3 f_$t.jpg; done
```

If you have not looked at a single frame, you have not checked the video.
