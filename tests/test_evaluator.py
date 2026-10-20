"""Hand-computed metrics, source controls, and adversarial candidate rejection."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from rtpilot.evaluate import Evaluator,dose_metrics,ANGLES,sha,ROOT
from rtpilot.verify import controls

class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ev=Evaluator()
        cls.x=np.concatenate([loadmat(ROOT/f'data/raw/Gantry{a}_Couch0_beamletSol.mat')['beamx'].ravel() for a in ANGLES])
        cls.d=cls.ev.dose(cls.x)
        cls.cfg=json.loads((ROOT/'config/paper.json').read_text())

    def test_hand_calculated_metrics(self):
        m=dose_metrics(np.arange(1,101),50)
        self.assertEqual(m['D95_gy'],6)
        self.assertEqual(m['D5_gy'],96)
        self.assertEqual(m['mean_gy'],50.5)
        self.assertEqual(m['V100_pct'],51)

    def test_source_controls(self): controls(self.ev)
    def test_bad_shape_and_nonfinite(self):
        for x in [np.ones(417),np.full(418,np.nan),np.full(418,np.inf)]:
            with self.assertRaises(ValueError): self.ev.dose(x)
    def test_bad_schema_pins_and_angle_order(self):
        p={'schema':'cort-plan/v1','profile':'paper','config_sha256':sha(ROOT/'config/paper.json'),
           'data_sha256':sha(ROOT/'data/manifest.json'),'angles':list(ANGLES),'beam_budget':5,'fluence_mu':self.x.tolist()}
        with tempfile.TemporaryDirectory(dir=ROOT/'results') as tmp:
            for key,value in [('config_sha256','0'*64),('data_sha256','0'*64),('schema','bad'),('angles',list(reversed(ANGLES))),('beam_budget',6)]:
                q=dict(p);q[key]=value;path=Path(tmp)/'bad.json';path.write_text(json.dumps(q))
                with self.assertRaises(ValueError):self.ev.read_plan(path)
    def test_zero_fluence_rejected(self):
        r=self.ev.assess(np.zeros(418),np.zeros_like(self.d),self.cfg,5)
        self.assertFalse(r['feasible'])
    def test_low_dose_rejected(self):
        self.assertFalse(self.ev.assess(.99*self.x,.99*self.d,self.cfg,5)['feasible'])
    def test_overdose_rejected(self):
        self.assertFalse(self.ev.assess(2*self.x,2*self.d,self.cfg,5)['feasible'])
    def test_beam_budget_rejected(self):
        self.assertFalse(self.ev.assess(self.x,self.d,self.cfg,3)['feasible'])
    def test_negative_fluence_rejected(self):
        x=self.x.copy();x[0]=-1
        self.assertFalse(self.ev.assess(x,self.d,self.cfg,5)['feasible'])
    def test_index_geometry(self):
        # AP changes fastest, LR next, SI slowest (CORT Figure 5).
        for v in [0,166,167,167*167,3597680]:
            ap=v%167;lr=(v//167)%167;si=v//(167*167)
            self.assertEqual(np.ravel_multi_index((ap,lr,si),(167,167,129),order='F'),v)

if __name__=='__main__':unittest.main()
