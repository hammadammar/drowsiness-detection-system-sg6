# SG6 test results

Latest local suite: 97 tests, 97 passed, 0 failures, 0 errors, 0 skipped. Evidence `evaluation/sg6_release_tests.xml`. Command: `python -m pytest -q --basetemp=.pytest-tmp/release-run --junitxml=evaluation/sg6_release_tests.xml` (create .pytest-tmp parent first on Windows). Standard Jetson command: `bash test_jetson.sh`. SG2/SG3/SG4 original tests preserved; SG6 tests under tests/.

VERIFIED ON RECORDED INPUT: all 600 committed real SG1 landmark records through adapters, SG2 schema, SG3 unknown mouth handling, SG4 and SG5, with timestamps/frame association. Original SG2 hand-labelled blink assertions pass if included in successful suite. Real recorded source timestamps may be fractional; accepted as required by existing schema. SG4 retains its integer truncation behavior.

VERIFIED USING MOCK DATA: valid/invalid points and types, empty/missing optional fields, duplicate timestamps, no face, face loss after closure without fabricated blink, sustained eye closure and recovery, SG3 full-landmark mouth -> temporal yawn count, SG5 rule/weighted threshold boundary and poor validity, cue alignment rejection, software alert cooldown. Original SG4 tests cover irregular/dropped samples, gaps, blink/yawn events, missing face and window expiry. These results verify logic, not detection accuracy in drivers.

VERIFIED ON RECORDED INPUT (generated blank fixture only): raw decoder + real SG1 model + 30 no-face observations + no confirmed drowsiness or alert; actual model initialization/cleanup. Fixture generation uses VideoWriter MJPG, 30 all-zero 320x240 frames at 10 FPS. It is intentionally not a labelled driver video. Missing-model test returns nonzero with clear path error before camera access; stored metrics in sg6_missing_model_metrics.json.

NOT TESTED: live USB camera capture, CSI, GUI, physical alarm, Jetson imports/model loading/performance, target power/thermal modes, sustained memory stability, real-driver raw video, complete system labelled accuracy/false-alert rate. No VERIFIED ON JETSON claims.

Historical failures retained: initial collection ran before dependency installation finished (missing jsonschema/mediapipe); an integration validator initially rejected fractional timestamps (fixed against schema); sandbox pytest temporary-directory failures were resolved by selecting a workspace temp directory and creating its parent. Earlier XML reports are historical, not final readiness evidence. Static SG3 API mismatch was repaired by restoring its documented unused mouth_roi argument; algorithm unchanged.
