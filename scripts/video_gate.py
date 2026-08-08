#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""video_gate.py — check a FINISHED video the way a viewer would experience it.

Every check here comes from a defect that shipped. None are hypothetical.

    0  ship it        1  rejected        2  don't know (not approval)

    python video_gate.py film.mp4
    python video_gate.py film.mp4 --expect-seconds 308 --tolerance 2

Requires ffmpeg and ffprobe on PATH (or --ffmpeg / --ffprobe).
"""
import argparse
import json
import re
import subprocess
import sys

DONE, REJECTED, UNKNOWN = 0, 1, 2
rows = []


def add(status, name, detail, fix=""):
    rows.append((status, name, detail, fix))


def run(args):
    return subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def probe(ffprobe, path, stream):
    r = run([ffprobe, "-v", "error", "-select_streams", stream,
             "-show_entries", "stream=duration,r_frame_rate,avg_frame_rate,"
             "sample_rate,width,height", "-show_entries", "format=duration",
             "-of", "json", path])
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def frac(s):
    try:
        a, b = s.split("/")
        return float(a) / float(b) if float(b) else None
    except (ValueError, AttributeError):
        return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("film")
    p.add_argument("--ffmpeg", default="ffmpeg")
    p.add_argument("--ffprobe", default="ffprobe")
    p.add_argument("--expect-seconds", type=float)
    p.add_argument("--tolerance", type=float, default=2.0)
    p.add_argument("--freeze-seconds", type=float, default=2.0,
                   help="a still frame longer than this counts as a defect")
    a = p.parse_args()

    v = probe(a.ffprobe, a.film, "v:0")
    au = probe(a.ffprobe, a.film, "a:0")
    if not v or not v.get("streams"):
        print("[?] cannot read the video stream — is ffprobe on PATH?")
        return UNKNOWN

    vs = v["streams"][0]
    dv = float(vs.get("duration") or v["format"]["duration"])
    da = float(au["streams"][0]["duration"]) if au and au.get("streams") else None
    dk = float(v["format"]["duration"])

    # 1. IMAGE vs SOUND. Shipped defect: 289 s of image under 528 s of audio.
    if da is None:
        add("?", "audio track", "no audio stream found")
    else:
        d = abs(dv - da)
        add("OK" if d <= 1.5 else "BAD", "image vs sound",
            f"image {dv:.1f}s, sound {da:.1f}s, gap {d:.2f}s",
            "the montage lost or gained shots — do not fix by trimming audio")

    # 2. HEADER vs CONTENT — a container that lies about its own length.
    add("OK" if abs(dk - dv) <= 1.5 else "BAD", "header vs content",
        f"header says {dk:.1f}s, video is {dv:.1f}s")

    # 3. CONSTANT FRAME RATE. Shipped defect: concat with `-c:v copy` produced
    #    r_frame_rate 375/1; a duration check then read 49 s instead of 737 s.
    rf, af = frac(vs.get("r_frame_rate")), frac(vs.get("avg_frame_rate"))
    if rf is None or af is None:
        add("?", "frame rate", "cannot read frame rate")
    else:
        add("OK" if abs(rf - af) <= 0.75 else "BAD", "frame rate",
            f"r_frame_rate {rf:.2f}, avg_frame_rate {af:.2f}",
            "not CFR — re-encode the video on concat instead of -c:v copy")

    # 4. FROZEN PICTURE. Careful: a freeze often means the frame is EMPTY,
    #    not that the shot is slow. Pull the frame and look before "adding motion".
    r = run([a.ffmpeg, "-i", a.film, "-vf",
             f"freezedetect=n=0.001:d={a.freeze_seconds}", "-f", "null", "-"])
    fr = re.findall(r"freeze_start: ([\d.]+)", r.stderr or "")
    add("OK" if not fr else "BAD", "frozen picture",
        "none" if not fr else f"{len(fr)} at " + ", ".join(f"{float(x):.0f}s" for x in fr[:6]),
        "extract that exact frame and LOOK at it — a freeze is usually an empty frame")

    # 5. BLACK FRAMES.
    r = run([a.ffmpeg, "-i", a.film, "-vf", "blackdetect=d=0.5:pix_th=0.02",
             "-f", "null", "-"])
    bl = re.findall(r"black_start:([\d.]+)", r.stderr or "")
    add("OK" if not bl else "BAD", "black frames",
        "none" if not bl else f"{len(bl)} at " + ", ".join(f"{float(x):.0f}s" for x in bl[:6]))

    # 6. LOUDNESS AND CLIPPING.
    if da is not None:
        r = run([a.ffmpeg, "-i", a.film, "-af", "volumedetect", "-f", "null", "-"])
        mx = re.search(r"max_volume: (-?[\d.]+) dB", r.stderr or "")
        mn = re.search(r"mean_volume: (-?[\d.]+) dB", r.stderr or "")
        if mx and mn:
            peak, mean = float(mx.group(1)), float(mn.group(1))
            add("OK" if peak <= -1.0 else "BAD", "clipping",
                f"peak {peak:.1f} dB, mean {mean:.1f} dB",
                "peak above -1 dB will distort after platform transcoding")
            add("OK" if mean > -35 else "BAD", "not silent",
                f"mean {mean:.1f} dB")
        else:
            add("?", "loudness", "volumedetect returned nothing")

    # 7. LENGTH AGAINST INTENT — only if the caller states the intent.
    if a.expect_seconds:
        d = abs(dv - a.expect_seconds)
        add("OK" if d <= a.tolerance else "BAD", "expected length",
            f"{dv:.1f}s vs expected {a.expect_seconds:.1f}s (gap {d:.1f}s)")

    print(f"\n=== FINISHED VIDEO ===\n  {a.film}  {vs.get('width')}x{vs.get('height')}\n")
    for st, n, d, fix in rows:
        mark = {"OK": "[OK]  ", "BAD": "[BAD] ", "?": "[?]   "}[st]
        print(f"  {mark}{n:<18} {d}")
        if st == "BAD" and fix:
            print(f"         -> {fix}")

    bad = [r for r in rows if r[0] == "BAD"]
    unk = [r for r in rows if r[0] == "?"]
    print()
    if bad:
        print(f"REJECTED — {len(bad)} defect(s) a viewer would notice.")
        return REJECTED
    if unk:
        print(f"DON'T KNOW — {len(unk)} check(s) could not run. This is NOT approval.")
        return UNKNOWN
    print("SHIP IT — every check passed on the finished file.")
    return DONE


if __name__ == "__main__":
    sys.exit(main())
