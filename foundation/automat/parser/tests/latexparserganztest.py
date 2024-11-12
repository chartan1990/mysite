import pprint

from foundation.automat.parser.sorte import Latexparser


def test__findingBackSlashAndInfixOperations__Trig0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '-\\sin( 2x_0 ) = -2\\sin(x_0)\\cos(x_0)' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._parse()
    expected_ast = {   ('*', 7): [('2', 6), ('x_0', 8)],
    ('*', 12): [('2', 11), ('sin', 13)],
    ('*', 14): [('*', 12), ('cos', 15)],
    ('-', 4): [('0', 3), ('sin', 5)],
    ('-', 10): [('0', 9), ('*', 14)],
    ('=', 0): [('-', 4), ('-', 10)],
    ('cos', 15): [('x_0', 2)],
    ('sin', 5): [('*', 7)],
    ('sin', 13): [('x_0', 1)]}
    print('PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)



def test__findingBackSlashAndInfixOperations__Trig1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sin^2(x) + \\cos^2(x)=1' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._parse()
    expected_ast = {   ('*', 7): [('2', 6), ('x_0', 8)],
    ('*', 12): [('2', 11), ('sin', 13)],
    ('*', 14): [('*', 12), ('cos', 15)],
    ('-', 4): [('0', 3), ('sin', 5)],
    ('-', 10): [('0', 9), ('*', 14)],
    ('=', 0): [('-', 4), ('-', 10)],
    ('cos', 15): [('x_0', 2)],
    ('sin', 5): [('*', 7)],
    ('sin', 13): [('x_0', 1)]}
    print('PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Trig2(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sin^{2}(x)+\\cos^{2}(x)=1' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._parse()
    expected_ast = {   ('*', 7): [('2', 6), ('x_0', 8)],
    ('*', 12): [('2', 11), ('sin', 13)],
    ('*', 14): [('*', 12), ('cos', 15)],
    ('-', 4): [('0', 3), ('sin', 5)],
    ('-', 10): [('0', 9), ('*', 14)],
    ('=', 0): [('-', 4), ('-', 10)],
    ('cos', 15): [('x_0', 2)],
    ('sin', 5): [('*', 7)],
    ('sin', 13): [('x_0', 1)]}
    print('PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Sqrt0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sqrt(4)=2' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._parse()
    expected_ast = {   ('*', 7): [('2', 6), ('x_0', 8)],
    ('*', 12): [('2', 11), ('sin', 13)],
    ('*', 14): [('*', 12), ('cos', 15)],
    ('-', 4): [('0', 3), ('sin', 5)],
    ('-', 10): [('0', 9), ('*', 14)],
    ('=', 0): [('-', 4), ('-', 10)],
    ('cos', 15): [('x_0', 2)],
    ('sin', 5): [('*', 7)],
    ('sin', 13): [('x_0', 1)]}
    print('PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Sqrt1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sqrt[3](9)=2' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._parse()
    expected_ast = {   ('*', 7): [('2', 6), ('x_0', 8)],
    ('*', 12): [('2', 11), ('sin', 13)],
    ('*', 14): [('*', 12), ('cos', 15)],
    ('-', 4): [('0', 3), ('sin', 5)],
    ('-', 10): [('0', 9), ('*', 14)],
    ('=', 0): [('-', 4), ('-', 10)],
    ('cos', 15): [('x_0', 2)],
    ('sin', 5): [('*', 7)],
    ('sin', 13): [('x_0', 1)]}
    print('PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Ln(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\ln(e)=1' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._parse()
    expected_ast = {   ('*', 7): [('2', 6), ('x_0', 8)],
    ('*', 12): [('2', 11), ('sin', 13)],
    ('*', 14): [('*', 12), ('cos', 15)],
    ('-', 4): [('0', 3), ('sin', 5)],
    ('-', 10): [('0', 9), ('*', 14)],
    ('=', 0): [('-', 4), ('-', 10)],
    ('cos', 15): [('x_0', 2)],
    ('sin', 5): [('*', 7)],
    ('sin', 13): [('x_0', 1)]}
    print('PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Frac(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\frac{12}{24}=\\frac{1000}{2000}' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._parse()
    expected_ast = {   ('*', 7): [('2', 6), ('x_0', 8)],
    ('*', 12): [('2', 11), ('sin', 13)],
    ('*', 14): [('*', 12), ('cos', 15)],
    ('-', 4): [('0', 3), ('sin', 5)],
    ('-', 10): [('0', 9), ('*', 14)],
    ('=', 0): [('-', 4), ('-', 10)],
    ('cos', 15): [('x_0', 2)],
    ('sin', 5): [('*', 7)],
    ('sin', 13): [('x_0', 1)]}
    print('PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Log0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\log_{12}(8916100448256)=12' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._parse()
    expected_ast = {   ('*', 7): [('2', 6), ('x_0', 8)],
    ('*', 12): [('2', 11), ('sin', 13)],
    ('*', 14): [('*', 12), ('cos', 15)],
    ('-', 4): [('0', 3), ('sin', 5)],
    ('-', 10): [('0', 9), ('*', 14)],
    ('=', 0): [('-', 4), ('-', 10)],
    ('cos', 15): [('x_0', 2)],
    ('sin', 5): [('*', 7)],
    ('sin', 13): [('x_0', 1)]}
    print('PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__Log1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\log(100)=2' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._parse()
    expected_ast = {   ('*', 7): [('2', 6), ('x_0', 8)],
    ('*', 12): [('2', 11), ('sin', 13)],
    ('*', 14): [('*', 12), ('cos', 15)],
    ('-', 4): [('0', 3), ('sin', 5)],
    ('-', 10): [('0', 9), ('*', 14)],
    ('=', 0): [('-', 4), ('-', 10)],
    ('cos', 15): [('x_0', 2)],
    ('sin', 5): [('*', 7)],
    ('sin', 13): [('x_0', 1)]}
    print('PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__tildeVariable(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\tilde{x}=2' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._parse()
    expected_ast = {   ('*', 7): [('2', 6), ('x_0', 8)],
    ('*', 12): [('2', 11), ('sin', 13)],
    ('*', 14): [('*', 12), ('cos', 15)],
    ('-', 4): [('0', 3), ('sin', 5)],
    ('-', 10): [('0', 9), ('*', 14)],
    ('=', 0): [('-', 4), ('-', 10)],
    ('cos', 15): [('x_0', 2)],
    ('sin', 5): [('*', 7)],
    ('sin', 13): [('x_0', 1)]}
    print('PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__findingBackSlashAndInfixOperations__SchrodingerWaveEquation(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\widehat{H}\\Psi=\\widehat{E}\\Psi' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._parse()
    expected_ast = {   ('*', 7): [('2', 6), ('x_0', 8)],
    ('*', 12): [('2', 11), ('sin', 13)],
    ('*', 14): [('*', 12), ('cos', 15)],
    ('-', 4): [('0', 3), ('sin', 5)],
    ('-', 10): [('0', 9), ('*', 14)],
    ('=', 0): [('-', 4), ('-', 10)],
    ('cos', 15): [('x_0', 2)],
    ('sin', 5): [('*', 7)],
    ('sin', 13): [('x_0', 1)]}
    print('PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)


def test__infixInBackslash__paraboloid(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'z=\\sqrt(x^2+y^2)' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._parse()
    expected_ast = {   ('*', 7): [('2', 6), ('x_0', 8)],
    ('*', 12): [('2', 11), ('sin', 13)],
    ('*', 14): [('*', 12), ('cos', 15)],
    ('-', 4): [('0', 3), ('sin', 5)],
    ('-', 10): [('0', 9), ('*', 14)],
    ('=', 0): [('-', 4), ('-', 10)],
    ('cos', 15): [('x_0', 2)],
    ('sin', 5): [('*', 7)],
    ('sin', 13): [('x_0', 1)]}
    print('PASSED? ', expected_ast == parser.ast)
    if verbose:
        pp.pprint(parser.ast)




if __name__=='__main__':
    # test__findingBackSlashAndInfixOperations__Trig0(True)
    test__findingBackSlashAndInfixOperations__Trig1(True)
    # test__findingBackSlashAndInfixOperations__Trig2()
    # test__findingBackSlashAndInfixOperations__Sqrt0()
    # test__findingBackSlashAndInfixOperations__Sqrt1()
    # test__findingBackSlashAndInfixOperations__Ln()
    # test__findingBackSlashAndInfixOperations__Frac()
    # test__findingBackSlashAndInfixOperations__Log0()
    # test__findingBackSlashAndInfixOperations__Log1()
    # test__findingBackSlashAndInfixOperations__tildeVariable()
    # test__findingBackSlashAndInfixOperations__SchrodingerWaveEquation()