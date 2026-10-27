# SG6 integration readiness

Overall: PARTIAL INTEGRATION; local evidence exists; not a fully validated Jetson system.

- Gate A Git safety: PASS locally. Dedicated integration branch, original checkout/main intact, source refs preserved; no remote push because connector push permission is false.
- Gate B modules/interfaces: PARTIAL. SG1-SG5 sources integrated and 97 tests passed locally; selected SG5 patch variant needs owner confirmation; no formally frozen shared full-system V1 document/schema was present (interfaces/README is a placeholder; SG2 schema is authoritative for SG2).
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
