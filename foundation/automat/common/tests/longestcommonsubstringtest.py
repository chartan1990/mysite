import inspect
import pprint

from foundation.automat.common.longestcommonsubstring import LongestCommonSubString

pp = pprint.PrettyPrinter(indent=4)

def test__oneTermFactorization__formulaContainedInAnotherFormula(verbose=False):
    schemeFormula0 = '(+ x 1)'
    schemeFormula1 = '(* (+ x 1) (- x 1))'
    commonSubstring = LongestCommonSubString.lcs(schemeFormula0, schemeFormula1)
    expected = '(+ x 1)'
    print('PASSED? ', commonSubstring == expected)
    if verbose:
        print(commonSubstring)


def test__oneTermFactorization__otherDirectionContainment(verbose=False):
    schemeFormula0 = '(* (+ x 1) (- x 1))'
    schemeFormula1 = '(+ x 1)'
    commonSubstring = LongestCommonSubString.lcs(schemeFormula0, schemeFormula1)
    expected = '(+ x 1)'
    print('PASSED? ', commonSubstring == expected)
    if verbose:
        print(commonSubstring)


if __name__=='__main__':
    test__oneTermFactorization__formulaContainedInAnotherFormula()
    test__oneTermFactorization__otherDirectionContainment()