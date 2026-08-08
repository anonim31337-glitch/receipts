#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate.py — run a command and refuse to call it done without a receipt.

    0  done          command exited 0 AND the artifact passed every check
    1  rejected      command failed, or the artifact is missing/bad
    2  don't know    a check could not be evaluated — this is NOT approval

Exit code 0 from a build tool means "I did not crash". It does not mean
"the thing exists". This wrapper closes that gap.

    python gate.py --cmd "npm run build" --artifact dist/index.js --min-bytes 1000
    python gate.py --cmd "python export.py" --artifact out/d.json --json-keys rows
    python gate.py --cmd "make film" --artifact out/f.mp4 --newer-than 600
    python gate.py --artifact out/f.mp4 --min-bytes 1000000     # check only
"""
import argparse
import json
import os
import subprocess
import sys
import time

DONE, REJECTED, UNKNOWN = 0, 1, 2


def say(status, name, detail):
    mark = {"OK": "[OK]  ", "BAD": "[BAD] ", "?": "[?]   "}[status]
    print(f"  {mark} {name:<22} {detail}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cmd", help="command to run; omit to only check the artifact")
    p.add_argument("--artifact", required=True, help="path that must exist afterwards")
    p.add_argument("--min-bytes", type=int, default=1,
                   help="artifact must be at least this large (default: non-empty)")
    p.add_argument("--newer-than", type=float, metavar="SECONDS",
                   help="artifact must have been written within the last N seconds "
                        "— catches a stale file left by an earlier run")
    p.add_argument("--contains", help="artifact text must contain this string")
    p.add_argument("--json-keys", help="comma-separated keys that must be present and non-empty")
    p.add_argument("--shell", action="store_true", help="run --cmd through the shell")
    a = p.parse_args()

    verdict = DONE
    started = time.time()

    if a.cmd:
        r = subprocess.run(a.cmd, shell=a.shell or os.name == "nt")
        if r.returncode != 0:
            say("BAD", "exit code", f"{r.returncode} — command failed")
            print("\nREJECTED: the command itself failed.")
            return REJECTED
        say("OK", "exit code", "0")

    # --- the part everybody skips -------------------------------------------
    if not os.path.exists(a.artifact):
        say("BAD", "artifact", f"does not exist: {a.artifact}")
        print("\nREJECTED: exit code said yes, the disk says no.")
        return REJECTED

    size = os.path.getsize(a.artifact)
    if size < a.min_bytes:
        say("BAD", "size", f"{size} B < required {a.min_bytes} B")
        verdict = REJECTED
    else:
        say("OK", "size", f"{size} B")

    if a.newer_than is not None:
        age = started - os.path.getmtime(a.artifact)
        if age > a.newer_than:
            say("BAD", "freshness", f"written {age:.0f} s ago — older than this run")
            verdict = REJECTED
        else:
            say("OK", "freshness", f"written {max(age, 0):.0f} s ago")

    if a.contains or a.json_keys:
        try:
            text = open(a.artifact, encoding="utf-8", errors="replace").read()
        except OSError as e:
            say("?", "readable", f"cannot read: {e}")
            return UNKNOWN

        if a.contains:
            if a.contains in text:
                say("OK", "contains", f"found {a.contains!r}")
            else:
                say("BAD", "contains", f"missing {a.contains!r}")
                verdict = REJECTED

        if a.json_keys:
            try:
                d = json.loads(text)
            except json.JSONDecodeError as e:
                say("BAD", "json", f"does not parse: {e}")
                return REJECTED
            for k in [x.strip() for x in a.json_keys.split(",") if x.strip()]:
                v = d.get(k) if isinstance(d, dict) else None
                if v in (None, "", [], {}, 0):
                    say("BAD", f"json[{k}]", "missing or empty")
                    verdict = REJECTED
                else:
                    n = len(v) if isinstance(v, (list, dict, str)) else v
                    say("OK", f"json[{k}]", f"present ({n})")

    print()
    print({DONE: "DONE — command succeeded and the artifact backs it up.",
           REJECTED: "REJECTED — do not report this step as finished.",
           UNKNOWN: "DON'T KNOW — this is not approval. Fix the check."}[verdict])
    return verdict


if __name__ == "__main__":
    sys.exit(main())
