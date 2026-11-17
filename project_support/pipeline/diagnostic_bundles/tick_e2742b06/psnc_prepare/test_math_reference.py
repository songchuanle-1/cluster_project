"""Stdlib real-number reference checks; not torch, native TRAIN or resources."""
import math
import unittest


def dct(n):
    return [[(1/math.sqrt(n) if k==0 else math.sqrt(2/n)*math.cos(math.pi/n*k*(j+.5))) for j in range(n)] for k in range(n)]


def transpose(x): return [list(row) for row in zip(*x)]


def mm(x,y): return [[sum(a*b for a,b in zip(row,col)) for col in zip(*y)] for row in x]


def close(x,y,tol=1e-12): return len(x)==len(y) and all(len(a)==len(b) and all(abs(c-d)<=tol for c,d in zip(a,b)) for a,b in zip(x,y))


def apply(x,f,q=None):
    if len(x)<2: return [f(row) for row in x]
    q=dct(len(x)) if q is None else q
    b=f([0.0]*len(x[0]));z=mm(q,x)
    v=[[a-c for a,c in zip(f(row),b)] for row in z]
    return [[a+c for a,c in zip(row,b)] for row in mm(transpose(q),v)]


def nonlinear(row): return [row[0]**3+.7, math.tanh(row[1]+.2)+.1*row[0]-.4]


def affine(row): return [2*row[0]-.5*row[1]+.3, -.7*row[0]+1.1*row[1]-.8]


class ReferenceTests(unittest.TestCase):
    def test_orthogonal_sizes(self):
        for n in (1,2,3,5,8,16,64):
            self.assertTrue(close(mm(dct(n),transpose(dct(n))),[[float(i==j) for j in range(n)] for i in range(n)],1e-12))
    def test_fixed_sign_convention(self):
        self.assertTrue(all(x>0 for x in dct(5)[0]));self.assertGreater(dct(5)[1][0],0);self.assertLess(dct(5)[1][-1],0)
    def test_zero_response_preserved(self):
        for n in (2,3,8):self.assertTrue(close(apply([[0,0] for _ in range(n)],nonlinear),[nonlinear([0,0]) for _ in range(n)]))
    def test_singleton_direct(self):self.assertEqual(apply([[.6,-.2]],nonlinear),[nonlinear([.6,-.2])])
    def test_no_group(self):self.assertEqual(apply([],nonlinear),[])
    def test_affine_collapse(self):
        for n in (2,3,5,8):
            x=[[.1*i-.3,.2*i+.4] for i in range(n)];self.assertTrue(close(apply(x,affine),[affine(row) for row in x]))
    def test_nonlinear_cross_token_dependency(self):
        x=[[.6,.1],[-.2,.4],[.9,-.7]];a=apply(x,nonlinear);x[1][0]+=.00001;b=apply(x,nonlinear);self.assertGreater(abs(a[0][0]-b[0][0]),1e-8)
    def test_affine_cross_token_dependency_disappears(self):
        x=[[.6,.1],[-.2,.4],[.9,-.7]];a=apply(x,affine);x[1][0]+=.00001;b=apply(x,affine);self.assertLess(abs(a[0][0]-b[0][0]),1e-12)
    def test_mode_row_permutation_is_not_association_control(self):
        x=[[.6,.1],[-.2,.4],[.9,-.7]];q=dct(3);self.assertTrue(close(apply(x,nonlinear,q),apply(x,nonlinear,[q[2],q[0],q[1]])))
    def test_mode_sign_flip_not_generally_invariant(self):
        x=[[.6,.1],[-.2,.4],[.9,-.7]];q=dct(3);flipped=[[-a for a in q[0]],q[1],q[2]];self.assertFalse(close(apply(x,nonlinear,q),apply(x,nonlinear,flipped)))
    def test_nonzero_constant_not_claimed_preserved(self):
        x=[[.6,.1]]*3;self.assertFalse(close(apply(x,nonlinear),[nonlinear(row) for row in x]))
    def test_column_association_can_change_output(self):
        x=[[.6,.1],[-.2,.4],[.9,-.7]];q=dct(3);columns=[[row[1],row[0],row[2]] for row in q];self.assertFalse(close(apply(x,nonlinear,q),apply(x,nonlinear,columns)))
    def test_true_support_excludes_internal_empty(self):
        ids0=[0,1,1,2];ids1=[2,0,3];counts=[0]*5
        for i in ids0:counts[ids1[i]]+=1
        self.assertEqual([i for i,n in enumerate(counts) if n],[0,2,3]);self.assertEqual([i for i,n in enumerate(counts) if not n],[1,4])
    def test_parent_boundary_independent(self):
        a=[[.6,.1],[-.2,.4]];b=[[.9,-.7],[.2,.8]];before=apply(a,nonlinear);b[0][0]+=1;self.assertEqual(before,apply(a,nonlinear))
    def test_inverse_to_original_ID(self):
        ids=[4,1,3];values=[[.6,.1],[-.2,.4],[.9,-.7]];out={j:v for j,v in zip(ids,apply(values,nonlinear))};self.assertEqual(list(out),ids);self.assertNotIn(5,out)
    def test_xyz_original_ID_tie(self):
        coords=[[0,0,0],[0,0,0],[0,1,0],[1,-1,0]];self.assertEqual(sorted([3,2,1,0],key=lambda j:(*coords[j],j)),[0,1,2,3])
    def test_empty_slot_original_bias_not_in_mixing(self):
        original=[nonlinear([0,0]) for _ in range(5)];indices=[0,2,3];mixed=apply([[.2,.1],[.3,-.2],[.5,.7]],nonlinear)
        for i,v in zip(indices,mixed):original[i]=v
        self.assertEqual(original[1],nonlinear([0,0]));self.assertEqual(original[4],nonlinear([0,0]));self.assertEqual(len(original),5)

if __name__=='__main__':unittest.main()
