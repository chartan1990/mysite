import inspect
import pprint

from foundation.automat.parser.sorte import Latexparser


def test__contiguousLeftOvers__decimalPlaces(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = ' -0.5 + 1.0 = 0.5'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('+', 5): [('-', 3), ('1.0', 6)],
    ('-', 3): [('0', 2), ('0.5', 4)],
    ('=', 0): [('+', 5), ('0.5', 1)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__collateBackslashInfixLeftOversToContiguous__exponentialOverMultiply(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = ' 3x^{9} = 3x^{2}x^{7}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('*', 2): [('3', 1), ('^', 4)],
    ('*', 6): [('*', 2), ('^', 8)],
    ('*', 11): [('3', 10), ('^', 13)],
    ('=', 0): [('*', 11), ('*', 6)],
    ('^', 4): [('x', 3), ('2', 5)],
    ('^', 8): [('x', 7), ('7', 9)],
    ('^', 13): [('x', 12), ('9', 14)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


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
    ('cos', 7): [('x_0', 12)],
    ('sin', 5): [('x_0', 11)],
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
    ('^', 9): [(('cos', 4), ('2', 7))],
    ('^', 10): [(('sin', 2), ('2', 6))],
    ('cos', 4): [('x', 8)],
    ('sin', 2): [('x', 5)]}
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
    ('^', 9): [(('cos', 4), ('2', 5))],
    ('^', 10): [(('sin', 2), ('2', 7))],
    ('cos', 4): [('x', 6)],
    ('sin', 2): [('x', 8)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Sqrt0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sqrt{4}=2'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {('=', 0): [('nroot', 1), ('2', 2)], ('nroot', 1): [(2, 4), ('4', 3)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Sqrt1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sqrt[3]{9}=2'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {('=', 0): [('nroot', 2), ('2', 1)], ('nroot', 2): [('3', 3), ('9', 4)]}
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
    expected_ast = {   ('=', 0): [('log', 2), ('12', 1)],
    ('log', 2): [('12', 4), ('8916100448256', 3)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Log1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\log(100)=2'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {('=', 0): [('log', 1), ('2', 2)], ('log', 1): [(10, 4), ('100', 3)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__tildeVariable(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\tilde{x}=2'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {('=', 0): [('tilde', 1), ('2', 2)], ('tilde', 1): [('x', 3)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__SchrodingerWaveEquation(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\widehat{H}\\Psi=\\widehat{E}\\Psi'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('*', 2): [('widehat', 1), ('Psi', 3)],
    ('*', 5): [('widehat', 4), ('Psi', 6)],
    ('=', 0): [('*', 5), ('*', 2)],
    ('widehat', 1): [('E', 7)],
    ('widehat', 4): [('H', 8)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__infixInBackslash__paraboloid(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'z=\\sqrt{x^2+y^2}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('+', 6): [('^', 4), ('^', 8)],
    ('=', 0): [('z', 2), ('nroot', 1)],
    ('^', 4): [('x', 3), ('2', 5)],
    ('^', 8): [('y', 7), ('2', 9)],
    ('nroot', 1): [(2, 10), ('+', 6)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__sqrtWithPowerCaretRightOtherInfix__hill(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'z=-\\sqrt[2]{x^2+y^2}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('+', 8): [('^', 6), ('^', 10)],
    ('-', 2): [('0', 1), ('nroot', 3)],
    ('=', 0): [('z', 4), ('-', 2)],
    ('^', 6): [('x', 5), ('2', 7)],
    ('^', 10): [('y', 9), ('2', 11)],
    ('nroot', 3): [('2', 12), ('+', 8)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__nonInfixBrackets__addImplicitMultiply(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '(1+(1+(1+1)))(((1+1)+1)+1)=16'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__nonInfixBrackets__addImplicitMultiply0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '(1+(1+1)(1+1)+1)+1=6'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__nonInfixBrackets__addImplicitMultiply1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '((1+(1+(1+1)))(((1+1)+1)+1)+1)+1=18'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__BODMAS__priorityBetweenInfixForBrackets(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\frac{2}{(x-1)(x+1)}=c'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__BODMAS__enclosingBracketInBackslashArg(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\frac{2}{(x-1)(x+1)} = \\frac{1}{x-1} - \\frac{1}{x+1}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('*', 8): [('-', 6), ('+', 10)],
    ('+', 10): [('x', 9), ('1', 11)],
    ('+', 19): [('x', 18), ('1', 20)],
    ('-', 3): [('/', 2), ('/', 4)],
    ('-', 6): [('x', 5), ('1', 7)],
    ('-', 15): [('x', 14), ('1', 16)],
    ('/', 1): [('2', 12), ('*', 8)],
    ('/', 2): [('1', 13), ('-', 15)],
    ('/', 4): [('1', 17), ('+', 19)],
    ('=', 0): [('/', 1), ('-', 3)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__BODMAS__enclosingBracketInBackslashArgWithExponent(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'c=\\sin((x-3)^2)'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('-', 4): [('x', 3), ('3', 5)],
    ('=', 0): [('c', 2), ('sin', 1)],
    ('^', 6): [('-', 4), ('2', 7)],
    ('sin', 1): [('^', 6)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__BODMAS__enclosingBracketInBackslashArgImplicitZero(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\frac{2}{(x-1)(x+1)} = \\frac{1}{x-1} + \\frac{-1}{x+1}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('*', 8): [('-', 6), ('+', 10)],
    ('+', 3): [('/', 2), ('/', 4)],
    ('+', 10): [('x', 9), ('1', 11)],
    ('+', 21): [('x', 20), ('1', 22)],
    ('-', 6): [('x', 5), ('1', 7)],
    ('-', 15): [('x', 14), ('1', 16)],
    ('-', 18): [('0', 17), ('1', 19)],
    ('/', 1): [('2', 12), ('*', 8)],
    ('/', 2): [('1', 13), ('-', 15)],
    ('/', 4): [('-', 18), ('+', 21)],
    ('=', 0): [('/', 1), ('+', 3)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__BODMAS__enclosingBracket(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'x^2-6x+9=(x-3)^2'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('*', 11): [('6', 10), ('x', 12)],
    ('+', 13): [('-', 9), ('9', 14)],
    ('-', 2): [('x', 1), ('3', 3)],
    ('-', 9): [('^', 7), ('*', 11)],
    ('=', 0): [('+', 13), ('^', 4)],
    ('^', 4): [('-', 2), ('2', 5)],
    ('^', 7): [('x', 6), ('2', 8)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__manyFracCaretEnclosingBrac__partialFrac(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\frac{x^2}{(x-2)(x-3)^2}=\\frac{4}{x-2}+\\frac{-3}{x-3}+\\frac{9}{(x-3)^2}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('*', 13): [('-', 11), ('^', 17)],
    ('+', 3): [('/', 2), ('/', 4)],
    ('+', 5): [('+', 3), ('/', 6)],
    ('-', 11): [('x', 10), ('2', 12)],
    ('-', 15): [('x', 14), ('3', 16)],
    ('-', 21): [('x', 20), ('2', 22)],
    ('-', 24): [('x', 23), ('3', 25)],
    ('-', 29): [('0', 28), ('3', 30)],
    ('-', 33): [('x', 32), ('3', 34)],
    ('/', 1): [('^', 8), ('*', 13)],
    ('/', 2): [('4', 19), ('-', 21)],
    ('/', 4): [('-', 29), ('-', 33)],
    ('/', 6): [('9', 31), ('^', 26)],
    ('=', 0): [('/', 1), ('+', 5)],
    ('^', 8): [('x', 7), ('2', 9)],
    ('^', 17): [('-', 15), ('2', 18)],
    ('^', 26): [('-', 24), ('2', 27)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__fracWithLogNoBase__changeLogBaseFormula(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\log_{b}(a)=\\frac{\\log_{c}(a)}{\\log_{c}(b)}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   
    ('/', 1): [('log', 4), ('log', 3)],
    ('=', 0): [('log', 2), ('/', 1)],
    ('log', 2): [('b', 5), ('a', 6)],
    ('log', 3): [('c', 8), ('b', 7)],
    ('log', 4): [('c', 10), ('a', 9)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)
#need test cases where there is sqrt in sqrt as arg, 
#trig in trig as arg
#log in log as arg
#frac in frac as arg
#infix in infix with leftRightBrackets

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

    equationStr = 'Q(x) = (x^3 - 2x^2 + 5x - 7)^2 - (x - 1)^3 + 3x^{21}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = None # to be filled in
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__hassliche__nonIntegerAndNegativeCoefficientsDECIMALPOINTTEST(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'R(x) = -0.5x^{10} + 3.14x^{8} - \\frac{2}{3}x^{5} + 1.618x^{3} - \\frac{1}{x}'
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
    # test__contiguousLeftOvers__decimalPlaces()
    # test__collateBackslashInfixLeftOversToContiguous__exponentialOverMultiply()
    # test__findingBackSlashAndInfixOperations__Trig0()
    # test__findingBackSlashAndInfixOperations__Trig1()
    # test__findingBackSlashAndInfixOperations__Trig2()
    # test__findingBackSlashAndInfixOperations__Sqrt0()
    # test__findingBackSlashAndInfixOperations__Sqrt1()
    # test__findingBackSlashAndInfixOperations__Ln()
    # test__findingBackSlashAndInfixOperations__Frac()
    # test__findingBackSlashAndInfixOperations__Log0()
    # test__findingBackSlashAndInfixOperations__Log1()
    # test__findingBackSlashAndInfixOperations__tildeVariable()
    # test__findingBackSlashAndInfixOperations__SchrodingerWaveEquation()
    # test__infixInBackslash__paraboloid()
    # test__sqrtWithPowerCaretRightOtherInfix__hill()
    test__nonInfixBrackets__addImplicitMultiply(True) # not tested yet
    # test__nonInfixBrackets__addImplicitMultiply0(True) # not tested yet
    # test__nonInfixBrackets__addImplicitMultiply1(True) # not tested yet
    # test__BODMAS__priorityBetweenInfixForBrackets(True) # not tested yet
    # test__BODMAS__enclosingBracketInBackslashArg(True) # not tested yet
    # test__BODMAS__enclosingBracketInBackslashArgWithExponent(True) # not tested yet
    # test__BODMAS__enclosingBracketInBackslashArgImplicitZero(True) # not tested yet
    # test__BODMAS__enclosingBracket(True) # not tested yet
    # test__manyFracCaretEnclosingBrac__partialFrac() # not tested yet
    # test__fracWithLogNoBase__changeLogBaseFormula() # not tested yet
    # test__hassliche__highPowersAndRandomCoefficientsPITEST(True)  # not tested yet
    # test__hassliche__nestedPolynomial(True) # not tested yet
    # test__hassliche__nonIntegerAndNegativeCoefficientsDECIMALPOINTTEST(True) # not tested yet
    # test__hassliche__mixedVariablesAndPowersPOWERCOTEVARIABLEDOUBLEVARIABLETEST(True) # not tested yet
    # test__hassliche__irrationalAndTranscendentalNumbersPOWERCOTEBACKSLASH(True) # not tested yet
    # test__hassliche__degree5(True) # not tested yet
    # test__hassliche__degree6(True) # not tested yet
    # test__hassliche__degree7(True) # not tested yet
    # test__hassliche__moreThanOneAdditiveTermInEachMultiplicativeTerm(True) # not tested yet
    # test__hassliche__moreThanOneAdditiveTermInEachMultiplicativeTerm0(True) # not tested yet
    # test__hassliche__moreThanOneAdditiveTermInEachMultiplicativeTerm1(True) # not tested yet
    # test__paveWayForDifferentiation__productRule(True) # not tested yet
    # test__paveWayForDifferentiation__sumRule(True) # not tested yet
    # test__paveWayForIntegration__enclosingBracketNonBackslash(True) # not tested yet
    # test__paveWayForIntegrtion__exponentOnEnclosingNonBackslash(True) # not tested yet