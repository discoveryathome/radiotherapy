"""Separate five-beam global-gain comparison when four-beam robustness fails."""
import json
from .data import ROOT,load,write_json,ANGLES
from .evaluate import Evaluator
from .optimize import Planner,save_plan

def main():
    D,V,B=load();ev=Evaluator();cfg=json.loads((ROOT/'config/research.json').read_text());pl=Planner(D,V,B,cfg)
    gains=cfg['sensitivity']['robust_training_gains'];x,info=pl.solve(ANGLES,gains=tuple(gains));out={'optimizer':info,'scenario_note':'Synthetic global output gains only; not setup/anatomy robustness.'}
    if x is not None:
        path=ROOT/'results/plans/robust_five.json';save_plan(path,x,'research',5,info)
        result,d=ev.evaluate(path);out.update(path=str(path.relative_to(ROOT)),evaluation=result,dose_recomputation_max_error_gy=float(abs(d-D@x).max()),scenarios=[])
        for g in cfg['sensitivity']['output_gains']:
            out['scenarios'].append({'gain':g,'evaluation':ev.assess(x,ev.dose(g*x),cfg,5)})
    write_json(ROOT/'results/robust-five.json',out);print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':main()
