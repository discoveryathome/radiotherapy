"""Monotone discrete 10-MU coordinate / pair-exchange search, fixed dose limits."""
import json,time,argparse
import numpy as np
from .data import ROOT,load,write_json
from .evaluate import Evaluator
from .optimize import Planner,save_plan

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--steps',type=int,default=80);ap.add_argument('--mode',choices=['pairs','decrement'],default='pairs');ap.add_argument('--name',default='quantized-local');args=ap.parse_args()
    start=time.perf_counter();cpu=time.process_time();D,V,B=load();ev=Evaluator();cfg=json.loads((ROOT/'config/research.json').read_text());pl=Planner(D,V,B,cfg)
    source=json.loads((ROOT/'trial/rounding/comparison.json').read_text())
    candidates=[r for r in source['plans'] if len(r['angles'])==4 and r.get('evaluation',{}).get('feasible')]
    base=min(candidates,key=lambda r:r['evaluation']['objective_gy']);plan=json.loads((ROOT/base['path']).read_text());x=np.array(plan['fluence_mu']);q=10.
    c,A,b,cols=pl.formulation(base['angles']);AA=A.toarray();y=x[cols].copy();slack=b-AA@y;history=[{'step':0,'objective_gy':float(c@y),'kind':'start'}]
    # Per-step work is bounded: try all single decrements, then best admissible
    # cheap pair exchanges. Every original linear constraint is checked.
    for step in range(1,args.steps+1):
        if time.perf_counter()-start>90:break
        best=None;best_gain=1e-10
        removals=np.flatnonzero(y>=q)
        for j in removals:
            delta=-q*AA[:,j];gain=q*c[j]
            if gain>best_gain and np.all(delta<=slack+1e-8):best=(j,None,delta);best_gain=gain
        if best is None and args.mode=='pairs':
            for j in removals[np.argsort(-c[removals])]:
                need=slack+q*AA[:,j]
                # Only target-lower rows go negative on a decrement. They provide
                # an inexpensive necessary filter before testing complete vectors.
                deficit=np.flatnonzero(need < -1e-8)
                adds=np.flatnonzero((y<=cfg['max_beamlet_mu']-q)&(c<c[j]-best_gain/q))
                if len(deficit) and len(adds):adds=adds[np.all(q*AA[np.ix_(deficit,adds)]<=need[deficit,None]+1e-8,axis=0)]
                for k in adds[np.argsort(c[adds])]:
                    delta=q*(AA[:,k]-AA[:,j]);gain=q*(c[j]-c[k])
                    if gain>best_gain and np.all(delta<=slack+1e-8):best=(j,k,delta);best_gain=gain
        if best is None:break
        j,k,delta=best;y[j]-=q
        if k is not None:y[k]+=q
        slack-=delta
        # Recompute instead of relying on accumulated slack arithmetic.
        slack=b-AA@y
        history.append({'step':step,'objective_gy':float(c@y),'kind':'decrement' if k is None else 'exchange','remove_column':int(cols[j]),'add_column':None if k is None else int(cols[k]),'max_constraint_violation':float(max(0,-slack.min()))})
    xx=np.zeros(418);xx[cols]=y;path=ROOT/f'trial/{args.name}_plan.json'
    save_plan(path,xx,'research',4,{'method':'monotone 10-MU coordinate and pair exchange','steps':len(history)-1,'start':base['path']})
    r,d=ev.evaluate(path)
    result={'path':str(path.relative_to(ROOT)),'start':base['path'],'history':history,'evaluation':r,'dose_recomputation_max_error_gy':float(np.abs(d-D@xx).max()),'grid_residual_mu':float(np.abs(xx/q-np.rint(xx/q)).max()),'seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu,'mode':args.mode,'step_budget':args.steps,'stopping_note':'Bounded heuristic; no global discrete-optimality claim.'}
    result['output_gain_sensitivity']=[{'gain':g,'evaluation':ev.assess(xx,ev.dose(xx*g),cfg,4)} for g in cfg['sensitivity']['output_gains']]
    write_json(ROOT/f'trial/{args.name}.json',result);print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
