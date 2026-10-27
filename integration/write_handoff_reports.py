"""Generate evidence-linked SG6 handoff reports from this checkout's results."""
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT/'documentation'

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

def write(name, text):
    (DOC/name).write_text(text.strip()+'\n',encoding='utf-8')

def main():
    refs = git('for-each-ref','--format=%(refname:short) %(objectname)','refs/remotes')
    (ROOT/'evaluation/sg6_source_refs.txt').write_text(refs+'\n')
    env = json.loads((ROOT/'evaluation/sg6_environment.json').read_text())
    exp = json.loads((ROOT/'evaluation/sg6_validation_experiment.json').read_text())
    raw = json.loads((ROOT/'evaluation/sg6_no_face_metrics.json').read_text())
    suite = ET.parse(ROOT/'evaluation/sg6_release_tests.xml').getroot().find('testsuite')
    count, failures, errors, skipped = (int(suite.get(n,0)) for n in ('tests','failures','errors','skipped'))
    passed = count-failures-errors-skipped
    write('SG6_ENVIRONMENT_AUDIT.md',f'''# SG6 environment audit

Audit date: 2026-10-28 (Asia/Karachi). Actual development host is Windows 11 Pro 10.0.26300, AMD64, Intel Core i5-10310U (8 logical processors), Intel UHD Graphics driver 31.0.101.2140. CIM reports 16,515,596 KiB visible RAM and 3,968,264 KiB free at the sampled instant. HP IR Camera and HP HD Camera enumerate OK; live acquisition was not exercised.

Python: {env['python']}. Development package/build and disk/memory evidence: `evaluation/sg6_environment.json`; exact installed versions: `evaluation/development-windows-lock.txt`. NumPy {env['packages']['numpy']}, OpenCV {env['packages']['cv2']}, MediaPipe {env['packages']['mediapipe']}. Both OpenCV distributions were pulled into the isolated Windows development environment; do not copy it to ARM64. Use JetPack/system OpenCV on target.

This is not a Jetson. Board model, JetPack/L4T, Ubuntu/kernel, Jetson CUDA/cuDNN/TensorRT, nvpmodel power mode, thermals, CSI, GPU utilization and target profiling are NOT TESTED. PyTorch, TensorRT and ONNX Runtime are absent in the development venv. OpenCV build text and utility discovery are stored in the JSON. A Windows performance-counter call failed in the sandbox; process RSS/CPU sampling used by the app succeeded. No power modes or clocks were changed.

The original checkout is clean on main at `5e76a255bff31e70c5ff065d3d134db804cd33cd`. Initial sandbox Git access failed with Permission denied; a read-only elevated check confirmed its status. Initial network clone failed with getaddrinfo thread failed; approved network clone succeeded in the writable workspace. Venv ensurepip failed; development packages were installed into that venv using the bundled runtime pip `--python` option. System Python/CUDA were not modified.

User confirmed no SSH target is currently available and requested files to copy to the Jetson Desktop. Run `python3 -m embedded_sg6.audit > jetson_environment.json` there before installation. The audit reads board metadata, L4T, OS, memory, disk, video devices, OpenCV build and dependency availability; missing commands are explicitly reported.
''')
    inventory = '''# SG6 module inventory

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
'''
    write('SG6_MODULE_INVENTORY.md', inventory)
    write('SG6_GIT_INTEGRATION_REPORT.md',f'''# SG6 Git integration report

Canonical repository: https://github.com/Hassanahmed-15/drowsiness-detection-system . Stable base `5e76a255bff31e70c5ff065d3d134db804cd33cd`; isolated clone and branch `integration/jetson-sg6`. Original clean checkout untouched. No stash, resets, clean, forced deletion, force push or main update. GitHub connector reports pull=true, push=false, so no push or PR was attempted.

## Audited references

```text
{refs}
```

SG2 is a no-ff merge (its midterm/experiment histories already included). SG1, SG3 and SG4 branches descend from the base but remove other subgroup/scaffold paths and replace root READMEs. A blind merge would delete unrelated team work. Audited source directories were imported with `integration/import_sources.py`; original algorithm files remain separately identifiable. Commit `8727c76` records the imports. SG5 patch branch algorithms were imported unchanged plus importable .py copies. Their branches/histories remain available in remote refs and the optional Git bundle. No merge conflicts were hidden or resolved by selecting a newer file.

Imported SG4 excludes tracked __pycache__ bytecode, generated fig.png/in.jsonl/out.jsonl. SG3 excludes generated results/sg3_output.json. The older SG1 source is retained under old/ but not executed. Module READMEs and requirements moved with each source. Scaffold/root docs preserved.

Other patch branches examined: sabihjil-patch-1 is SG3 documentation; tehreemfaisall-patch-1 is empty scaffold; patch-2 adds nested SG1 landmark-map documentation; patch-3 adds historical comparison CSV only. alveenashahidd-patch-1 is mock SG5 dataset; patch-2 is a duplicate rule function. sg3-patch-3 contains a Colab SG5 notebook and PDF, not SG3 production code: notebook rule/weighted thresholds differ from selected .py algorithms. Excluded as alternative experiments pending SG5 owner agreement. No benchmark numbers from these artifacts are presented as SG6 measurements.

Validation order limitation: subgroup sources were imported/committed before test dependencies finished installing. Subsequent import, schema, unit and integration checks were run together; this does not meet the requested per-merge test/commit order retroactively. Initial failures and fixes are retained in test reports. Existing V1 schema is unchanged; SG6 uses backward-compatible adapters and explicitly documented selection policies.

Local history can be reviewed with `git log --oneline --graph --all`. For transfer including histories, use the separately generated `sg6-history.bundle`, then `git clone -b integration/jetson-sg6 sg6-history.bundle sg6-source`. Runtime ZIP is intentionally smaller and excludes .git/venv/models.
''')
    write('SG6_SYSTEM_ARCHITECTURE.md','''# SG6 system architecture

```mermaid
flowchart LR
  A[One OpenCV capture] --> B[SG1 MediaPipe Tasks]
  B --> C[SG2 selected eye classifier]
  B --> D[SG3 MAR from eight real full landmarks]
  C --> E[SG6 field adapter and frame alignment]
  D --> E
  E --> F[SG4 elapsed-time window]
  F --> G[SG5 rule or weighted decision]
  G --> H[SG6 cooldown software alert]
```

Canonical entry `embedded_sg6/app.py`. Config `embedded_sg6/config.json`; CLI overrides select source, model, GUI, frame limit and output paths. `Pipeline` initializes reusable modules once. Input frame and timestamp are shared. VIDEO timestamps derive from verified container FPS; live read completion uses monotonic_ns; performance uses perf_counter_ns. Replayed source timestamps are preserved in SG2/SG3; existing SG4 truncates to integer milliseconds. Strict increasing source timestamps prevent stale replay. This does not add a new V1 contract or claim a formally approved shared schema exists.

SG1 nested records are flattened only at adapter boundary. SG2's frozen JSON Schema is validated with a cached Draft202012Validator every frame. SG2 `eye_valid`/`eye_state` -> SG4 `eyes_valid`/nullable `eyes_closed`; matching frame IDs/timestamps enforced. SG3 eight inner lip points use indices 78,82,13,312,308,317,14,87 from actual full landmarks. SG1 four-point mouth remains unchanged. Missing optional landmarks produce unknown mouth evidence. A model confidence score is never invented. SG3 sigmoid output and SG5 scores are heuristic, not calibrated probabilities.

Driver policy: configure normalized driver_region for the seat. If multiple faces occur inside it, mark observation unknown rather than selecting a different person by largest area. With one face, SG1's region selection is used. Identity continuity through a completely replaced single face is not verified; reset/recalibration is required for a new driver. Driver region must be established on the vehicle.

Unknown current face/eyes gates SG5 invalid even if historical window remains valid. Pending SG2 blink is cancelled on missing face or gap > SG4 max_gap_ms, without emitting an inferred blink. SG4 remains the authoritative time-based closure/event window. Its default warmup=5000 ms and unvalidated thresholds remain unchanged. Pipeline validation errors emit explicit INVALID records, reset histories and continue; five consecutive module errors stop. Camera read failure stops in UNKNOWN with a clear error. No automatic reconnect is promised. Capture/detector/file/GUI resources close via ExitStack; Ctrl+C is handled. Alert sink exceptions are reported as alert_error rather than confirming successful output.

Synchronous capture is selected: one outstanding frame, no producer queue or thread shutdown problem. Latest-frame threading is deferred until target camera-buffer latency is measured. Hidden backend buffering and frame drops are unknown. Full frame landmark output is needed for SG3; SG1 currently also creates three ROI copies. No change to that code was justified by target profiling. RGB conversion, detector and landmarks are currently measured together as sg1_ms because the upstream Tasks call combines inference stages.

JSONL is streamed (no accumulated frame/video buffer). Metrics aggregate means/maxima and sampled RSS. Processing FPS includes input/model startup after Pipeline initialization and output work; it is not sensor FPS. read_complete_to_decision_ms excludes sensor exposure/backend buffering; physical camera-to-alert delay is unavailable. Software alerts are JSON stderr events with monotonic cooldown, not a buzzer. Physical hardware integration should implement an alert sink update(decision, monotonic_ms), report failures, and retain cooldown gating.
''')
    write('SG6_JETSON_DEPLOYMENT.md','''# SG6 Jetson deployment

Follow `START_HERE_JETSON.md`; package is designed for copying to the Jetson Desktop. Shell files use LF and can be invoked with bash without executable permission.

The target board is unknown. The guide's Orin Nano target is not evidence of an installed Orin board. Audit first. Python >=3.10 is required by SG4 and this integration. Original Nano/older JetPack software may be incompatible; setup explicitly refuses older Python rather than upgrading system Python/CUDA. No ARM64 MediaPipe, TensorRT, CUDA, FP16 or PyTorch compatibility claim is made. Core landmark replay still needs usable NumPy/OpenCV/PyYAML/jsonschema. Do not install the Windows lock file on Jetson.

Setup: `bash setup_jetson.sh`. Audit: `python3 -m embedded_sg6.audit`. Tests: `bash test_jetson.sh`. Help: `bash run_jetson.sh --help`. Recorded landmarks: `bash run_jetson.sh --sg1-jsonl interfaces/sg2/examples/eb8_09_real_sg1.jsonl --headless --benchmark`. Raw input: explicitly acquire model with `.venv/bin/python -m embedded_sg6.download_face_model`, then `bash run_jetson.sh --video /path/driver.mp4 --headless` or `--camera 0`.

Model source is the versioned Google URL in download_face_model.py, selected by original SG1/SG2. Official documentation: https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker . Component model cards (FaceMesh V2, BlazeFace Short Range, Blendshape V2) are linked there; reviewed cards state Apache-2.0. Local SHA256 and byte size are in models/face_landmarker.provenance.json; no publisher checksum was provided. ZIP integrity and actual Tasks loading were verified locally. Weights are excluded from Git and transfer ZIP, so acquisition is explicit. SG2 release SHA256 acquisition script is preserved; CNN absent and unverified.

Camera/CSI/GUI commands are implemented, not target verified. Use system camera enumeration and OpenCV build diagnostics first. Physical alert hardware is unavailable; only software JSON alert sink exists. Preserve separate output/metrics paths for each benchmark. Labelled driver video and target sustained runs are required before any accuracy, false-alert-rate or real-time deployment claim.
''')
    write('SG6_PERFORMANCE_BENCHMARK.md',f'''# SG6 performance benchmark

Verification: VERIFIED ON RECORDED INPUT, Windows CPU, not Jetson. Structured results: `evaluation/sg6_validation_experiment.json`. Reproduce: `python -m embedded_sg6.benchmark`. Hypothesis: cache the unchanged JSON Schema validator instead of calling jsonschema.validate (which builds/checks it every frame). One factor varies; unchanged backup EAR config, same committed 600 SG1 landmarks, three repeated runs with alternating order. Other local test processes were active, so absolute throughput has contention and is not a controlled idle-machine capacity claim.

Median baseline {exp['median_fps']['baseline']:.2f} observations/s; cached {exp['median_fps']['cached']:.2f} observations/s. All six algorithm-output SHA256 digests identical: {exp['identical_outputs']}. This supports cached validation, not an algorithm/backend improvement. Each row stores validation latency, elapsed time, RSS and output hash. No camera/video/SG1 inference/CNN is included. Source landmarks carry hand-labelled blinks, but this experiment checks unchanged predictions, not new whole-system accuracy. Full drowsiness labels are unavailable.

Raw no-face smoke: generated 320x240 MJPG AVI, 10 FPS source, 30 blank frames, actual SG1 Tasks model. Status {raw['status']}, {raw['frames']} frames, {raw['errors']} errors, processing FPS including startup {raw['processing_fps']:.2f}, sampled peak RSS {raw['peak_sampled_rss_bytes']} bytes. See `evaluation/sg6_no_face_metrics.json`. Blank input does not validate face detection/eye/yawn accuracy or representative runtime; SG1 includes cold import/model startup in elapsed total. Stage means/maxima and CPU are recorded separately.

GPU utilization, thermals, power mode, actual camera input FPS, dropped sensor frames and physical camera-to-alert latency: unavailable. No TensorRT/FP16/backend/async optimization was justified without target profiling. No sustained stability or memory-leak clearance claim. Adaptive EAR calibration and yawn smoothing still depend on frame/sample counts; temporal events use SG4 time windows. Re-run on the actual target with identical labelled recordings and warmup policy before choosing resolution, threading, power mode or inference backend.
''')
    write('SG6_TEST_RESULTS.md',f'''# SG6 test results

Latest local suite: {count} tests, {passed} passed, {failures} failures, {errors} errors, {skipped} skipped. Evidence `evaluation/sg6_release_tests.xml`. Command: `python -m pytest -q --basetemp=.pytest-tmp/release-run --junitxml=evaluation/sg6_release_tests.xml` (create .pytest-tmp parent first on Windows). Standard Jetson command: `bash test_jetson.sh`. SG2/SG3/SG4 original tests preserved; SG6 tests under tests/.

VERIFIED ON RECORDED INPUT: all 600 committed real SG1 landmark records through adapters, SG2 schema, SG3 unknown mouth handling, SG4 and SG5, with timestamps/frame association. Original SG2 hand-labelled blink assertions pass if included in successful suite. Real recorded source timestamps may be fractional; accepted as required by existing schema. SG4 retains its integer truncation behavior.

VERIFIED USING MOCK DATA: valid/invalid points and types, empty/missing optional fields, duplicate timestamps, no face, face loss after closure without fabricated blink, sustained eye closure and recovery, SG3 full-landmark mouth -> temporal yawn count, SG5 rule/weighted threshold boundary and poor validity, cue alignment rejection, software alert cooldown. Original SG4 tests cover irregular/dropped samples, gaps, blink/yawn events, missing face and window expiry. These results verify logic, not detection accuracy in drivers.

VERIFIED ON RECORDED INPUT (generated blank fixture only): raw decoder + real SG1 model + 30 no-face observations + no confirmed drowsiness or alert; actual model initialization/cleanup. Fixture generation uses VideoWriter MJPG, 30 all-zero 320x240 frames at 10 FPS. It is intentionally not a labelled driver video. Missing-model test returns nonzero with clear path error before camera access; stored metrics in sg6_missing_model_metrics.json.

NOT TESTED: live USB camera capture, CSI, GUI, physical alarm, Jetson imports/model loading/performance, target power/thermal modes, sustained memory stability, real-driver raw video, complete system labelled accuracy/false-alert rate. No VERIFIED ON JETSON claims.

Historical failures retained: initial collection ran before dependency installation finished (missing jsonschema/mediapipe); an integration validator initially rejected fractional timestamps (fixed against schema); sandbox pytest temporary-directory failures were resolved by selecting a workspace temp directory and creating its parent. Earlier XML reports are historical, not final readiness evidence. Static SG3 API mismatch was repaired by restoring its documented unused mouth_roi argument; algorithm unchanged.
''')
    write('SG6_INTEGRATION_READINESS.md',f'''# SG6 integration readiness

Overall: PARTIAL INTEGRATION; local evidence exists; not a fully validated Jetson system.

- Gate A Git safety: PASS locally. Dedicated integration branch, original checkout/main intact, source refs preserved; no remote push because connector push permission is false.
- Gate B modules/interfaces: PARTIAL. SG1-SG5 sources integrated and {passed} tests passed locally; selected SG5 patch variant needs owner confirmation; no formally frozen shared full-system V1 document/schema was present (interfaces/README is a placeholder; SG2 schema is authoritative for SG2).
- Gate C pipeline: PARTIAL. Real landmark replay and generated blank raw video work locally. Driver raw-video/camera, CNN, complete mouth/head-cue performance and physical actuator unverified.
- Gate D Jetson: NOT TESTED. User will copy package to target. Actual board/Python/JetPack, ARM64 dependencies, model loading and resources must be audited there.
- Gate E quantitative validation: PARTIAL. Controlled schema-cache comparison with identical algorithm outputs; no target baseline/optimized measurements or full-system accuracy.
- Gate F reproducibility: PARTIAL. Canonical CLI, configs, dependency manifest, safe setup/audit/test scripts, reports and transfer package exist. Device-dependent packages still require actual target compatibility validation.

## Checklist

- [x] Audit repository, source branches and Windows development host.
- [x] Preserve original checkout and create dedicated integration branch.
- [x] Integrate real subgroup sources with traceable provenance.
- [x] Connect contracts without rewriting original schemas.
- [x] Implement canonical headless app, software alert and profiling.
- [x] Run local unit/interface/replay/no-face model tests and controlled validation experiment.
- [x] Prepare Jetson handoff and report limitations.
- [ ] Identify actual board and compatible Python/MediaPipe/OpenCV environment.
- [ ] Verify actual camera, driver selection and real face/eye/mouth data.
- [ ] Confirm SG5 selected rule variant and freeze shared contracts with team.
- [ ] Calibrate SG3/SG4/SG5 thresholds against labelled held-out driver data.
- [ ] Verify CNN licensing/loading, physical alert, target performance and sustained stability.

SG6 contributions are adapters, capture ownership, runtime/configuration, validation, alert execution, diagnostics/profiling, tests and deployment. SG1-SG5 algorithms remain the team's work. Next device run begins with START_HERE_JETSON.md; do not describe this handoff as production-ready or Jetson-verified.
''')

if __name__ == '__main__':
    main()
