---
description: Prove the last step actually happened — name the artifact, check it, and say "I don't know" when you cannot.
argument-hint: [what you just claimed to finish]
---

Do not answer from memory or from an exit code. Verify on disk.

For the work described as `$ARGUMENTS` (or, if empty, for the most recent
step you claimed to complete in this conversation):

1. **Name the artifact.** The exact path that must exist because that step
   ran. If you cannot name one, stop and say so — an unverifiable step
   cannot be reported as done.

2. **Check it with a predicate a plausible failure would trip.** Not "the
   file exists" — that passes for empty files, truncated downloads and black
   frames. Pick something the actual failure mode would break: byte size,
   parsed structure, expected key, duration, the string you published.

   Prefer running it rather than reasoning about it:

   ```
   python scripts/gate.py --artifact <path> --min-bytes <n> [--json-keys a,b] [--contains "..."]
   ```

   For a rendered video use the finished-file gate instead:

   ```
   python scripts/video_gate.py <path>
   ```

3. **Report the check, not the vibe.** Say what you measured.
   - Bad: "Build succeeded, looks good."
   - Good: "dist/index.js is 84 KB, written 3 s ago, exports `mount`."

4. **If a check could not run, say "I don't know" — never "OK".** A missing
   tool, a missing report, an unmounted drive: none of those are approval.
   Absence of evidence is not evidence of success.

5. **If the artifact is missing or bad, say the step is not done** and state
   what you will do about it. Do not soften it, do not move on, and do not
   let a later step depend on it.

Finally, if you set any threshold during this check, say whether you tested
it against a case you know should fail. A threshold you have only ever
watched pass is not a threshold.
