"""Replay all saved trial witnesses without running contributor search code."""
import json
import numpy as np
from .evaluate import Evaluator,ROOT
from .verify import assert_equivalent

def main():
    ev=Evaluator();count=0
    reports=list((ROOT/'trial').glob('*/comparison.json'))
    reports += [ROOT/'trial'/n for n in ['quantized-local.json','decrement-only.json','extended-pairs.json','quantized.json'] if (ROOT/'trial'/n).exists()]
    for report in reports:
        doc=json.loads(report.read_text());rows=doc.get('plans',[doc])
        for row in rows:
            if 'path' not in row or 'evaluation' not in row:continue
            e,d=ev.evaluate(ROOT/row['path']);old=row['evaluation']
            assert_equivalent(e,old)
            if e['feasible']!=old['feasible'] or e['tg119_reference_goals_pass']!=old['tg119_reference_goals_pass'] or abs(e['objective_gy']-old['objective_gy'])>1e-7:
                raise AssertionError('Trial witness mismatch: '+row['path'])
            for structure,metrics in e['metrics'].items():
                for key,value in metrics.items():
                    if abs(value-old['metrics'][structure][key])>1e-7:raise AssertionError('Trial metric mismatch')
            if 'rounding' in row['path'] or report.name in ['quantized-local.json','decrement-only.json','extended-pairs.json','quantized.json']:
                p=json.loads((ROOT/row['path']).read_text());x=np.array(p['fluence_mu'])
                if np.max(np.abs(x/10-np.rint(x/10)))>1e-9:raise AssertionError('Not on the 10-MU grid')
            for sc in row.get('output_gain_sensitivity',[]):
                p,x,_,cfg=ev.read_plan(ROOT/row['path'])
                if sc['gain'] not in cfg['sensitivity']['output_gains']:raise AssertionError('Unexpected trial gain')
                assert_equivalent(ev.assess(x,ev.dose(x*sc['gain']),cfg,p['beam_budget']),sc['evaluation'])
            count+=1
    if count<1:raise AssertionError('No trial witnesses')
    print(f'PASS independent dose, metrics, feasibility and grid checks for {count} trial witnesses')
if __name__=='__main__':main()
