"""Trial: discrete MU-grid repair of the predeclared 10-MU rounding sensitivity.

A computational delivery proxy only. No aperture sequencing or machine model.
The neighborhood and MILP budget are recorded, and full evaluator is unchanged.
"""
import json,time
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from .data import ROOT,load,write_json
from .evaluate import Evaluator
from .optimize import Planner,save_plan

def main():
    start=time.perf_counter();cpu=time.process_time();D,V,B=load();ev=Evaluator();cfg=json.loads((ROOT/'config/research.json').read_text());pl=Planner(D,V,B,cfg)
    source=json.loads((ROOT/'trial/initial-comparison.json').read_text())
    base=next(r for r in source['plans'] if r['name']=='subset_0_72_144_216')
    x=np.array(json.loads((ROOT/base['path']).read_text())['fluence_mu']);angles=base['evaluation']['active_angles'];c,A,b,cols=pl.formulation(angles)
    quantum=10.;lo=np.maximum(0,np.floor(x[cols]/quantum)-2);hi=np.minimum(cfg['max_beamlet_mu']/quantum,np.ceil(x[cols]/quantum)+2)
    r=milp(c*quantum,integrality=np.ones(len(cols)),bounds=Bounds(lo,hi),constraints=LinearConstraint(A*quantum,-np.inf,b),options={'time_limit':90,'mip_rel_gap':1e-4,'presolve':True})
    info={'status':int(r.status),'message':r.message,'seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu,'quantum_mu':quantum,'neighborhood':'floor(x/10)-2 through ceil(x/10)+2, clipped to original box','mip_gap':getattr(r,'mip_gap',None),'dual_bound':getattr(r,'mip_dual_bound',None),'nodes':getattr(r,'mip_node_count',None)}
    if r.x is not None:
        xx=np.zeros(418);xx[cols]=np.rint(r.x)*quantum
        info['integrality_residual_before_projection']=float(np.abs(r.x-np.rint(r.x)).max())
        path=ROOT/'trial/quantized_plan.json';save_plan(path,xx,'research',4,info)
        result,d=ev.evaluate(path);info.update(evaluation=result,path=str(path.relative_to(ROOT)),dose_recomputation_max_error_gy=float(np.abs(d-D@xx).max()),max_grid_residual_mu=float(np.abs(xx/quantum-np.rint(xx/quantum)).max()))
    write_json(ROOT/'trial/quantized.json',info);print(json.dumps(info,indent=2),flush=True)
if __name__=='__main__':main()
