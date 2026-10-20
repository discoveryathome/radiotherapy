"""Generate rays; rtpilot.certify checks them without importing this module."""
import itertools,json
from .data import ROOT,load,ANGLES,write_json,digest
from .optimize import Planner
from .evaluate import Evaluator
from .certify import check

def main():
    D,V,B=load();cfg=json.loads((ROOT/'config/research.json').read_text());pl=Planner(D,V,B,cfg);ev=Evaluator();rows=[]
    for a in itertools.combinations(ANGLES,3):
        x,info=pl.solve(a)
        if x is not None or 'farkas' not in info:raise RuntimeError(info)
        r=check(info,ev,cfg)
        if not r['verified_numerically']:raise AssertionError(r)
        rows.append({'solver':info,'independent_check':r})
        write_json(ROOT/'results/infeasibility.json',{'data_sha256':digest(ROOT/'data/manifest.json'),'config_sha256':digest(ROOT/'config/research.json'),'cases':rows,'note':'Floating-point Farkas ray checks; not formal exact certificates. Infeasibility of every 3-beam superset also rules out smaller subsets.'})
        print('Checked',a,r['contradiction_margin'],flush=True)
if __name__=='__main__':main()
