# SG6 Jetson deployment

Follow `START_HERE_JETSON.md`; package is designed for copying to the Jetson Desktop. Shell files use LF and can be invoked with bash without executable permission.

The target board is unknown. The guide's Orin Nano target is not evidence of an installed Orin board. Audit first. Python >=3.10 is required by SG4 and this integration. Original Nano/older JetPack software may be incompatible; setup explicitly refuses older Python rather than upgrading system Python/CUDA. No ARM64 MediaPipe, TensorRT, CUDA, FP16 or PyTorch compatibility claim is made. Core landmark replay still needs usable NumPy/OpenCV/PyYAML/jsonschema. Do not install the Windows lock file on Jetson.

Setup: `bash setup_jetson.sh`. Audit: `python3 -m embedded_sg6.audit`. Tests: `bash test_jetson.sh`. Help: `bash run_jetson.sh --help`. Recorded landmarks: `bash run_jetson.sh --sg1-jsonl interfaces/sg2/examples/eb8_09_real_sg1.jsonl --headless --benchmark`. Raw input: explicitly acquire model with `.venv/bin/python -m embedded_sg6.download_face_model`, then `bash run_jetson.sh --video /path/driver.mp4 --headless` or `--camera 0`.

Model source is the versioned Google URL in download_face_model.py, selected by original SG1/SG2. Official documentation: https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker . Component model cards (FaceMesh V2, BlazeFace Short Range, Blendshape V2) are linked there; reviewed cards state Apache-2.0. Local SHA256 and byte size are in models/face_landmarker.provenance.json; no publisher checksum was provided. ZIP integrity and actual Tasks loading were verified locally. Weights are excluded from Git and transfer ZIP, so acquisition is explicit. SG2 release SHA256 acquisition script is preserved; CNN absent and unverified.

Camera/CSI/GUI commands are implemented, not target verified. Use system camera enumeration and OpenCV build diagnostics first. Physical alert hardware is unavailable; only software JSON alert sink exists. Preserve separate output/metrics paths for each benchmark. Labelled driver video and target sustained runs are required before any accuracy, false-alert-rate or real-time deployment claim.
