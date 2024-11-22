import inspect
import pprint

from foundation.automat.parser.sorte import Latexparser


def test__findingBackSlashAndInfixOperations__Trig0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '-\\sin( 2x_0 ) = -2\\sin(x_0)\\cos(x_0)'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('*', 4): [('2', 3), ('sin', 5)],
    ('*', 6): [('*', 4), ('cos', 7)],
    ('*', 14): [('2', 13), ('x_0', 15)],
    ('-', 2): [('0', 1), ('*', 6)],
    ('-', 9): [('0', 8), ('sin', 10)],
    ('=', 0): [('-', 9), ('-', 2)],
    ('cos', 7): [('x_0', 11)],
    ('sin', 5): [('x_0', 12)],
    ('sin', 10): [('*', 14)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast) # rename ast to latex_ast 


def test__findingBackSlashAndInfixOperations__Trig1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sin^2(x) + \\cos^2(x)=1'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('+', 3): [('^', 10), ('^', 9)],
    ('=', 0): [('+', 3), ('1', 1)],
    ('^', 9): [(('cos', 4), ('2', 6))],
    ('^', 10): [(('sin', 2), ('2', 8))],
    ('cos', 4): [('x', 5)],
    ('sin', 2): [('x', 7)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Trig2(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sin^{2}(x)+\\cos^{2}(x)=1'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('+', 3): [('^', 10), ('^', 9)],
    ('=', 0): [('+', 3), ('1', 1)],
    ('^', 9): [(('cos', 4), ('2', 6))],
    ('^', 10): [(('sin', 2), ('2', 8))],
    ('cos', 4): [('x', 5)],
    ('sin', 2): [('x', 7)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Sqrt0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sqrt(4)=2'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {('=', 0): [('nroot', 1), ('2', 2)], ('nroot', 1): [(2, 4), ('4', 3)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Sqrt1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sqrt[3](9)=2'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {('=', 0): [('nroot', 2), ('2', 1)], ('nroot', 2): [('3', 4), ('9', 3)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Ln(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\ln(e)=1'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {('=', 0): [('log', 2), ('1', 1)], ('log', 2): [('e', 4), ('e', 3)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Frac(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\frac{12}{24}=\\frac{1000}{2000}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('/', 1): [('1000', 4), ('2000', 3)],
    ('/', 2): [('12', 6), ('24', 5)],
    ('=', 0): [('/', 2), ('/', 1)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Log0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\log_{12}(8916100448256)=12'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {
    ('=', 0): [('log', 4), ('12', 3)],
    ('log', 4): [('12', 1), ('8916100448256', 2)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Log1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\log(100)=2'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {('=', 0): [('log', 4), ('2', 2)], ('log', 4): [(10, 3), ('100', 1)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__tildeVariable(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\tilde{x}=2'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {('=', 0): [('tilde', 3), ('2', 2)], ('tilde', 3): [('x', 1)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__SchrodingerWaveEquation(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\widehat{H}\\Psi=\\widehat{E}\\Psi'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('*', 4): [('widehat', 3), ('Psi', 5)],
    ('*', 7): [('widehat', 6), ('Psi', 8)],
    ('=', 0): [('*', 4), ('*', 7)],
    ('widehat', 3): [('H', 1)],
    ('widehat', 6): [('E', 2)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__infixInBackslash__paraboloid(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'z=\\sqrt(x^2+y^2)'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('+', 5): [('^', 3), ('^', 7)],
    ('=', 0): [('z', 1), ('sqrt', 10)],
    ('^', 3): [('x', 2), ('2', 4)],
    ('^', 7): [('y', 6), ('2', 8)],
    ('sqrt', 10): [(2, 9), ('+', 5)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__sqrtWithPowerCaretRightOtherInfix__hill(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'z=-\\sqrt[2](x^2+y^2)'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('+', 6): [('^', 4), ('^', 8)],
    ('-', 11): [('0', 10), ('sqrt', 12)],
    ('=', 0): [('z', 1), ('-', 11)],
    ('^', 4): [('x', 3), ('2', 5)],
    ('^', 8): [('y', 7), ('2', 9)],
    ('sqrt', 12): [('2', 2), ('+', 6)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__manyFracCaretEnclosingBrac__partialFrac(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\frac{x^2}{(x-2)(x-3)^2}=\\frac{4}{x-2}+\\frac{-3}{x-3}+\\frac{9}{(x-3)^2}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   
    ('*', 9): [('2', 8), ('x', 10)],
    ('+', 30): [('frac', 29), ('frac', 31)],
    ('+', 32): [('+', 30), ('frac', 33)],
    ('-', 7): [('x', 6), ('*', 9)],
    ('-', 11): [('-', 7), ('^', 13)],
    ('-', 16): [('x', 15), ('2', 17)],
    ('-', 19): [('0', 18), ('3', 20)],
    ('-', 22): [('x', 21), ('3', 23)],
    ('-', 25): [('x', 24), ('^', 27)],
    ('=', 0): [('frac', 34), ('+', 32)],
    ('^', 4): [('x', 3), ('2', 5)],
    ('^', 13): [('3', 12), ('2', 14)],
    ('^', 27): [('3', 26), ('2', 28)],
    ('frac', 29): [('4', 1), ('-', 16)],
    ('frac', 31): [('-', 19), ('-', 22)],
    ('frac', 33): [('9', 2), ('-', 25)],
    ('frac', 34): [('^', 4), ('-', 11)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__fracWithLogNoBase__changeLogBaseFormula(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\log_{b}(a)=\\frac{\\log_{c}(a)}{\\log_{c}(b)}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__hassliche__highPowersAndRandomCoefficientsPITEST(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'P(x) = 7x^{13} - 3x^{9} + 5x^{8} - \\sqrt{2}x^{4} + \\pi x^{2} - 42'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__hassliche__nestedPolynomial(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'Q(x) = (x^3 - 2x^2 + 5x - 7)^2 - (x - 1)^3 + 3x'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__hassliche__nonIntegerAndNegativeCoefficientsDECIMALPOINTTEST(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'R(x) = -0.5x^{10} + 3.14x^{8} - \frac{2}{3}x^{5} + 1.618x^{3} - \frac{1}{x}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__hassliche__mixedVariablesAndPowersPOWERCOTEVARIABLEDOUBLEVARIABLETEST(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'S(x, y) = x^5y^4 - 7x^3y^2 + 2x^2 - y^3 + x^2y - 4'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__hassliche__irrationalAndTranscendentalNumbersPOWERCOTEBACKSLASH(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'T(x) = e^{x} - \\cos(x)x^4 + x^3\\sin(x) - \\ln(x^2+1)'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__hassliche__degree5(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '(x - 1)(x + 2)(x - 3)(x + 4)(x - 5) = x^5 - 3x^4 - 32x^3 + 94x^2 + 31x - 120'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__hassliche__degree6(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '(x - 1)(x - 2)(x + 3)(x + 4)(x - 5)(x + 6) = x^6 + 5x^5 - 35x^4 - 75x^3 + 368x^2 + 246x - 720'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__hassliche__degree7(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '(x - 1)(x + 2)(x - 3)(x + 4)(x - 5)(x + 6)(x - 7) = x^7 + 4x^6 - 37x^5 - 58x^4 + 520x^3 + 201x^2 - 2156x + 5040'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__hassliche__moreThanOneAdditiveTermInEachMultiplicativeTerm(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '((x + 2x^2 - 3)^2)((x^2 - x + 1)^3)((x^3 + 2x - 5)) = x^{10} + 4x^9 - 2x^8 - 41x^7 - 69x^6 + 142x^5 + 420x^4 - 567x^3 - 174x^2 + 185x - 75'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__hassliche__moreThanOneAdditiveTermInEachMultiplicativeTerm0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '((x^2 + x - 1)^2)((x^3 - 2x + 4)^2)((x^2 + 3x - 7)) = x^{10} - 3x^9 - 20x^8 + 60x^7 + 161x^6 - 260x^5 - 385x^4 + 494x^3 + 509x^2 - 378x + 196'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__hassliche__moreThanOneAdditiveTermInEachMultiplicativeTerm1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '((x^2 + 2x^3 - 4)^3)((x^2 - x + 2)^2)((x^3 + 3x - 5)) = x^{15} + 8x^{14} - 14x^{13} - 191x^{12} + 48x^{11} + 1218x^{10} - 60x^9 - 2700x^8 - 1452x^7 + 4375x^6 + 3476x^5 - 2922x^4 - 1685x^3 + 655x^2 + 103x - 400'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


#need test cases where there is sqrt in sqrt as arg, 
#trig in trig as arg
#log in log as arg
#frac in frac as arg

#
def test__paveWayForDifferentiation__productRule(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\frac{d}{dx}uv=u\\frac{dv}{dx}+v\\frac{du}{dx}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__paveWayForDifferentiation__sumRule(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\frac{d}{dx}(u+v)=\\frac{du}{dx}+\\frac{dv}{dx}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)
#

def test__paveWayForIntegration__enclosingBracketNonBackslash(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\int{(x-3)(x+1)}dx=\\frac{1}{3}x^3-3x^2-3x+C'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__paveWayForIntegrtion__exponentOnEnclosingNonBackslash(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\int{(x-1)(x+1)^2}dx=\\frac{1}{4}x^4+\\frac{1}{3}x^3-\\frac{1}{2}x^2-x+C'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


if __name__=='__main__':
    # test__findingBackSlashAndInfixOperations__Trig0()
    # test__findingBackSlashAndInfixOperations__Trig1()
    # test__findingBackSlashAndInfixOperations__Trig2()
    # test__findingBackSlashAndInfixOperations__Sqrt0()
    # test__findingBackSlashAndInfixOperations__Sqrt1()
    # test__findingBackSlashAndInfixOperations__Ln()
    # test__findingBackSlashAndInfixOperations__Frac()
    test__findingBackSlashAndInfixOperations__Log0(True)
    # test__findingBackSlashAndInfixOperations__Log1(True)
    # test__findingBackSlashAndInfixOperations__tildeVariable(True)
    # test__findingBackSlashAndInfixOperations__SchrodingerWaveEquation(True)
    # test__infixInBackslash__paraboloid(True)
    # test__sqrtWithPowerCaretRightOtherInfix__hill(True)
    # test__manyFracCaretEnclosingBrac__partialFrac(True) # not tested yet
    # test__fracWithLogNoBase__changeLogBaseFormula(True) # not tested yet
    # test__hassliche__highPowersAndRandomCoefficientsPITEST(True)  # not tested yet
    # test__hassliche__nestedPolynomial() # not tested yet
    # test__hassliche__nonIntegerAndNegativeCoefficientsDECIMALPOINTTEST() # not tested yet
    # test__hassliche__mixedVariablesAndPowersPOWERCOTEVARIABLEDOUBLEVARIABLETEST() # not tested yet
    # test__hassliche__irrationalAndTranscendentalNumbersPOWERCOTEBACKSLASH() # not tested yet
    # test__hassliche__degree5() # not tested yet
    # test__hassliche__degree6() # not tested yet
    # test__hassliche__degree7() # not tested yet
    # test__hassliche__moreThanOneAdditiveTermInEachMultiplicativeTerm() # not tested yet
    # test__hassliche__moreThanOneAdditiveTermInEachMultiplicativeTerm0() # not tested yet
    # test__hassliche__moreThanOneAdditiveTermInEachMultiplicativeTerm1() # not tested yet
    # test__paveWayForDifferentiation__productRule() # not tested yet
    # test__paveWayForDifferentiation__sumRule() # not tested yet
    # test__paveWayForIntegration__enclosingBracketNonBackslash() # not tested yet
    # test__paveWayForIntegrtion__exponentOnEnclosingNonBackslash() # not tested yet