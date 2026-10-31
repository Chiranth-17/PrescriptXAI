import fs from 'node:fs/promises';

const ink='#153649', teal='#087f83', muted='#506773';
let evidenceCaption='';
function text(slide,value,x,y,w,h,size=28,color=ink,bold=false){
  const shape=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},
    fill:'none',line:{fill:'none',width:0,style:'solid'}});
  shape.text=value;
  shape.text.style={fontFamily:'Arial',fontSize:size,color,bold};
  return shape;
}
function page(p,title,notes=''){
  const s=p.slides.add({width:1280,height:720,background:{fill:'#ffffff'}});
  text(s,title,64,42,1152,105,44,ink,true);
  s.speakerNotes.text=notes;
  return s;
}
function lines(s,items,y=180,size=29){
  items.forEach((value,i)=>text(s,value,68,y+i*105,1136,92,size));
}
function table(s,values,widths,top=175,height=400,fontSize=24){
  const t=s.tables.add({rows:values.length,columns:values[0].length,
    left:64,top,width:1152,height,columnWidths:widths,values});
  t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({
    fill:'#ffffff',textStyle:{fontFamily:'Arial',fontSize,color:ink},
    margins:{left:10,right:10,top:2,bottom:2}});
  t.cells.block({row:0,column:0,rowCount:1,columnCount:values[0].length}).assign({
    fill:ink,textStyle:{fontFamily:'Arial',fontSize,bold:true,color:'#ffffff'}});
  return t;
}
function foot(s,value,caption=evidenceCaption){
  text(s,value,66,622,1148,67,19,muted);
  text(s,caption,66,694,1148,22,14,muted);
}
function ci(g,m,percent=true,digits=1){
  const v=g.metrics[m].ci;if(v.estimate===null)return 'undefined';
  const k=percent?100:1;
  return `${(k*v.estimate).toFixed(digits)}\n[${(k*v.lower).toFixed(digits)}, ${(k*v.upper).toFixed(digits)}]`;
}
function group(e,profile,version,pop){
  return e.headline_groups[`${profile}/${version}/${pop}_all_alerts/fast/full`];
}
const sourceNote=e=>`Measured run ${e.study_manifest.run_id}; source ${e.study_manifest.git_hash}; `+
 `study ${e.study_manifest.study_path}, SHA256 ${e.study_manifest.study_file_sha256}. `+
 'Exact per-row config paths/runtime hashes, protocol/K/k_max/D_max/population and engine-bootstrap metadata are in paper/evidence.json. '+
 'K=1, k_max=3, v1 D_max=5 / v2 D_max=8. 95% whole-engine CIs, 2000 draws, bootstrap seed1729. All failed queries retained. Maximum E3 proxy evidence.';

