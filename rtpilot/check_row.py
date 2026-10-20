"""Frontier row contract: enforce beam budget, MU grid, and gain-model identity."""
import argparse,json
import numpy as np
from .evaluate import Evaluator

def main():
    ap=argparse.ArgumentParser();ap.add_argument('plan');ap.add_argument('--expected-score',type=float);ap.add_argument('--beams',type=int,required=True);ap.add_argument('--quantum',type=float,required=True);ap.add_argument('--gain-min',type=float,default=1.);ap.add_argument('--gain-max',type=float,default=1.);args=ap.parse_args()
    if not 1<=args.beams<=5 or not np.isfinite([args.quantum,args.gain_min,args.gain_max]).all() or args.quantum<0 or not 0<args.gain_min<=args.gain_max:raise ValueError('Invalid benchmark row')
    ev=Evaluator();p,x,d,cfg=ev.read_plan(args.plan)
    if p['profile']!='research':raise ValueError('Wrong planning profile')
    score=ev.assess(x,d,cfg,args.beams)['objective_gy']
    if args.expected_score is not None and (not np.isfinite(args.expected_score) or abs(score-args.expected_score)>1e-7):raise ValueError('Claimed score mismatch')
    if p['beam_budget']!=args.beams:raise ValueError('Wrong beam-budget category')
    if args.quantum and np.abs(x/args.quantum-np.rint(x/args.quantum)).max()>1e-9:raise ValueError('Fluence is off the required grid')
    for gain in sorted(set([1.,args.gain_min,args.gain_max])):
        r=ev.assess(x,ev.dose(x*gain) if gain!=1 else d,cfg,args.beams)
        if not r['feasible']:raise ValueError('Infeasible at required output gain '+str(gain))
    print(json.dumps({'valid':True,'beam_budget':args.beams,'quantum_mu':args.quantum,'gain_interval':[args.gain_min,args.gain_max],'nominal_objective_gy':ev.assess(x,d,cfg,args.beams)['objective_gy']}))
if __name__=='__main__':main()
