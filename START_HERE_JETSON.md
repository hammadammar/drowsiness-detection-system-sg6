# Copy this folder to your Jetson Desktop

Status: 97 local tests passed; Jetson execution is NOT TESTED. This package contains the team's real SG1-SG5 algorithms and SG6 adapters. It is an academic prototype, with unvalidated temporal/decision thresholds.

Open a terminal in this folder. No sudo, power-mode changes, CUDA installs or model downloads happen automatically.

1. Identify your actual board and Python: `python3 -m embedded_sg6.audit > jetson_environment.json`. Also read `/proc/device-tree/model` and `/etc/nv_tegra_release`.
2. Run `bash setup_jetson.sh`. Requires Python >=3.10. It keeps system packages visible and installs only portable test/integration dependencies. It deliberately does not upgrade NumPy, OpenCV, CUDA, TensorRT or PyTorch.
3. If this is an **original Jetson Nano on JetPack 4**, its usual Python environment is too old for this source. Setup stops. An independently compatible Python >=3.10 environment, OpenCV bindings and MediaPipe Tasks ARM64 build must be established first. This package does not promise that wheels exist for that platform. Do not replace the OS Python to force installation.
4. For an Orin Nano, verify the installed JetPack/Python combination. Raw video needs `numpy`, `cv2`, `mediapipe.tasks`, and `pandas`. Use compatible NVIDIA/system OpenCV first. MediaPipe and ONNX Runtime wheels must match ARM64, Python and the OS. The Windows development lock file is evidence only, not a Jetson installation recipe.
5. Verify dependencies with `.venv/bin/python -m embedded_sg6.audit > evaluation/jetson_environment.json`.

## First test: no camera or model download

After NumPy and OpenCV are available:

```bash
bash test_jetson.sh
bash run_jetson.sh --sg1-jsonl interfaces/sg2/examples/eb8_09_real_sg1.jsonl --headless --benchmark
```

This replays real **recorded landmarks**, not the original camera video. It exercises SG2-SG5 and software alerts. SG3 requires optional full landmarks; recordings without those correctly give unknown mouth evidence. Primary SG2 config G warns and uses its existing adaptive EAR backup when the CNN/ONNX Runtime is absent. That is degraded operation, not CNN verification. To use the explicit backup, set `eye_config` to `module_sg2/configs/backup.yaml` in `embedded_sg6/config.json`.

## Raw camera/video

Install a verified compatible MediaPipe Tasks environment before proceeding. Acquire the versioned official face model explicitly:

```bash
.venv/bin/python -m embedded_sg6.download_face_model
.venv/bin/python -m embedded_sg6.smoke_video
bash run_jetson.sh --video /absolute/path/to/driver.mp4 --headless --benchmark
bash run_jetson.sh --camera 0 --headless --benchmark
```

Camera/video/GUI/CSI modes need target-device verification. `--display` enables overlays when a GUI exists; `--headless` is the default. CSI accepts an explicit `--csi-pipeline` string only if system OpenCV has GStreamer support; no generic CSI pipeline is assumed compatible. Use `v4l2-ctl --list-devices` if installed to identify USB cameras.

For SG2's CNN, see `module_sg2/models/README.md` and its checksum-verifying acquisition script. No SG2 model is bundled; its licensing/provenance must be confirmed by its owners before external distribution. No TensorRT conversion or CUDA acceleration has been verified.

Outputs are streamed to `evaluation/sg6_output.jsonl`; aggregate timings and resources go to `evaluation/sg6_metrics.json`. These paths are overwritten by a run; use `--output` and `--metrics` to retain separate runs. Press Ctrl+C for clean shutdown. Alerts are rate-limited JSON messages on stderr; a physical buzzer is not implemented.

For measured integration checks and blockers, read `documentation/SG6_TEST_RESULTS.md` and `documentation/SG6_INTEGRATION_READINESS.md`. Copy `jetson_environment.json`, the test XML, and performance output back for target-specific debugging. Camera read completion latency excludes exposure, driver buffering and physical alert latency.
