# SG6 module inventory

All source references are frozen in `evaluation/sg6_source_refs.txt`. Readiness describes integration maturity; none is Jetson-verified.

## SG1 — PARTIAL

Source `origin/module_sg1` at `6b78a7242772bdce641eedaeb6a03e3650ba4615`, imported under `module_sg1/`. Entry `Sg1_Pipeline.py`: MediaPipe Tasks face landmarker, OpenCV, NumPy, pandas, optional YAML. Input BGR frame/result; output nested V1 record plus BGR ROI arrays. Boxes are x/y/width/height in full-frame pixels; six ordered points per eye; four mouth points; optional 478 full landmarks. Confidence is null because this API does not expose a detector score. Selected model `models/face_landmarker.task`; explicit versioned download and SHA256 provenance exist. SG6 wraps capture; original demo accepts video. No original SG1 tests. Actual model loaded and ran on 30 generated blank video frames locally. Faces/partial occlusions/real-camera geometry remain unverified. Head-pose signs are not validated. Multiple in-region candidates become unknown in the integrated app.

## SG2 — PARTIAL

Source `origin/module_sg2` at `b8dd288308b0d8e8515965ee70b93de736f7f93f`, merged with history. Entry `sg2_eye.EyeStateModule.process`: flat face block with frame_id/timestamp_ms, optional BGR frame for CNN; output sg2-v1 state, EAR, closure/blink evidence, heuristic confidence. Dependencies NumPy/OpenCV/PyYAML; optional ONNX Runtime. Primary G = adaptive EAR + CNN confirmation, backup C = adaptive EAR. CNN `module_sg2/models/eye_state_cnn_v2.onnx` is absent, so existing warned backup is active and recorded in output. Real 600-frame landmark sample and labelled blink tests exist, plus mock streams and schema tests. Calibration windows/warmup are frame-based; time-based closure is handled independently by SG4. SG6 cancels pending blink on missing face or elapsed gap > SG4 max_gap_ms. No CNN/Jetson verification.

## SG3 — PARTIAL

Source `origin/module_sg3` at `eccb03c43c4fc8450316e5e7a13e39fa084c029b`, imported under `module_sg3/`. Entry `sg3.SG3.process`, NumPy core, no learned weights. Consumes eight inner-mouth points, face validity and optional HeadPose; emits MouthOutput mouth_valid/yawn_prob/cue_flags. Existing tests preserved. SG6 restored unused optional mouth_roi for backward compatibility. Eight points come from actual optional SG1 full landmarks using SG3's own map; four points are never expanded. Missing full landmarks => mouth unknown. Pose cues intentionally unavailable until SG1/SG3 sign agreement. MAR sigmoid thresholds are starting assumptions, not calibrated yawn probabilities. Optional standalone upstream uses legacy MediaPipe solutions and needs compatibility review; canonical app uses SG1 Tasks instead.

## SG4 — PARTIAL

Source `origin/module_sg4` at `c5bd34dc15974e5f3e1028d6b3a426939eeb9e22`, imported under `module_sg4/`. Entry `sg4.TemporalAnalyzer.update`. Standard-library core, pytest tests and optional plotting/YAML. Flat/nested per-frame cues -> window validity, PERCLOS, blink rate/duration, current/longest closure, yawn count. No weights. Recorded JSONL/replay/mock generation tools and tests exist. Bounded sliding time windows; gaps capped; duplicate/decreasing timestamps rejected. Defaults explicitly unvalidated placeholders; yawn smoothing uses samples and head cues are unused. Existing integer timestamp conversion truncates fractional milliseconds (<1 ms difference); SG2/SG3 retain source timestamp. No target measurements.

## SG5 — PARTIAL

Named `module_sg5` branch is scaffold only. Actual code from `origin/alveenashahidd-patch-1-1` at `4cc9a2531bff7e8f35bf23786b8c1ce8d748a326`. Extensionless `decision_rules`, `weighted_fusion`, `compare_methods`, `mock_inputs` preserved; byte-identical importable .py copies created for algorithms. Entries make_decision/weighted_decision, standard library, no weights. SG4 dict -> NORMAL/WARNING/DROWSY, validity, heuristic score and alarm flag. Original mock examples, no original automated assertions. Added integration tests exercise thresholds and invalid windows. Rule method selected as baseline; weighted alternative configurable. Notebook on sg3-patch-3 has different threshold variants and is excluded pending owner approval. No calibrated confidence, hysteresis or physical actuator in source.

## SG6 — PARTIAL

Original `embedded_sg6` branch equals main scaffolding. New canonical entry `python -m embedded_sg6.app`, with config, headless observation/video/camera/CSI input selection, single capture owner, shared frame, adapters, schema validation, output streaming, CPU/RSS and stage timing, cleanup, cooldown software alerts, model acquisition, read-only audit, experiment and packaging infrastructure. No replacement subgroup algorithm. Camera, GUI, CSI, GPU acceleration, physical alerts and Jetson sustained operation NOT TESTED. No test driver video or complete system ground truth is bundled.
