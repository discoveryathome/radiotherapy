import unittest
import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from rtpilot.adaptive import solve as adaptive
from rtpilot.conic import solve as conic
from rtpilot.warm import solve as warm

class SolverTests(unittest.TestCase):
    def test_known_lp(self):
        A=sparse.csr_matrix([[-1.,-1.],[1.,0.],[0.,1.]])
        b=np.array([-1.,.8,.8]);c=np.array([1.,2.])
        for solver in (adaptive,conic,warm):
            x,info=solver(c,A,b,2.)
            self.assertIsNotNone(x,info)
            self.assertLess(abs(c@x-1.2),1e-6)
            self.assertLess(abs(info['numerical_duality_gap']),1e-6)
            self.assertLess((A@x-b).max(),1e-6)
    def test_warm_vector_bounds(self):
        x,info=warm(np.array([1.,2.]),sparse.csr_matrix([[-1.,-1.]]),np.array([-1.]),np.array([.8,.4]))
        self.assertIsNotNone(x,info)
        self.assertAlmostEqual(x[0]+2*x[1],1.2,places=6)

    def test_infeasible(self):
        A=sparse.csr_matrix([[-1.],[1.]])
        b=np.array([-2.,1.]);c=np.ones(1)
        for solver in (adaptive,conic,warm):
            x,info=solver(c,A,b,3.)
            self.assertIsNone(x)
            self.assertEqual(info['status'],2)
    def test_adaptive_separates_unseen_constraints(self):
        # Initial endpoints omit the interior binding constraint.
        A=sparse.csr_matrix(-np.ones((201,1)));b=-np.ones(201);b[97]=-2.
        x,info=adaptive(np.ones(1),A,b,3.,initial_rows=2,add_rows=1)
        self.assertAlmostEqual(x[0],2.,places=6)
        self.assertGreater(len(info['history']),1)
        self.assertLess(info['final_rows'],info['full_rows'])

if __name__=='__main__': unittest.main()
