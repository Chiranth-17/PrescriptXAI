"""Measure the complete historical serial workload on committed current source."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter_ns, process_time_ns

import numpy as np
import torch
import yaml
from filelock import FileLock
from threadpoolctl import threadpool_info, threadpool_limits

import prescriptxai
from prescriptxai.config import AppConfig
from prescriptxai.constraints.bounds import allowed_interval
from prescriptxai.data.cmapss import load_cmapss_archive, to_model_frame
from prescriptxai.evaluation.experiments import (
    content_hash,
    file_hash,
    runtime_manifest,
    source_revision,
)
from prescriptxai.evaluation.metrics import engine_bootstrap_interval
from prescriptxai.evaluation.runner import raw_telemetry
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.schemas import RecourseResult


def atomic_json(path, value):
    """Keep a prior complete manifest and atomically replace each JSON document."""
    temporary = path.with_suffix(path.suffix+'.tmp')
    if path.exists():
        prior = path.with_suffix(path.suffix+'.previous')
        prior_temp = prior.with_suffix(prior.suffix+'.tmp')
        prior_temp.write_bytes(path.read_bytes())
        prior_temp.replace(prior)
    with temporary.open('w',encoding='utf-8') as stream:
        stream.write(json.dumps(value,indent=2,allow_nan=False))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def verified_early_exit(result, state, config, pipeline):
    """Explain absent solver settings only when the frozen action box proves no search began."""
    if result.failure is None:
        return False
    taxonomy, bundle = pipeline.engine.taxonomy, pipeline.engine.model
    scales = dict(zip(bundle.feature_names,bundle.scaler.scaler.scale_,strict=True))
    required = 0
    infeasible = False
    for name in taxonomy.active_controllable_feature_names(bundle.feature_names):
        try:
            low,high = allowed_interval(state[name],taxonomy.actuator_constraints[name],
                                        horizon_steps=config.recourse.rate_horizon_steps)
            lower = max((low-state[name])/scales[name],-config.recourse.max_scaled_distance)
            upper = min((high-state[name])/scales[name],config.recourse.max_scaled_distance)
            infeasible = infeasible or lower > upper
            required += int(lower > 0 or upper < 0)
        except ValueError:
            infeasible = True
    if result.failure.reason == 'infeasible_actuator_interval':
        return infeasible
    if result.failure.reason == 'mandatory_changes_exceed_sparsity':
        return not infeasible and required > config.recourse.k_max
    return False


def validate_sample(mode, index, encoded, states, config, pipeline):
    """Reject corrupt, swapped, out-of-population or incompatible resumed public records."""
    if mode not in ('fast','thorough') or not isinstance(index,int) or not 0 <= index < 1000:
        raise ValueError('checkpoint contains unexpected mode or index')
    row = json.loads(encoded)
    state = states[index]
    if row['original_state'] != state or (row['engine_id'],row['cycle']) != (state['engine_id'],state['cycle']):
        raise ValueError('checkpoint state differs from the indexed canonical query')
    for key in ('public_call_ms','process_cpu_ms'):
        if isinstance(row[key],bool) or not isinstance(row[key],(float,int)) or not np.isfinite(row[key]) or row[key] < 0:
            raise ValueError('checkpoint duration is not finite and nonnegative')
    times = [datetime.fromisoformat(row[key]) for key in ('started_utc','finished_utc')]
    if any(value.tzinfo is None or value.utcoffset().total_seconds() != 0 for value in times):
        raise ValueError('checkpoint timestamps must be aware UTC values')
    if times[0] > times[1]:
        raise ValueError('checkpoint UTC chronology is inconsistent')
    if row['status'] == 'ERROR':
        if not row.get('error_type') or row.get('result') is not None or row['timings']:
            raise ValueError('malformed recorded error')
    else:
        result = RecourseResult.model_validate(row['result'])
        effective = config.model_copy(deep=True)
        effective.recourse.search_mode = mode
        if (result.original_state != state or result.mode != mode.upper()
            or result.status != row['status'] or result.timings.model_dump(mode='json') != row['timings']
            or result.config_hash != content_hash(effective.model_dump(mode='json'))
            or result.model_version != pipeline.model_version or result.seed != config.seed
            or result.tau_safe != config.tau_safe or result.tau_danger != config.tau_danger
            or (result.solver_settings and result.solver_settings.get('search_mode') != mode)):
            raise ValueError('checkpoint public result/config/mode/settings differ')
        if not result.solver_settings and not verified_early_exit(result,state,config,pipeline):
            raise ValueError('absent solver settings lack a verified frozen-box early exit')
        if result.solver_settings:
            expected = {'max_iter':config.recourse.max_iterations,'restarts':config.recourse.restarts,
                        'alpha_steps':config.recourse.alpha_steps,'support_search_limit':config.recourse.support_search_limit,
                        'feedback_max_refinements':config.validation.feedback_max_refinements,
                        'search_mode':mode,'k_max':config.recourse.k_max,
                        'max_scaled_distance':config.recourse.max_scaled_distance,
                        'true_model_grid_points':config.recourse.true_model_grid_points,
                        'grid_support_cap':None,'validate_plausibility':True,'check_distribution':True,
                        'check_coupling':True,'propagate_dependents':True,
                        'effective_distribution_filter':True,'effective_coupling_filter':True}
            if any(result.solver_settings.get(key) != value
                   or type(result.solver_settings.get(key)) is not type(value)
                   for key,value in expected.items()):
                raise ValueError('recorded effective solver settings differ from frozen runtime policy')
    return hashlib.sha256(encoded.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    design = yaml.safe_load(args.config.read_text(encoding='utf-8'))
    fixed = {'calls_per_mode':1000, 'warmups_per_mode':10, 'modes':['fast','thorough'],
             'expected_engines':16, 'native_threads':1, 'torch_interop_threads':1, 'bootstrap_replicates':2000,
             'bootstrap_seed':1729, 'bootstrap_confidence':.95}
    if any(design.get(k) != v for k,v in fixed.items()):
        raise ValueError('the full registered serial design is required')
    source = source_revision(require_clean=True)
    if Path(prescriptxai.__file__).resolve() != (Path.cwd()/'src/prescriptxai/__init__.py').resolve():
        raise ValueError('imports must resolve to this committed source')
    if args.resume and (not (args.output/'manifest.json').is_file()
                        or not (args.output/'samples.sqlite3').is_file()):
        raise ValueError('resume requires the existing manifest and checkpoint')
    if args.resume and (args.output/'complete.json').exists():
        raise ValueError('the measurement already completed; audit it without resuming')
    args.output.mkdir(parents=True, exist_ok=args.resume)
    serial_lock = Path('artifacts/remediation/serial-latency.lock')
    serial_lock.parent.mkdir(parents=True,exist_ok=True)
    with FileLock(serial_lock,timeout=0), FileLock(args.output/'measurement.lock', timeout=0):
        measure(args, design, source)


def measure(args, design, source):
    original = Path(design['historical_directory'])
    historical = json.loads((original/'manifest.json').read_text(encoding='utf-8'))
    if historical['git_hash'] != design['historical_source']:
        raise ValueError('historical source differs from registration')
    with closing(sqlite3.connect((original/'records.sqlite3').resolve().as_uri()+'?mode=ro',uri=True)) as old:
        encoded, = old.execute(
            "SELECT c.payload FROM records r JOIN cases c USING(case_id) "
            "WHERE json_extract(r.payload,'$.group')=? AND json_extract(r.payload,'$.seed')=? LIMIT 1",
            ('FD001/xgb/v1/development_all_alerts/fast/full',1729)).fetchone()
        config = AppConfig.model_validate(json.loads(encoded)['config'])
    if (config.tau_safe,config.tau_danger,config.recourse.rate_horizon_steps,
        config.recourse.k_max,config.validation.mahalanobis_max) != (.2,.8,1,3,5.):
        raise ValueError('scientific limits differ from registration')
    historical_latency = json.loads((original/'latency.json').read_text(encoding='utf-8'))
    if content_hash(config.model_dump(mode='json')) != historical_latency['labels']['config_hash']:
        raise ValueError('the full effective config differs from the historical serial config')
    with closing(sqlite3.connect((original/'latency.sqlite3').resolve().as_uri()+'?mode=ro',uri=True)) as old:
        identities = {}
        for mode in design['modes']:
            values = [json.loads(row[0]) for row in old.execute(
                'SELECT payload FROM samples WHERE mode=? ORDER BY idx',(mode,))]
            identities[mode] = [(row['engine_id'],row['cycle']) for row in values]
    if identities['fast'] != identities['thorough'] or len(identities['fast']) != 1000:
        raise ValueError('the original complete mode workloads must match')
    if len({row[0] for row in identities['fast']}) != design['expected_engines']:
        raise ValueError('the original engine population differs')
    archive = config.data.root/config.data.archive_name
    if file_hash(archive) != historical['archive_sha256']:
        raise ValueError('the original raw archive hash differs')
    frame = to_model_frame(load_cmapss_archive(archive,'FD001').train).set_index(['engine_id','cycle'],drop=False)
    states = [raw_telemetry(frame.loc[(engine,cycle)]) for engine,cycle in identities['fast']]
    asset = historical['assets']['models']['FD001/xgb/base']
    expected = {str(config.pipeline.taxonomy_path):historical['taxonomy_sha256'],
                **{str(Path(asset['paths'][key])):asset['hashes'][key]
                   for key in ('model','coupling','mahalanobis_v1')}}
    loaded_paths = [config.pipeline.taxonomy_path,config.artifacts.model,
                    config.artifacts.coupling,config.artifacts.mahalanobis]
    inputs = {str(path):file_hash(path) for path in loaded_paths if path is not None}
    if inputs != expected:
        raise ValueError('fitted assets or taxonomy differ from historical run')
    code = {str(path):file_hash(path) for path in Path('src/prescriptxai').rglob('*.py')}
    code[str(Path(__file__).resolve().relative_to(Path.cwd().resolve()))] = file_hash(Path(__file__))
    signature = {'source':source,'design':design,'config':config.model_dump(mode='json'),
                 'config_sha256':file_hash(args.config),'historical_serial_database_sha256':file_hash(original/'latency.sqlite3'),
                 'source_config_sha256':file_hash(Path(design['source_config'])),
                 'selected_historical_case_sha256':hashlib.sha256(encoded.encode()).hexdigest(),
                 'archive_sha256':file_hash(archive),'input_hashes':inputs,'code_hashes':code,
                 'identities':identities['fast'],'runtime':runtime_manifest()}
    identity = content_hash(signature)
    manifest_path = args.output/'manifest.json'
    if args.resume:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest['identity_sha256'] != identity:
            raise ValueError('resume source/config/inputs/workload/runtime are incompatible')
    else:
        manifest = {**signature,'identity_sha256':identity,'started_utc':datetime.now(UTC).isoformat(),
                    'segments':[],'population':'original_full_serial_1000_calls_per_mode_16_engines',
                    'scope':'warm serial backend; UI/network/startup/attribution unmeasured',
                    'protocol':'v1','K':1,'k_max':3,'D_max_version':'v1','D_max':5.0,
                    'measurement_config':str(args.config),'source_config':design['source_config']}
    awake = None
    if os.name == 'nt':
        awake = ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        if not awake:
            raise OSError('Windows rejected temporary idle-sleep inhibition; no calls started')
    segment = {'pid':os.getpid(),'start_utc':datetime.now(UTC).isoformat(),
               'idle_sleep_inhibition_return':awake,
               'note':'temporary idle-sleep request only; lid closure/user suspension can still interrupt'}
    manifest['segments'].append(segment)
    atomic_json(manifest_path,manifest)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    try:
        with threadpool_limits(limits=1), closing(sqlite3.connect(args.output/'samples.sqlite3')) as db:
            segment['torch_intra_threads'] = torch.get_num_threads()
            segment['torch_interop_threads'] = torch.get_num_interop_threads()
            segment['native_threadpools'] = threadpool_info()
            if (segment['torch_intra_threads'] != 1 or segment['torch_interop_threads'] != 1
                or any(pool['num_threads'] != 1 for pool in segment['native_threadpools'])):
                raise ValueError('actual runtime thread counts do not match serial registration')
            db.execute('CREATE TABLE IF NOT EXISTS samples(mode TEXT,idx INTEGER,payload TEXT,PRIMARY KEY(mode,idx))')
            pipeline = PrescriptXAI.from_config(config)
            if pipeline.config.recourse != config.recourse or pipeline.config.artifacts != config.artifacts:
                raise ValueError('effective solver/assets changed on load')
            existing = list(db.execute('SELECT mode,idx,payload FROM samples ORDER BY mode,idx'))
            preserved = {f'{mode}:{index}':validate_sample(mode,index,payload,states,config,pipeline)
                         for mode,index,payload in existing}
            sealed = {}
            for previous in manifest['segments'][:-1]:
                sealed.update(previous.get('checkpoint_hashes_after',{}))
            if any(preserved.get(key) != digest for key,digest in sealed.items()):
                raise ValueError('previously sealed checkpoint payloads were altered or removed')
            segment['checkpoint_hashes_before'] = preserved
            atomic_json(manifest_path,manifest)
            segment['completed_before'] = db.execute('SELECT count(*) FROM samples').fetchone()[0]
            for mode in design['modes']:
                done = {row[0] for row in db.execute('SELECT idx FROM samples WHERE mode=?',(mode,))}
                if len(done) < 1000:
                    for warmup in range(10):
                        pipeline.recommend(states[warmup],mode=mode)
                for index,state in enumerate(states):
                    if index in done:
                        continue
                    utc = datetime.now(UTC).isoformat()
                    started, cpu = perf_counter_ns(),process_time_ns()
                    try:
                        result = pipeline.recommend(state,mode=mode)
                        elapsed, cpu_ms = (perf_counter_ns()-started)/1e6,(process_time_ns()-cpu)/1e6
                        payload = {'status':result.status,'result':result.model_dump(mode='json'),
                                   'timings':result.timings.model_dump(mode='json')}
                    except Exception as error:
                        elapsed, cpu_ms = (perf_counter_ns()-started)/1e6,(process_time_ns()-cpu)/1e6
                        payload = {'status':'ERROR','error_type':type(error).__name__,'timings':{}}
                    payload.update({'engine_id':int(state['engine_id']),'cycle':int(state['cycle']),
                                    'original_state':state,'started_utc':utc,'finished_utc':datetime.now(UTC).isoformat(),
                                    'public_call_ms':elapsed,'process_cpu_ms':cpu_ms})
                    with db:
                        db.execute('INSERT INTO samples VALUES(?,?,?)',(mode,index,json.dumps(payload,allow_nan=False)))
            rows = {mode:[json.loads(row[0]) for row in db.execute('SELECT payload FROM samples WHERE mode=? ORDER BY idx',(mode,))]
                    for mode in design['modes']}
            after = {f'{mode}:{index}':validate_sample(mode,index,payload,states,config,pipeline)
                     for mode,index,payload in db.execute('SELECT mode,idx,payload FROM samples ORDER BY mode,idx')}
            if any(after.get(key) != digest for key,digest in preserved.items()):
                raise ValueError('completed checkpoint payloads changed during resume')
            segment['checkpoint_hashes_after'] = after
            segment['completed_after'] = db.execute('SELECT count(*) FROM samples').fetchone()[0]
        budgets = {'ingestion_ms':10,'inference_ms':15,'optimization_ms':1800,
                   'validation_ms':100,'pipeline_ms':2200,'dashboard_ms':250}
        actual_budgets = config.latency_budget
        if list(budgets.values()) != [actual_budgets.ingestion_max_ms,actual_budgets.inference_max_ms,
            actual_budgets.optimization_max_ms,actual_budgets.validation_max_ms,
            actual_budgets.pipeline_max_ms,actual_budgets.dashboard_max_ms]:
            raise ValueError('latency budgets differ from registration')
        modes = {}
        for mode,records in rows.items():
            modes[mode.upper()] = {}
            for stage,budget in budgets.items():
                available = [(r['engine_id'],r['public_call_ms'] if stage=='pipeline_ms' else r['timings'][stage])
                             for r in records if stage=='pipeline_ms' or r['timings'].get(stage) is not None]
                ids,values = (np.asarray([p[0] for p in available]),np.asarray([p[1] for p in available]))
                ci = engine_bootstrap_interval(ids,values,seed=1729,replicates=2000,confidence=.95,
                    statistic=lambda x:float(np.quantile(x,.95))) if available else None
                p95 = float(np.quantile(values,.95)) if available else None
                errors = sum(r['status']=='ERROR' for r in records)
                modes[mode.upper()][stage] = {'count':len(available),'all_query_count':len(records),
                    'missing_count':len(records)-len(available),'error_count':errors,
                    'engine_count':len(set(ids)),'p95_ms':p95,'p95_engine_ci':asdict(ci) if ci else None,
                    'upper_budget_ms':budget,'passed':None if p95 is None else p95<=budget and errors==0 and len(available)==1000}
        guarded = {**inputs,**code,str(archive):signature['archive_sha256'],
                   str(args.config):signature['config_sha256'],
                   design['source_config']:signature['source_config_sha256']}
        if source_revision(require_clean=True) != source or any(file_hash(Path(p))!=h for p,h in guarded.items()):
            raise ValueError('measured source or fitted inputs changed while running')
        if any(len(records)!=1000 for records in rows.values()):
            raise ValueError('required population is incomplete')
        errors = sum(row['status']=='ERROR' for records in rows.values() for row in records)
        report = {'complete':True,'calls':sum(map(len,rows.values())),'errors':errors,
                  'identity_sha256':identity,'modes':modes,'result_scope':manifest['scope'],
                  'source':source,'measurement_config':str(args.config),'config_sha256':file_hash(args.config)}
        atomic_json(args.output/'complete.json',report)
        print(json.dumps(report,indent=2))
        if errors:
            raise SystemExit(1)
    finally:
        segment['end_utc'] = datetime.now(UTC).isoformat()
        atomic_json(manifest_path,manifest)
        if os.name == 'nt':
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)


if __name__ == '__main__':
    main()
