# GitHub handoff — 2026-10-28

The user requested publication to their own account after the local integration work.
Destination: https://github.com/hammadammar/drowsiness-detection-system-sg6 (private).
Original upstream: https://github.com/Hassanahmed-15/drowsiness-detection-system .

`integration/jetson-sg6` contains the integrated application and is the destination repository's default branch. `source/*` branches preserve the original fetched subgroup/patch/main heads. Existing upstream tags are preserved. Algorithm authorship and commit history are retained. The original upstream and original desktop checkout are unchanged.

Earlier audit reports describe the original GitHub connector's read-only access. Subsequent Git Credential Manager sign-in as hammadammar authorized creation and publication of this separate repository; those historical reports are not current destination permission statements.

Start with START_HERE_JETSON.md. The release assets contain the committed-source ZIP and its SHA256 manifest, plus a Git history bundle. Windows virtual environments and model binaries are excluded. Model download remains explicit. Local evidence remains 97 passing release tests, recorded landmark replay and generated no-face raw-model smoke testing; no Jetson or live-camera verification has been added by publishing.
