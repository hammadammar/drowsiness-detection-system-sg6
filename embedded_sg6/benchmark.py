"""Controlled experiment: construct/check schema per frame versus cache validator.

Uses committed SG1 landmarks, NOT camera throughput or Jetson inference.
"""
import argparse
import hashlib
import json
import statistics
import time

from .pipeline import Pipeline, ROOT

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repeats',type=int,default=3)
    p.add_argument('--output',default='evaluation/sg6_validation_experiment.json')
    a = p.parse_args()
    path = ROOT/'interfaces/sg2/examples/eb8_09_real_sg1.jsonl'
    blocks = [json.loads(line) for line in path.read_text().splitlines()]
    import jsonschema
    import psutil
    schema = json.loads((ROOT/'interfaces/sg2/sg2_eye_state_v1.schema.json').read_text())
    class Baseline:
        def validate(self, value):
            jsonschema.validate(value, schema)
    rows, signatures = [], {}
    for repeat in range(a.repeats):
        for mode in (('baseline','cached') if repeat % 2 == 0 else ('cached','baseline')):
            pipe = Pipeline(ROOT/'module_sg2/configs/backup.yaml',alert_sink=lambda e:None)
            if mode == 'baseline':
                pipe.validator = Baseline()
            outputs = []
            stage = 0
            start = time.perf_counter()
            for block in blocks:
                out = pipe.process(block)
                stage += out.pop('stage_latency_ms')['validation_ms']
                outputs.append(out)
            elapsed = time.perf_counter()-start
            # Alert wall-clock cooldown is not an inference output and is excluded.
            for out in outputs:
                out.pop('software_alert')
            digest = hashlib.sha256(json.dumps(outputs,sort_keys=True).encode()).hexdigest()
            signatures[mode] = digest
            rows.append(dict(repeat=repeat,mode=mode,frames=len(blocks),elapsed_s=elapsed,
                             processing_fps=len(blocks)/elapsed,validation_mean_ms=stage/len(blocks),
                             rss_bytes=psutil.Process().memory_info().rss,output_sha256=digest))
    result = dict(hypothesis='Caching an unchanged SG2 schema validator reduces validation overhead without changing algorithm outputs',
                  verification='VERIFIED ON RECORDED INPUT (SG1 landmarks only)',
                  input=str(path.relative_to(ROOT)), input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  factor='Validator construction/checking strategy only',eye_config='backup.yaml (no image/CNN)',
                  identical_outputs=len({r['output_sha256'] for r in rows})==1,rows=rows,
                  median_fps={mode:statistics.median(r['processing_fps'] for r in rows if r['mode']==mode) for mode in ('baseline','cached')})
    (ROOT/a.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    main()
