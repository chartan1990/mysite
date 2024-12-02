import inspect
import pprint

from foundation.automat.core.equation import Equation


def test__onetermFactorisation__cutSubtreeAtRoot(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)


    eq0 = Equation('(= z (+ (* 2 a) (+ (* 2 b) (+ (* 2 c) (+ (* 2 d) (+ (* 2 e) (+ (* 2 f) (+ (* 2 g) (+ (* 2 h) (+ (* 2 i) (+ (* 2 j) (* 2 k))))))))))))', 'scheme')
    rootNode = None
    for nonLeaf in eq0.ast.keys():
        if str(nonLeaf[0]) == '2':
            rootNode = nonLeaf
            break
    subTree = eq0._cutSubASTAtRoot(rootNode) # need to find a rootNode (with the rightID)
    if verbose:
        pp.pprint(subTree)


def test__onetermFactorisation__cutSubtreeAtRoot0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)


    eq0 = Equation('(= z (+ (* (sin (* (+ x 1) (- x 1))) a) (+ (* (sin (* (+ x 1) (- x 1))) b) (+ (* (sin (* (+ x 1) (- x 1))) c) (+ (* (sin (* (+ x 1) (- x 1))) d) (+ (* (sin (* (+ x 1) (- x 1))) e) (+ (* (sin (* (+ x 1) (- x 1))) f) (+ (* (sin (* (+ x 1) (- x 1))) g) (+ (* (sin (* (+ x 1) (- x 1))) h) (+ (* (sin (* (+ x 1) (- x 1))) i) (+ (* (sin (* (+ x 1) (- x 1))) j) (* (sin (* (+ x 1) (- x 1))) k))))))))))))', 'scheme')
    rootNode = None
    for nonLeaf in eq0.ast.keys():
        if str(nonLeaf[0]) == 'sin':
            rootNode = nonLeaf
            break
    subTree = eq0._cutSubASTAtRoot(rootNode) # need to find a rootNode (with the rightID)
    if verbose:
        pp.pprint(subTree) # we are expecting the AST of (sin (* (+ x 1) (- x 1)))


if __name__=='__main__':
    test__onetermFactorisation__cutSubtreeAtRoot()
    test__onetermFactorisation__cutSubtreeAtRoot0()