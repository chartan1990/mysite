import inspect
import pprint

from foundation.automat.parser.sorte import Schemeparser


def test__schemeParserTest__add(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '(= a (+ b c))'
    parser = Schemeparser(equationStr=equationStr, verbose=verbose)
    ast = parser.ast
    pp.pprint(ast)
    expected_ast = {
    ('=', 0):[('a', 1), ('+', 2)],
    ('+', 2):[('b', 3), ('c', 4)]
    }
    unparsedStr = parser._unparse()
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', (equationStr==unparsedStr) and (ast==expected_ast))
    if verbose:
        pp.pprint(parser.ast)


def test__schemeParserTest__harmonicMean(verbose=False):
    #HARMONIC MEAN : https://en.wikipedia.org/wiki/Harmonic_mean
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '(= (/ 1 a) (+ (/ 1 b) (/ 1 c)))'
    parser = Schemeparser(equationStr=equationStr, verbose=verbose)
    ast = parser.ast
    pp.pprint(ast)
    expected_ast = {   ('+', 2): [('/', 5), ('/', 6)],
    ('/', 1): [('1', 3), ('a', 4)],
    ('/', 5): [('1', 7), ('b', 8)],
    ('/', 6): [('1', 9), ('c', 10)],
    ('=', 0): [('/', 1), ('+', 2)]}
    unparsedStr = parser._unparse()
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', (equationStr==unparsedStr) and (ast==expected_ast))
    if verbose:
        pp.pprint(parser.ast)


def test__schemeParserTest__phasorDiagram(verbose=False):
    #Phasor Diagram : https://en.wikipedia.org/wiki/Euler%27s_formula
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '(= (^ e (* i x)) (+ (cos x) (* i (sin x))))'
    parser = Schemeparser(equationStr=equationStr, verbose=verbose)
    ast = parser.ast
    pp.pprint(ast)
    expected_ast ={   ('*', 4): [('i', 7), ('x', 8)],
    ('*', 6): [('i', 10), ('sin', 11)],
    ('+', 2): [('cos', 5), ('*', 6)],
    ('=', 0): [('^', 1), ('+', 2)],
    ('^', 1): [('e', 3), ('*', 4)],
    ('cos', 5): [('x', 9)],
    ('sin', 11): [('x', 12)]}
    unparsedStr = parser._unparse()
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', (equationStr==unparsedStr) and (ast==expected_ast))
    if verbose:
        pp.pprint(parser.ast)


def test__schemeParserTest__ebersMollModelp1(verbose=False):
    #Ebers-Moll model : https://en.wikipedia.org/wiki/Bipolar_junction_transistor#Ebers%E2%80%93Moll_model
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '(= I_E (* I_{ES} (- (^ e (/ V_{BE} V_T) 1))))'
    parser = Schemeparser(equationStr=equationStr, verbose=verbose)
    ast = parser.ast
    pp.pprint(ast)
    expected_ast = {   
    ('*', 2): [('I_{ES}', 3), ('-', 4)],
    ('-', 4): [('^', 5)],
    ('/', 7): [('V_{BE}', 9), ('V_T', 10)],
    ('=', 0): [('I_E', 1), ('*', 2)],
    ('^', 5): [('e', 6), ('/', 7), ('1', 8)]}
    unparsedStr = parser._unparse()
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', (equationStr==unparsedStr) and (ast==expected_ast))


def test__schemeParserTest__earlyEffectModel(verbose=False):
    #https://en.wikipedia.org/wiki/Early_effect#Large-signal_model
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '(= I_E (* I_S (* (^ e (/ V_{BE} V_T)) (+ 1 (/ V_{CE} V_A)))))'
    parser = Schemeparser(equationStr=equationStr, verbose=verbose)
    ast = parser.ast
    pp.pprint(ast)
    expected_ast = {   ('*', 2): [('I_S', 3), ('*', 4)],
    ('*', 4): [('^', 5), ('+', 6)],
    ('+', 6): [('1', 9), ('/', 10)],
    ('/', 8): [('V_{BE}', 11), ('V_T', 12)],
    ('/', 10): [('V_{CE}', 13), ('V_A', 14)],
    ('=', 0): [('I_E', 1), ('*', 2)],
    ('^', 5): [('e', 7), ('/', 8)]}
    unparsedStr = parser._unparse()
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', (equationStr==unparsedStr) and (ast==expected_ast))

if __name__=='__main__':
    test__schemeParserTest__add()
    test__schemeParserTest__harmonicMean()
    test__schemeParserTest__phasorDiagram()
    test__schemeParserTest__ebersMollModelp1()
    test__schemeParserTest__earlyEffectModel()