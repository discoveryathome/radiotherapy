"""Contributor experiment: stricter DVH goals with explicit voxel exemptions.

The frozen research constraints remain in force. The additional TG119 reference
metric gate is checked by the unchanged independent evaluator. This is an active-set
heuristic; no global optimum or machine deliverability claim follows.
"""
import argparse
import itertools
import json
import time
from pathlib import Path
import numpy as np
from scipy import sparse
from .data import ROOT,load,ANGLES,write_json
from .evaluate import Evaluator
from .optimize import Planner,save_plan
from .warm import solve

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',default='results/comparison.json');ap.add_argument('--out',default='trial/dvh');ap.add_argument('--max-sets',type=int,default=4);args=ap.parse_args()
    start=time.perf_counter();cpu=time.process_time();folder=ROOT/args.out;folder.mkdir(parents=True,exist_ok=True)
    D,V,B=load();ev=Evaluator();cfg=json.loads((ROOT/'config/research.json').read_text());pl=Planner(D,V,B,cfg)
    source=json.loads((ROOT/args.source).read_text());eligible=[r for r in source['plans'] if r['profile']=='research' and r['name'].startswith('subset') and r['evaluation']['feasible']]
    eligible.sort(key=lambda r:(r['evaluation']['beam_budget']!=3,r['evaluation']['objective_gy']))
    rows=[]
    for base in eligible[:args.max_sets]:
        bp=json.loads((ROOT/base['path']).read_text());x=np.array(bp['fluence_mu']);angles=base['evaluation']['active_angles'];budget=base['evaluation']['beam_budget']
        c,A,b,cols=pl.formulation(angles)
        # Compare a stronger, entirely convex all-voxel surrogate against the
        # nonconvex permitted-hot-volume active-set heuristic.
        for strategy in ['all_voxel_caps','hot_voxel_exemptions']:
            xx=x.copy();best=None
            for iteration in range(1 if strategy=='all_voxel_caps' else 5):
                target=(pl.T@xx);core=(pl.C@xx)
                if strategy=='all_voxel_caps': ti=np.arange(len(target));ci=np.arange(len(core))
                else:
                    nt=int(np.ceil(.10*len(target)))-1;nc=int(np.ceil(.05*len(core)))-1
                    ti=np.argsort(target,kind='stable')[:len(target)-nt]
                    ci=np.argsort(core,kind='stable')[:len(core)-nc]
                AA=sparse.vstack([A,pl.T[ti][:,cols],pl.C[ci][:,cols]],format='csr')
                # Small interior margin avoids order-statistic boundary ambiguity.
                bb=np.r_[b,np.full(len(ti),55.-1e-5),np.full(len(ci),25.-1e-5)]
                y,info=solve(c,AA,bb,cfg['max_beamlet_mu'],time_limit=90)
                item={'base':base['name'],'strategy':strategy,'iteration':iteration,'optimizer':info}
                if y is None:
                    rows.append(item);print(base['name'],strategy,'status',info['status'],flush=True);break
                xx=np.zeros(418);xx[cols]=y
                name=f"{base['name']}_{strategy}_{iteration}";path=folder/f'{name}.json';save_plan(path,xx,'research',budget,info)
                e,d=ev.evaluate(path);item.update(path=str(path.relative_to(ROOT)),evaluation=e,dose_recomputation_max_error_gy=float(np.max(np.abs(d-D@xx))))
                rows.append(item);write_json(folder/'comparison.json',{'plans':rows,'elapsed_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu})
                print(name,'feasible',e['feasible'],'reference goals',e['tg119_reference_goals_pass'],'objective',e['objective_gy'],flush=True)
                if best is not None and abs(best-e['objective_gy'])<1e-7:break
                best=e['objective_gy']
    write_json(folder/'comparison.json',{'plans':rows,'elapsed_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu})
if __name__=='__main__':main()
