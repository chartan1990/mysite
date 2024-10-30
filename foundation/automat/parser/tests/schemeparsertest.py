if __name__=='__main__':
    from foundation.automat.parser.parser import Schemeparser

    #############SchemeParser testing
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    eqs = '(= a (+ b c))'
    schemeParser = Schemeparser(eqs, verbose=False)
    ast = schemeParser.ast
    print('*********ast:')
    pp.pprint(ast)
    """
    ast = {
    ('=', 0):[(('a', 1), ('+', 2)],
    ('+', 2):[('b', 3), ('c', 4)]
    }
    """
    unparsedStr = schemeParser._unparse()
    print(f'***********unparsedStr: modorimashitaka: {eqs==unparsedStr}')
    print(unparsedStr)
    print('*******************HARMONIC MEAN : https://en.wikipedia.org/wiki/Harmonic_mean')
    eqs = '(= (/ 1 a) (+ (/ 1 b) (/ 1 c)))'
    schemeParser = Schemeparser(eqs, verbose=False)
    ast = schemeParser.ast
    print('*********ast:')
    pp.pprint(ast)
    """
    ast = {
    ('=', 0):[('/', 1), ('+', 2)],
    ('/', 1):[(1, 3), ('a', 4)],
    ('+', 5):[('/', 6), ('/', 7)],
    ('/', 6):[(1, 8), ('b', 9)],
    ('/', 7):[(1, 10), ('c', 11)]
    }
    """
    unparsedStr = schemeParser._unparse()

    print(f'***********unparsedStr: modorimashitaka: {eqs==unparsedStr}')
    print(unparsedStr)

    print('*******************Phasor Diagram : https://en.wikipedia.org/wiki/Euler%27s_formula')
    eqs = '(= (^ e (* i x)) (+ (cos x) (* i (sin x))))'
    schemeParser = Schemeparser(eqs, verbose=False)
    ast = schemeParser.ast
    print('*********ast:')
    pp.pprint(ast)
    """
    ast = {
    ('=', 0):[('^', 1), ('+', 2)],
    ('^', 1):[(e, 3), ('*', 4)],
    ('+', 2):[('cos', 5), ('*', 6)],

    ('*', 4):[('i', 7), ('x', 8)],
    ('cos', 5):[('x', 9)],
    ('*', 6):[('i', 10), ('sin', 11)],
    ('sin', 11):[('x', 12)]
    }
    """
    unparsedStr = schemeParser._unparse()
    print(f'***********unparsedStr: modorimashitaka {eqs==unparsedStr}')
    print(unparsedStr)

    print('*******************Ebers-Moll_model : https://en.wikipedia.org/wiki/Bipolar_junction_transistor#Ebers%E2%80%93Moll_model')
    eqs = '(= I_E (* I_{ES} (- (^ e (/ V_{BE} V_T) 1))))'
    schemeParser = Schemeparser(eqs, verbose=False)
    ast = schemeParser.ast
    print('*********ast:')
    pp.pprint(ast)
    """
    ast = {
    ('=', 0):[('I_E', 1), ('-', 2)]

    ('-', 2):[('^', 3), (1, 4)],

    ('^', 3):[('e', 5), ('/', 6)],
    ('/', 6):[('V_{BE}', 7), ('V_T', 8)]
    }
    """
    unparsedStr = schemeParser._unparse()
    print(f'***********unparsedStr: modorimashitaka {eqs==unparsedStr}')
    print(unparsedStr)


    print('*******************Early-effect_model(Collector current) : https://en.wikipedia.org/wiki/Early_effect#Large-signal_model')
    eqs = '(= I_E (* I_S (* (^ e (/ V_{BE} V_T)) (+ 1 (/ V_{CE} V_A)))))'
    schemeParser = Schemeparser(eqs, verbose=False)
    ast = schemeParser.ast
    print('*********ast:')
    pp.pprint(ast)
    unparsedStr = schemeParser._unparse()
    print(f'***********unparsedStr: modorimashitaka {eqs==unparsedStr}')
    print(unparsedStr)

