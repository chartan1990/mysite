import inspect
import pprint

from foundation.automat.parser.sorte import Latexparser


def test__findingBackSlashAndInfixOperations__Trig0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '-\\sin( 2x_0 ) = -2\\sin(x_0)\\cos(x_0)'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('*', 4): [('2', 3), ('x_0', 5)],
    ('*', 9): [('2', 8), ('sin', 10)],
    ('*', 11): [('*', 9), ('cos', 12)],
    ('-', 7): [('0', 6), ('*', 11)],
    ('-', 14): [('0', 13), ('sin', 15)],
    ('=', 0): [('-', 14), ('-', 7)],
    ('cos', 12): [('x_0', 2)],
    ('sin', 10): [('x_0', 1)],
    ('sin', 15): [('*', 4)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast) # rename ast to latex_ast 


def test__findingBackSlashAndInfixOperations__Trig1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sin^2(x) + \\cos^2(x)=1'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('+', 8): [('^', 6), ('^', 9)],
    ('=', 0): [('+', 8), ('1', 5)],
    ('^', 6): [('sin', 7), ('2', 1)],
    ('^', 9): [('cos', 10), ('2', 3)],
    ('cos', 10): [('x', 4)],
    ('sin', 7): [('x', 2)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Trig2(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sin^{2}(x)+\\cos^{2}(x)=1'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('+', 8): [('^', 6), ('^', 9)],
    ('=', 0): [('+', 8), ('1', 5)],
    ('^', 6): [('sin', 7), ('2', 1)],
    ('^', 9): [('cos', 10), ('2', 3)],
    ('cos', 10): [('x', 4)],
    ('sin', 7): [('x', 2)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Sqrt0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sqrt(4)=2'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {('=', 0): [('sqrt', 4), ('2', 2)], ('sqrt', 4): [(2, 3), ('4', 1)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Sqrt1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sqrt[3](9)=2'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {('=', 0): [('sqrt', 4), ('2', 3)], ('sqrt', 4): [('3', 1), ('9', 2)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Ln(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\ln(e)=1'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {('=', 0): [('log', 4), ('1', 2)], ('log', 4): [('e', 3), ('e', 1)]}
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Frac(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\frac{12}{24}=\\frac{1000}{2000}'
    parser = Latexparser(equationStr, verbose=verbose)
    parser._parse()
    expected_ast = {   ('=', 0): [('frac', 5), ('frac', 6)],
    ('frac', 5): [('12', 1), ('24', 2)],
    ('frac', 6): [('1000', 3), ('2000', 4)]}
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
    ('=', 0): [('*', 7), ('*', 4)],
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
    expected_ast = None # to be filled in
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
    # test__findingBackSlashAndInfixOperations__Log0()
    # test__findingBackSlashAndInfixOperations__Log1()
    # test__findingBackSlashAndInfixOperations__tildeVariable()
    # test__findingBackSlashAndInfixOperations__SchrodingerWaveEquation()
    # test__infixInBackslash__paraboloid()
    # test__sqrtWithPowerCaretRightOtherInfix__hill()
    test__manyFracCaretEnclosingBrac__partialFrac(True) # not tested yet
    # test__fracWithLogNoBase__changeLogBaseFormula() # not tested yet
    # test__paveWayForDifferentiation__productRule() # not tested yet
    # test__paveWayForDifferentiation__sumRule() # not tested yet
    # test__paveWayForIntegration__enclosingBracketNonBackslash() # not tested yet
    # test__paveWayForIntegrtion__exponentOnEnclosingNonBackslash() # not tested yet