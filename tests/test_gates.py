#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-tests for the gates. Every case is asserted BOTH ways.

A gate you have only ever watched pass is not a gate — so each check here
is proven against an input that must be accepted AND one that must be
rejected. If only the happy path were tested, this file would be theatre.

    python tests/test_gates.py
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "..", "scripts", "gate.py")
DONE, REJECTED, UNKNOWN = 0, 1, 2
wyniki = []


def uruchom(*args):
    r = subprocess.run([sys.executable, GATE, *args],
                       capture_output=True, text=True)
    return r.returncode


def sprawdz(nazwa, oczekiwany, faktyczny):
    ok = oczekiwany == faktyczny
    wyniki.append(ok)
    nazwy = {DONE: "done", REJECTED: "rejected", UNKNOWN: "don't know"}
    print(f"  {'PASS' if ok else 'FAIL'}  {nazwa:<52} "
          f"expected {nazwy[oczekiwany]}, got {nazwy.get(faktyczny, faktyczny)}")


def main():
    with tempfile.TemporaryDirectory() as d:
        brak = os.path.join(d, "never_created.txt")
        pusty = os.path.join(d, "empty.txt")
        maly = os.path.join(d, "small.json")
        dobry = os.path.join(d, "good.json")
        open(pusty, "w").close()
        open(maly, "w").write("{}")
        open(dobry, "w").write('{"rows": [1, 2, 3], "total": 3}')

        print("\n=== gate.py ===")

        # The whole point: a command can succeed and produce nothing.
        sprawdz("command exits 0 but the artifact is missing",
                REJECTED, uruchom("--cmd", "python -c pass", "--artifact", brak))
        sprawdz("command exits 0 and the artifact is there",
                DONE, uruchom("--cmd", "python -c pass", "--artifact", dobry))

        # A failing command must never be rescued by an artifact lying around.
        sprawdz("command fails even though the artifact exists",
                REJECTED, uruchom("--cmd", "python -c \"import sys; sys.exit(3)\"",
                                  "--artifact", dobry))

        # "It exists" is the weakest check there is.
        sprawdz("artifact exists but is empty", REJECTED,
                uruchom("--artifact", pusty, "--min-bytes", "100"))
        sprawdz("artifact exists and is large enough", DONE,
                uruchom("--artifact", dobry, "--min-bytes", "10"))

        # Structure, not just bytes.
        sprawdz("json parses but the required key is missing", REJECTED,
                uruchom("--artifact", maly, "--json-keys", "rows"))
        sprawdz("json has the required keys", DONE,
                uruchom("--artifact", dobry, "--json-keys", "rows,total"))
        sprawdz("json key present but empty", REJECTED,
                uruchom("--artifact", maly, "--json-keys", "rows,total"))

        # Content, not just shape.
        sprawdz("artifact does not contain the expected string", REJECTED,
                uruchom("--artifact", dobry, "--contains", "not-in-there"))
        sprawdz("artifact contains the expected string", DONE,
                uruchom("--artifact", dobry, "--contains", "total"))

        # A stale file from an earlier run must not count as this run's work.
        os.utime(dobry, (0, 0))
        sprawdz("artifact is older than this run", REJECTED,
                uruchom("--artifact", dobry, "--newer-than", "60"))

    zdane = sum(wyniki)
    print(f"\n{zdane}/{len(wyniki)} passed")
    if zdane != len(wyniki):
        print("FAILED — a gate that does not reject is not a gate.")
        return 1
    print("Every case proven both ways.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