export async function populate(p,root){
  const e=JSON.parse(await fs.readFile(`${root}/paper/evidence.json`,'utf8'));
  evidenceCaption=`Run ${e.study_manifest.run_id} | source ${e.study_manifest.git_hash.slice(0,12)} | exact row configs: paper/evidence.json`;
  if(Object.keys(e.headline_groups).length!==24)throw Error('complete24strata required');
  p.slides.keep([]);
  const note=sourceNote(e);
  let s=page(p,'PrescriptXAI',note);
  s.background.fill=ink;
  s.shapes.items[0].text.style={fontFamily:'Arial',fontSize:44,color:'#ffffff',bold:true};
  text(s,'Sparse recourse for\npredictive maintenance',70,180,1110,200,61,'#ffffff',true);
  text(s,'Separate model validity, statistical plausibility\nand proxy engineering evidence',74,420,1110,130,34,'#d5e9ed');
  text(s,'Research presentation | 30 October 2026 | At most E3',74,630,1110,40,23,'#d5e9ed');
  // The cover uses editable typography, with no illustration presented as physical evidence.
  s=page(p,'Research question',note+' Literature: https://arxiv.org/abs/2002.06278');
  lines(s,[
    'Can constrained recourse find sparse, plausible candidates within an assumed action space?',
    'A prediction change is a model result. A maintenance intervention needs response evidence.',
    'Static C-MAPSS supports proxy evaluation. Physical benefit remains unproven.'
  ]);
  s=page(p,'Data and proxy taxonomy',note+' C-MAPSS origin: https://ntrs.nasa.gov/citations/20090029214. Configs/features.yaml and docs/assumptions.md.');
  lines(s,[
    'FD001: XGBoost, MLP and LSTM. FD002: XGBoost. Fit isolation is by engine.',
    'Sensor channels are control proxies. Bounds, rates and intervention horizon K are assumptions.',
    'No direct bleed-valve command or ambient telemetry. Core-speed mapping differs from the synopsis.',
    'LSTM retains real history. Its scorable-alert population differs from snapshot models.'
  ],165,27);
  s=page(p,'Optimization in scaled control space',note+' Method: paper/manuscript.md Section3 and docs/math.md.');
  text(s,'J(delta) = movement + prediction penalty\n                  + bound penalty + feasibility feedback',70,174,1120,125,35,teal,true);
  lines(s,[
    'L-BFGS-B, frozen weight schedules and sparse-support search. Hard immutable masks and bounds.',
    'Raw delta_x = scale * delta_z. Dependent channels are propagated, not free decisions.',
    'True-model grid fallback uses the same limits. Finite search gives no global certificate.'
  ],340,27);
  s=page(p,'Four checks and a separate action gate',note+' E1–E5: AGENTS.md18; src/prescriptxai/validation/.');
  table(s,[['Check','Question'],['Tier1 / E1','Does true calibrated risk meet tau_safe?'],
    ['Tier2 / E2','Is Mahalanobis distance within the registered cutoff?'],
    ['Tier3 / E3 proxy','Do immutable fields, bounds, rates and context pass?'],
    ['Tier4 / E3 proxy','Do configured and learned sensor relationships pass?'],
    ['Joint success','All four tiers AND sparse-action feasibility']],[300,852],170,410,25);
  foot(s,'Validity, Tier2 all/returned, Tier3, Tier4 and joint are separate. No check establishes physical safety.');
  s=page(p,'Predictive and calibration diagnostics',note+' Original training revisions/hashes are in paper/evidence.json model_metadata; later evaluation configs are not original fitting files. Guo et al: https://proceedings.mlr.press/v70/guo17a.html');
  const predictors=[['Profile','Rows','AUROC','Brier before / after','ECE before / after']];
  for(const key of ['FD001/xgb/base','FD001/mlp/base','FD001/lstm/base','FD002/xgb/base']){
    const m=e.model_metadata[key].metrics;const b=m.calibration.test_before,a=m.calibration.test_after;
    predictors.push([key.replace('/base',''),String(m.test_holdout.sample_count),m.test_holdout.auroc.toFixed(4),
      `${b.brier_score.toFixed(5)} /\n${a.brier_score.toFixed(5)}`,`${b.ece.toFixed(5)} /\n${a.ece.toFixed(5)}`]);
  }
  table(s,predictors,[240,100,160,326,326],180,345,24);
  foot(s,'Saved point diagnostics, no invented CIs. Calibration is not uniformly improved. Predictor selection excludes recourse outcomes.');
  s=page(p,'FD001 XGBoost v1: search-surrogate error',note+' Model metadata observed holdout versus summary candidate groups. XGBoost: https://arxiv.org/abs/1603.02754');
  const observed=e.model_metadata['FD001/xgb/base'].metrics.surrogate_fidelity;
  const oof=group(e,'FD001/xgb','v1','grouped_oof');
  text(s,`Observed held-out MAE: ${observed.mae.toFixed(5)}\n${observed.sample_count} observed states`,70,182,510,150,36,teal,true);
  text(s,`Recourse-candidate MAE: ${ci(oof,'surrogate_MAE',false,3)}\n${oof.engines} engines, grouped OOF`,665,182,510,210,34,ink,true);
  text(s,'These are different populations. Final acceptance always uses the true calibrated predictor.',70,458,1100,95,31);
  foot(s,'Candidate interval is a 95% whole-engine bootstrap CI. Surrogate agreement does not certify intervention fidelity.');
  s=page(p,'Learned coupling residual evidence',note+' Source artifacts/phase7-models/index.json models[FD001/xgb/base].coupling_calibration. Validation engines also calibrate residual thresholds.');
  const cc=e.coupling_asset_index.models['FD001/xgb/base'].coupling_calibration;
  const cr=[['Channel','R2','Residual std','Share beyond envelope']];
  for(const name of ['sensor_3','sensor_4','sensor_6','sensor_14']){
    const v=cc.per_sensor[name];cr.push([name,v.r2.toFixed(3),v.residual_std.toPrecision(5),`${(100*v.share_beyond_threshold).toFixed(3)}%`]);
  }
  table(s,cr,[250,200,280,422],170,345,26);
  foot(s,`${cc.row_count} rows / ${cc.engine_count} calibration engines. Point diagnostics, not untouched-test CIs. Learned coupling is not physics simulation.`);
  s=page(p,'FD001 XGBoost across populations',note);
  const xr=[['Protocol / population','Engines','Validity %','T2 all %','Joint %']];
  for(const v of ['v1','v2'])for(const pop of ['internal_heldout','grouped_oof','official_test']){
    const g=group(e,'FD001/xgb',v,pop);xr.push([`${v} / ${pop.replace('internal_heldout','held-out').replace('grouped_oof','OOF').replace('official_test','official')}`,String(g.engines),ci(g,'validity'),ci(g,'plausibility_all'),ci(g,'joint')]);
  }
  table(s,xr,[285,100,255,255,257],165,430,24);
  foot(s,'95% engine CIs. K=1,k_max=3. Both protocols retained. Tier2 returned, Tier3, Tier4 and denominators follow in the appendix.');
  s=page(p,'Model validity alone is weak evidence',note);
  const contrast=[['Profile / protocol','Engines','Validity %','T2 all %','Joint %']];
  for(const profile of ['FD001/lstm','FD002/xgb'])for(const v of ['v1','v2']){
    const g=group(e,profile,v,'internal_heldout');contrast.push([`${profile} / ${v}`,String(g.engines),ci(g,'validity'),ci(g,'plausibility_all'),ci(g,'joint')]);
  }
  table(s,contrast,[285,100,255,255,257],185,340,24);
  foot(s,'Internal held-out alerts,95% engine CIs. History constraints limit LSTM recourse. High FD002 validity coexists with poor plausibility/joint evidence.');
  s=page(p,'Quality targets, measurements and gaps',note+' This panel is FD001/XGB/v1 internalheld-out only. Complete24stratum target gaps are in paper/appendix.md AppendixB. Verdicts use unrounded estimates.');
  const targetGroup=group(e,'FD001/xgb','v1','internal_heldout');
  const tr=[['Metric','Design target','Measured [95% engine CI]','Signed shortfall / verdict']];
  for(const [name,metric,target,upper,percent,digits] of [
    ['Validity','validity',.95,false,true,2],['T2 all','plausibility_all',.9,false,true,2],
    ['T2 returned','plausibility_returned',.9,false,true,2],
    ['Mean support / all','sparsity_all',3,true,false,2],
    ['Mean model-risk drop','risk_reduction',.60,false,false,6]]){
    const v=targetGroup.metrics[metric].ci.estimate;
    const gap=(upper?v-target:target-v)*(percent?100:1);
    tr.push([name,`${upper?'<= ': '>= '}${percent?target*100:target}${percent?'%':''}`,
      ci(targetGroup,metric,percent,digits).replace('\n',' '),
      `${gap>=0?'+':''}${gap.toFixed(digits)}${percent?'pp':''} ${gap>0?'miss':'pass'}`]);
  }
  tr.push(['Trajectory health','Conditional','Unmeasured','No validated dynamics']);
  table(s,tr,[245,145,430,332],165,420,23);
  foot(s,`FD001/XGB/v1, internal held-out: ${targetGroup.unique_engine_cycle_queries} queries / ${targetGroup.query_seed_observations} observations / ${targetGroup.engines} engines. Conditional T2 denominator is retained in the appendix.`);
  s=page(p,'Intervention horizon is an assumption',note+' Paired diagnostic scope; exact config/hashes in diagnostic_groups.');
  const kr=[['Assumed K','Engines','Validity %','T2 all %','Joint %']];
  for(const k of [1,2,3,5,10]){
    const g=e.diagnostic_groups[`FD001/xgb/v1/paired_internal_diagnostic/fast/sensitivity-horizon-K-${k}`];
    kr.push([String(k),String(g.engines),ci(g,'validity'),ci(g,'plausibility_all'),ci(g,'joint')]);
  }
  table(s,kr,[285,100,255,255,257],170,390,24);
  foot(s,'Paired FD001/XGB/v1 diagnostic population,95% engine CIs. K changes cumulative proxy-rate allowance, not observed machine dynamics.');
  s=page(p,'Latency budgets and measured gaps',note+' Historical source63,1000calls/mode,16engines. Startup/network/UIexcluded. Current post-audit source has not inherited these timings.');
  const lr=[['Mode / stage','p95 ms [engine CI]','Upper budget ms','Gap ms']];
  for(const mode of ['FAST','THOROUGH'])for(const stage of ['optimization_ms','pipeline_ms']){
    const item=e.latency.modes[mode][stage],v=item.p95_engine_ci;
    lr.push([`${mode} / ${stage.replace('_ms','')}`,`${item.p95_ms.toFixed(1)}\n[${v.lower.toFixed(1)},${v.upper.toFixed(1)}]`,String(item.upper_budget_ms),Math.max(0,item.p95_ms-item.upper_budget_ms).toFixed(1)]);
  }
  table(s,lr,[310,422,220,200],180,340,24);
  foot(s,'1,000 calls / 16 engines per mode, 95% engine CIs. UI 250 ms and full UI/network total 2200 ms are unmeasured. New standby-contaminated profiling is separate.');
  const demo=await fs.readFile(`${root}/docs/demo_script.md`,'utf8');
  for(const [label,caseId,imageName] of [['RECOVERABLE','5/241','phase10-readme-recoverable.png'],['ESCALATE','2/278','phase10-readme-escalate.png']]){
    s=page(p,`Recorded operator case: ${label}`,`Source docs/demo_script.md and docs/phase10_changes.md. ${demo.slice(demo.indexOf('## Run identity'),demo.indexOf('## 0:00'))} Transition to live dashboard using THOROUGH with the same trusted artifact; wait for the actual solve. Never label this saved screenshot as live inference.`);
    const row=demo.split('\n').find(line=>line.startsWith(`| ${caseId} |`));
    const cells=row.split('|').map(x=>x.trim());
    text(s,`Engine / cycle ${caseId}\nRisk ${cells[3]} -> ${cells[4]}\nEvidence ${cells[5]}`,68,170,420,190,31,ink,true);
    text(s,label==='RECOVERABLE'?'True model score and all proxy checks pass. The action remains decision support.':'The closest diagnostic is not an accepted action. Show the failed checks and escalation.',68,400,420,165,27);
    s.images.add({blob:new Uint8Array(await fs.readFile(`${root}/docs/screenshots/${imageName}`)),contentType:'image/png',fit:'contain',alt:`Actual saved ${label} dashboard screenshot`,position:{left:520,top:155,width:690,height:438}});
    foot(s,'Single observed case, not a population estimate. Use docs/demo_script.md for the actual live walkthrough.',
      'README walkthrough reproduce-20261026T042558162985Z | source 8aa18cb | config: phase10-reproduce-v1.yaml');
  }
  s=page(p,'Defense answers',note+' SynopsisSection12 and paper/manuscript.md Section7.');
  text(s,'Does the change reduce real-machine failure?',68,175,1140,60,32,teal,true);
  text(s,'Tier1 establishes that the calibrated model target is met. Proxy and distribution checks add evidence. Causal benefit still needs validated response data.',68,250,1120,130,29);
  text(s,'Can we claim a specific RUL-cycle extension?',68,414,1140,60,32,teal,true);
  text(s,'No. Static C-MAPSS is non-interactive. No validated transition or simulator result is available here.',68,493,1120,100,29);
  s=page(p,'SDG 9 motivation and next evidence',note+' UNtargetdefinitions: https://sdgs.un.org/goals/goal9. No officialindicator or fieldbenefit measured.');
  lines(s,[
    'SDG 9.1: reliable and resilient infrastructure. SDG 9.4: resource efficiency and sustainable upgrades.',
    'No measured lifespan, disposal or downtime benefit. A changed risk score cannot establish either target.',
    'Next: validated simulator integration, N-CMAPSS, first-principles coupling and richer actuator telemetry.'
  ],175,30);
  s=page(p,'Reproducibility and remaining limits',note+' Frozenreplay runphase11-seed1730-20261028T030707Z; configs/experiments/phase11-seed1730-replay.yaml and phase11-audit.yaml; docs/final_verification.md.');
  lines(s,[
    'Frozen replay: 34,298 queries / 64 groups. Zero mismatches against each of two historical references.',
    '576 whole-engine CI objects independently checked. Reused engines demonstrate repeatability, not fresh generalization.',
    'Historical test exposure cannot be undone. Finite reference searches remain unresolved.',
    'Installable MIT research package and dashboard. This deck and manuscript are not paper submission or field certification.'
  ],163,27);
  // Readable complete24strata supplement. Tables remain native/editable.
  for(const profile of ['FD001/xgb','FD001/mlp','FD001/lstm','FD002/xgb']){
    const all=[['Protocol / population','Q / observations / N','Validity %','T2 all %','T2 returned %']];
    const tiers=[['Protocol / population','Tier3 %','Tier4 %','Joint %','All / returned obs.']];
    for(const v of ['v1','v2'])for(const pop of ['internal_heldout','grouped_oof','official_test']){
      const g=group(e,profile,v,pop);const title=`${v}/${pop.replace('internal_heldout','held-out').replace('grouped_oof','OOF').replace('official_test','official')}`;
      all.push([title,`${g.unique_engine_cycle_queries}/${g.query_seed_observations}/${g.engines}`,ci(g,'validity'),ci(g,'plausibility_all'),ci(g,'plausibility_returned')]);
      tiers.push([`${title}\nN=${g.engines} engines`,ci(g,'tier3'),ci(g,'tier4'),ci(g,'joint'),`${g.query_seed_observations}/${g.metrics.plausibility_returned.ci.denominator}`]);
    }
    s=page(p,`${profile.toUpperCase()} | all headline populations`,note+' Fullgroupdetails in paper/evidence.json; all tier and conditionaldenominators retained.');
    table(s,all,[245,190,239,239,239],170,430,23);
    foot(s,'FAST/full, K=1, k_max=3, v1 D_max5 / v2 D_max8. 95% engine CIs. Q=unique engine/cycle, observations include five solver seeds, N=engines.');
    s=page(p,`${profile.toUpperCase()} | constraints and joint`,note);
    table(s,tiers,[245,235,235,235,202],170,430,23);
    foot(s,'Engine counts match the preceding table. Returned=nonzero action-feasible candidate, regardless of tier outcome. Failed queries remain in all-query denominators.');
  }
  return {slideCount:p.slides.items.length,tableSlides:p.slides.items.map((s,i)=>s.tables.items.length?i+1:null).filter(Boolean),source:note};
}
