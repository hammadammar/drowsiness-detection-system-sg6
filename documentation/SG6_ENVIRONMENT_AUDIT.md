# SG6 environment audit

Audit date: 2026-10-28 (Asia/Karachi). Actual development host is Windows 11 Pro 10.0.26300, AMD64, Intel Core i5-10310U (8 logical processors), Intel UHD Graphics driver 31.0.101.2140. CIM reports 16,515,596 KiB visible RAM and 3,968,264 KiB free at the sampled instant. HP IR Camera and HP HD Camera enumerate OK; live acquisition was not exercised.

Python: 3.12.14 (main, Aug 25 2026, 14:01:42) [MSC v.1944 64 bit (AMD64)]. Development package/build and disk/memory evidence: `evaluation/sg6_environment.json`; exact installed versions: `evaluation/development-windows-lock.txt`. NumPy 2.5.4, OpenCV 5.0.0, MediaPipe 1.2.0. Both OpenCV distributions were pulled into the isolated Windows development environment; do not copy it to ARM64. Use JetPack/system OpenCV on target.

This is not a Jetson. Board model, JetPack/L4T, Ubuntu/kernel, Jetson CUDA/cuDNN/TensorRT, nvpmodel power mode, thermals, CSI, GPU utilization and target profiling are NOT TESTED. PyTorch, TensorRT and ONNX Runtime are absent in the development venv. OpenCV build text and utility discovery are stored in the JSON. A Windows performance-counter call failed in the sandbox; process RSS/CPU sampling used by the app succeeded. No power modes or clocks were changed.

The original checkout is clean on main at `5e76a255bff31e70c5ff065d3d134db804cd33cd`. Initial sandbox Git access failed with Permission denied; a read-only elevated check confirmed its status. Initial network clone failed with getaddrinfo thread failed; approved network clone succeeded in the writable workspace. Venv ensurepip failed; development packages were installed into that venv using the bundled runtime pip `--python` option. System Python/CUDA were not modified.

User confirmed no SSH target is currently available and requested files to copy to the Jetson Desktop. Run `python3 -m embedded_sg6.audit > jetson_environment.json` there before installation. The audit reads board metadata, L4T, OS, memory, disk, video devices, OpenCV build and dependency availability; missing commands are explicitly reported.
