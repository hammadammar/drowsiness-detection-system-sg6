# SG6 Git integration report

Canonical repository: https://github.com/Hassanahmed-15/drowsiness-detection-system . Stable base `5e76a255bff31e70c5ff065d3d134db804cd33cd`; isolated clone and branch `integration/jetson-sg6`. Original clean checkout untouched. No stash, resets, clean, forced deletion, force push or main update. GitHub connector reports pull=true, push=false, so no push or PR was attempted.

## Audited references

```text
origin 5e76a255bff31e70c5ff065d3d134db804cd33cd
origin/alveenashahidd-patch-1 72ead8828edc4f7dac6fefd6264e9725c9dc3839
origin/alveenashahidd-patch-1-1 4cc9a2531bff7e8f35bf23786b8c1ce8d748a326
origin/alveenashahidd-patch-2 8c2bcad750a9aba4f2b41fe253cc05fca17a97a4
origin/embedded_sg6 5e76a255bff31e70c5ff065d3d134db804cd33cd
origin/main 5e76a255bff31e70c5ff065d3d134db804cd33cd
origin/module_sg1 6b78a7242772bdce641eedaeb6a03e3650ba4615
origin/module_sg2 b8dd288308b0d8e8515965ee70b93de736f7f93f
origin/module_sg3 eccb03c43c4fc8450316e5e7a13e39fa084c029b
origin/module_sg4 c5bd34dc15974e5f3e1028d6b3a426939eeb9e22
origin/module_sg5 5e76a255bff31e70c5ff065d3d134db804cd33cd
origin/sabihjil-patch-1 f8cbafc2e68fb5063b6363830546c7dc5d3cde57
origin/sg2/midterm 19a24ae0d49bf2514a0351b1eccbdad5936093ef
origin/sg2/w5-eye-state-experiments 41a7f53b25f11776e2647c9c13a5fcd688a5d499
origin/sg3-patch-3 7ab4275a4cab5159e2427ae6ad9cbfe3cb5708a2
origin/tehreemfaisall-patch-1 549a756790c12139916cbc2a06210fd4b67812ca
origin/tehreemfaisall-patch-2 8238f4d28f532fab675f3aa3ed6eac891df5447f
origin/tehreemfaisall-patch-3 9c0cc439489af8c4eb86fde1c382c7a9b3eed13d
```

SG2 is a no-ff merge (its midterm/experiment histories already included). SG1, SG3 and SG4 branches descend from the base but remove other subgroup/scaffold paths and replace root READMEs. A blind merge would delete unrelated team work. Audited source directories were imported with `integration/import_sources.py`; original algorithm files remain separately identifiable. Commit `8727c76` records the imports. SG5 patch branch algorithms were imported unchanged plus importable .py copies. Their branches/histories remain available in remote refs and the optional Git bundle. No merge conflicts were hidden or resolved by selecting a newer file.

Imported SG4 excludes tracked __pycache__ bytecode, generated fig.png/in.jsonl/out.jsonl. SG3 excludes generated results/sg3_output.json. The older SG1 source is retained under old/ but not executed. Module READMEs and requirements moved with each source. Scaffold/root docs preserved.

Other patch branches examined: sabihjil-patch-1 is SG3 documentation; tehreemfaisall-patch-1 is empty scaffold; patch-2 adds nested SG1 landmark-map documentation; patch-3 adds historical comparison CSV only. alveenashahidd-patch-1 is mock SG5 dataset; patch-2 is a duplicate rule function. sg3-patch-3 contains a Colab SG5 notebook and PDF, not SG3 production code: notebook rule/weighted thresholds differ from selected .py algorithms. Excluded as alternative experiments pending SG5 owner agreement. No benchmark numbers from these artifacts are presented as SG6 measurements.

Validation order limitation: subgroup sources were imported/committed before test dependencies finished installing. Subsequent import, schema, unit and integration checks were run together; this does not meet the requested per-merge test/commit order retroactively. Initial failures and fixes are retained in test reports. Existing V1 schema is unchanged; SG6 uses backward-compatible adapters and explicitly documented selection policies.

Local history can be reviewed with `git log --oneline --graph --all`. For transfer including histories, use the separately generated `sg6-history.bundle`, then `git clone -b integration/jetson-sg6 sg6-history.bundle sg6-source`. Runtime ZIP is intentionally smaller and excludes .git/venv/models.
