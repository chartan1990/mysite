import pprint

from foundation.automat.parser.parser import Latexparser


def test__findingBackSlashAndInfixOperations_Trig0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sin(2x) = 2\\sin(x)\\cos(x)' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    if verbose:
        print('variablePos************************')
        pp.pprint(parser.variablesPos) # here we are only have variables that start with backslash.... not all the variables are captured.
    expected__variablesPos = []
    print(f'variablesPos as expected? {parser.variablesPos==expected__variablesPos}')
    if verbose:
        print('functionPos************************')
        pp.pprint(parser.functionPos)
    expected__functionPos = [   {   'argument1': None,
        'argument1BracketType': None,
        'argument1EndPosition': None,
        'argument1StartPosition': None,
        'argument2': '2x',
        'argument2BracketType': '(',
        'argument2EndPosition': 7,
        'argument2StartPosition': 5,
        'endPos': 4,
        'name': 'sin',
        'startPos': 0,
        'type': 'backslash'},
    {   'argument1': None,
        'argument1BracketType': None,
        'argument1EndPosition': None,
        'argument1StartPosition': None,
        'argument2': 'x',
        'argument2BracketType': '(',
        'argument2EndPosition': 18,
        'argument2StartPosition': 17,
        'endPos': 16,
        'name': 'sin',
        'startPos': 12,
        'type': 'backslash'},
    {   'argument1': None,
        'argument1BracketType': None,
        'argument1EndPosition': None,
        'argument1StartPosition': None,
        'argument2': 'x',
        'argument2BracketType': '(',
        'argument2EndPosition': 25,
        'argument2StartPosition': 24,
        'endPos': 23,
        'name': 'cos',
        'startPos': 19,
        'type': 'backslash'}]
    print(f'expected__functionPos as expected? {parser.functionPos==expected__functionPos}')
    #for enclose tree... then take difference between child and parent's index....  (range difference only for labels and brackets and not the contents of the arguments), those are the ones that are not captured.
    #then add implicit multiply..., if got enclosure tree then no need to prefixToInfix.... YEAH! XD
    if verbose:
        print('openBracketsLocation************************')
        pp.pprint(parser.openBracketsLocation)
    expected__openBracketsLocation = {'(': [], '[': [], '{': []}
    print(f'expected__openBracketsLocation as expected? {parser.openBracketsLocation==expected__openBracketsLocation}')
    if verbose:
        print('matchingBracketsLocation************************')
        pp.pprint(parser.matchingBracketsLocation)
    expected__matchingBracketsLocation = [   {'endPos': 7, 'openBracketType': '(', 'startPos': 4},
    {'endPos': 18, 'openBracketType': '(', 'startPos': 16},
    {'endPos': 25, 'openBracketType': '(', 'startPos': 23}]
    print(f'expected__matchingBracketsLocation as expected? {parser.matchingBracketsLocation==expected__matchingBracketsLocation}')
    if verbose:
        print('infixOperatorPositions************************')
        pp.pprint(parser.infixOperatorPositions)
    expected__infixOperatorPositions = {'*': [], '+': [], '-': [], '/': [], '^': []}
    print(f'expected__infixOperatorPositions as expected? {parser.infixOperatorPositions==expected__infixOperatorPositions}')
    #TODO remove openBracketsLocations that belong to backslash.... only keep enclosing brackets


def test__findingBackSlashAndInfixOperations_Trig1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sin^2(x)+\\cos^2(x)=1' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    if verbose:
        print('variablePos************************')
        pp.pprint(parser.variablesPos) # here we are only have variables that start with backslash.... not all the variables are captured.
    expected__variablesPos = []
    print(f'variablesPos as expected? {parser.variablesPos==expected__variablesPos}')
    if verbose:
        print('functionPos************************')
        pp.pprint(parser.functionPos)
    #abit weird...
    expected__functionPos = [   {   'argument1': '2',
        'argument1BracketType': None,
        'argument1EndPosition': 6,
        'argument1StartPosition': 5,
        'argument2': 'x',
        'argument2BracketType': '(',
        'argument2EndPosition': 8,
        'argument2StartPosition': 7,
        'endPos': 4,
        'name': 'sin',
        'startPos': 0,
        'type': 'backslash'},
    {   'argument1': '2',
        'argument1BracketType': None,
        'argument1EndPosition': 16,
        'argument1StartPosition': 15,
        'argument2': 'x',
        'argument2BracketType': '(',
        'argument2EndPosition': 18,
        'argument2StartPosition': 17,
        'endPos': 14,
        'name': 'cos',
        'startPos': 10,
        'type': 'backslash'}]
    print(f'expected__functionPos as expected? {parser.functionPos==expected__functionPos}')
    if verbose:
        print('openBracketsLocation************************')
        pp.pprint(parser.openBracketsLocation)
    expected__openBracketsLocation = {'(': [], '[': [], '{': []}
    print(f'expected__openBracketsLocation as expected? {parser.openBracketsLocation==expected__openBracketsLocation}')
    if verbose:
        print('matchingBracketsLocation************************')
        pp.pprint(parser.matchingBracketsLocation)
    expected__matchingBracketsLocation = [   {'endPos': 8, 'openBracketType': '(', 'startPos': 6},
    {'endPos': 18, 'openBracketType': '(', 'startPos': 16}]
    print(f'expected__matchingBracketsLocation as expected? {parser.matchingBracketsLocation==expected__matchingBracketsLocation}')
    if verbose:
        print('infixOperatorPositions************************')
        pp.pprint(parser.infixOperatorPositions)
    expected__infixOperatorPositions = {
    '*': [],
    '+': [   {   'endPos': 4,
                 'endSymbol': '^',
                 'leftCloseBracket': ')',
                 'position': 9,
                 'rightOpenBracket': None,
                 'startPos': 14,
                 'startSymbol': '^'}],
    '-': [],
    '/': [],
    '^': [   {   'endPos': 9,
                 'endSymbol': '+',
                 'leftCloseBracket': None,
                 'position': 4,
                 'rightOpenBracket': None,
                 'startPos': 9,
                 'startSymbol': '+'},
             {   'endPos': 4,
                 'endSymbol': '^',
                 'leftCloseBracket': None,
                 'position': 14,
                 'rightOpenBracket': None,
                 'startPos': 9,
                 'startSymbol': '+'}]}
    print(f'expected__infixOperatorPositions as expected? {parser.infixOperatorPositions==expected__infixOperatorPositions}')


def test__findingBackSlashAndInfixOperations_Trig2(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sin^{2}(x)+\\cos^{2}(x)=1' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    if verbose:
        print('variablePos************************')
        pp.pprint(parser.variablesPos) # here we are only have variables that start with backslash.... not all the variables are captured.
    expected__variablesPos = []
    print(f'variablesPos as expected? {parser.variablesPos==expected__variablesPos}')
    if verbose:
        print('functionPos************************')
        pp.pprint(parser.functionPos)
    expected__functionPos = [   {   'argument1': '2',
        'argument1EndPosition': 7,
        'argument1StartPosition': 6,
        'argument2': 'x',
        'argument2EndPosition': 10,
        'argument2StartPosition': 9,
        'endPos': 4,
        'name': 'sin',
        'startPos': 0,
        'type': 'backslash'},
    {   'argument1': '2',
        'argument1EndPosition': 19,
        'argument1StartPosition': 18,
        'argument2': 'x',
        'argument2EndPosition': 22,
        'argument2StartPosition': 21,
        'endPos': 16,
        'name': 'cos',
        'startPos': 12,
        'type': 'backslash'}]
    print(f'expected__functionPos as expected? {parser.functionPos==expected__functionPos}')
    if verbose:
        print('openBracketsLocation************************')
        pp.pprint(parser.openBracketsLocation)
    expected__openBracketsLocation = {'(': [], '[': [], '{': []}
    print(f'expected__openBracketsLocation as expected? {parser.openBracketsLocation==expected__openBracketsLocation}')
    if verbose:
        print('matchingBracketsLocation************************')
        pp.pprint(parser.matchingBracketsLocation)
    expected__matchingBracketsLocation = [   {'endPos': 7, 'openBracketType': '(', 'startPos': 4},
    {'endPos': 18, 'openBracketType': '(', 'startPos': 16},
    {'endPos': 25, 'openBracketType': '(', 'startPos': 23}]
    print(f'expected__matchingBracketsLocation as expected? {parser.matchingBracketsLocation==expected__matchingBracketsLocation}')
    if verbose:
        print('infixOperatorPositions************************')
        pp.pprint(parser.infixOperatorPositions)
    expected__infixOperatorPositions = {'*': [], '+': [], '-': [], '/': [], '^': []}
    print(f'expected__infixOperatorPositions as expected? {parser.infixOperatorPositions==expected__infixOperatorPositions}')


#sqrt
def test__findingBackSlashAndInfixOperations_Sqrt0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sqrt(4)=2' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    if verbose:
        print('variablePos************************')
        pp.pprint(parser.variablesPos) # here we are only have variables that start with backslash.... not all the variables are captured.
    expected__variablesPos = []
    print(f'variablesPos as expected? {parser.variablesPos==expected__variablesPos}')
    if verbose:
        print('functionPos************************')
        pp.pprint(parser.functionPos)
    expected__functionPos = [   {   'argument1': 2,
        'argument1EndPosition': None,
        'argument1StartPosition': None,
        'argument2': '4',
        'argument2EndPosition': 7,
        'argument2StartPosition': 6,
        'endPos': 5,
        'name': 'sqrt',
        'startPos': 0,
        'type': 'backslash'}]
    print(f'expected__functionPos as expected? {parser.functionPos==expected__functionPos}')
    if verbose:
        print('openBracketsLocation************************')
        pp.pprint(parser.openBracketsLocation)
    expected__openBracketsLocation = {'(': [], '[': [], '{': []}
    print(f'expected__openBracketsLocation as expected? {parser.openBracketsLocation==expected__openBracketsLocation}')
    if verbose:
        print('matchingBracketsLocation************************')
        pp.pprint(parser.matchingBracketsLocation)
    expected__matchingBracketsLocation = [   {'endPos': 7, 'openBracketType': '(', 'startPos': 4},
    {'endPos': 18, 'openBracketType': '(', 'startPos': 16},
    {'endPos': 25, 'openBracketType': '(', 'startPos': 23}]
    print(f'expected__matchingBracketsLocation as expected? {parser.matchingBracketsLocation==expected__matchingBracketsLocation}')
    if verbose:
        print('infixOperatorPositions************************')
        pp.pprint(parser.infixOperatorPositions)
    expected__infixOperatorPositions = {'*': [], '+': [], '-': [], '/': [], '^': []}
    print(f'expected__infixOperatorPositions as expected? {parser.infixOperatorPositions==expected__infixOperatorPositions}')

def test__findingBackSlashAndInfixOperations_Sqrt1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\sqrt[3](9)=2' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    if verbose:
        print('variablePos************************')
        pp.pprint(parser.variablesPos) # here we are only have variables that start with backslash.... not all the variables are captured.
    expected__variablesPos = []
    print(f'variablesPos as expected? {parser.variablesPos==expected__variablesPos}')
    if verbose:
        print('functionPos************************')
        pp.pprint(parser.functionPos)
    expected__functionPos = [   {   'argument1': '3',
        'argument1EndPosition': 7,
        'argument1StartPosition': 6,
        'argument2': '9',
        'argument2EndPosition': 10,
        'argument2StartPosition': 9,
        'endPos': 5,
        'name': 'sqrt',
        'startPos': 0,
        'type': 'backslash'}]
    print(f'expected__functionPos as expected? {parser.functionPos==expected__functionPos}')
    if verbose:
        print('openBracketsLocation************************')
        pp.pprint(parser.openBracketsLocation)
    expected__openBracketsLocation = {'(': [], '[': [], '{': []}
    print(f'expected__openBracketsLocation as expected? {parser.openBracketsLocation==expected__openBracketsLocation}')
    if verbose:
        print('matchingBracketsLocation************************')
        pp.pprint(parser.matchingBracketsLocation)
    expected__matchingBracketsLocation = [   {'endPos': 7, 'openBracketType': '(', 'startPos': 4},
    {'endPos': 18, 'openBracketType': '(', 'startPos': 16},
    {'endPos': 25, 'openBracketType': '(', 'startPos': 23}]
    print(f'expected__matchingBracketsLocation as expected? {parser.matchingBracketsLocation==expected__matchingBracketsLocation}')
    if verbose:
        print('infixOperatorPositions************************')
        pp.pprint(parser.infixOperatorPositions)
    expected__infixOperatorPositions = {'*': [], '+': [], '-': [], '/': [], '^': []}
    print(f'expected__infixOperatorPositions as expected? {parser.infixOperatorPositions==expected__infixOperatorPositions}')

#ln
def test__findingBackSlashAndInfixOperations_Ln(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\ln(e)=1' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    if verbose:
        print('variablePos************************')
        pp.pprint(parser.variablesPos) # here we are only have variables that start with backslash.... not all the variables are captured.
    expected__variablesPos = []
    print(f'variablesPos as expected? {parser.variablesPos==expected__variablesPos}')
    if verbose:
        print('functionPos************************')
        pp.pprint(parser.functionPos)
    expected__functionPos = [   {   'argument1': 'e',
        'argument1EndPosition': None,
        'argument1StartPosition': None,
        'argument2': 'e',
        'argument2EndPosition': 5,
        'argument2StartPosition': 4,
        'endPos': 3,
        'name': 'ln',
        'startPos': 0,
        'type': 'backslash'}]
    print(f'expected__functionPos as expected? {parser.functionPos==expected__functionPos}')
    if verbose:
        print('openBracketsLocation************************')
        pp.pprint(parser.openBracketsLocation)
    expected__openBracketsLocation = {'(': [], '[': [], '{': []}
    print(f'expected__openBracketsLocation as expected? {parser.openBracketsLocation==expected__openBracketsLocation}')
    if verbose:
        print('matchingBracketsLocation************************')
        pp.pprint(parser.matchingBracketsLocation)
    expected__matchingBracketsLocation = [   {'endPos': 7, 'openBracketType': '(', 'startPos': 4},
    {'endPos': 18, 'openBracketType': '(', 'startPos': 16},
    {'endPos': 25, 'openBracketType': '(', 'startPos': 23}]
    print(f'expected__matchingBracketsLocation as expected? {parser.matchingBracketsLocation==expected__matchingBracketsLocation}')
    if verbose:
        print('infixOperatorPositions************************')
        pp.pprint(parser.infixOperatorPositions)
    expected__infixOperatorPositions = {'*': [], '+': [], '-': [], '/': [], '^': []}
    print(f'expected__infixOperatorPositions as expected? {parser.infixOperatorPositions==expected__infixOperatorPositions}')

#frac
def test__findingBackSlashAndInfixOperations_Frac(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\frac{12}{24}=\\frac{1000}{2000}' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    if verbose:
        print('variablePos************************')
        pp.pprint(parser.variablesPos) # here we are only have variables that start with backslash.... not all the variables are captured.
    expected__variablesPos = []
    print(f'variablesPos as expected? {parser.variablesPos==expected__variablesPos}')
    if verbose:
        print('functionPos************************')
        pp.pprint(parser.functionPos)
    expected__functionPos = [   {   'argument1': '12',
        'argument1EndPosition': 8,
        'argument1StartPosition': 6,
        'argument2': '24',
        'argument2EndPosition': 12,
        'argument2StartPosition': 10,
        'endPos': 5,
        'name': 'frac',
        'startPos': 0,
        'type': 'backslash'},
    {   'argument1': '1000',
        'argument1EndPosition': 24,
        'argument1StartPosition': 20,
        'argument2': '2000',
        'argument2EndPosition': 30,
        'argument2StartPosition': 26,
        'endPos': 19,
        'name': 'frac',
        'startPos': 14,
        'type': 'backslash'}]
    print(f'expected__functionPos as expected? {parser.functionPos==expected__functionPos}')
    if verbose:
        print('openBracketsLocation************************')
        pp.pprint(parser.openBracketsLocation)
    expected__openBracketsLocation = {'(': [], '[': [], '{': []}
    print(f'expected__openBracketsLocation as expected? {parser.openBracketsLocation==expected__openBracketsLocation}')
    if verbose:
        print('matchingBracketsLocation************************')
        pp.pprint(parser.matchingBracketsLocation)
    expected__matchingBracketsLocation = [   {'endPos': 7, 'openBracketType': '(', 'startPos': 4},
    {'endPos': 18, 'openBracketType': '(', 'startPos': 16},
    {'endPos': 25, 'openBracketType': '(', 'startPos': 23}]
    print(f'expected__matchingBracketsLocation as expected? {parser.matchingBracketsLocation==expected__matchingBracketsLocation}')
    if verbose:
        print('infixOperatorPositions************************')
        pp.pprint(parser.infixOperatorPositions)
    expected__infixOperatorPositions = {'*': [], '+': [], '-': [], '/': [], '^': []}
    print(f'expected__infixOperatorPositions as expected? {parser.infixOperatorPositions==expected__infixOperatorPositions}')

#log
def test__findingBackSlashAndInfixOperations_Log0(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\log_{12}(8916100448256)=12' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    if verbose:
        print('variablePos************************')
        pp.pprint(parser.variablesPos) # here we are only have variables that start with backslash.... not all the variables are captured.
    expected__variablesPos = []
    print(f'variablesPos as expected? {parser.variablesPos==expected__variablesPos}')
    if verbose:
        print('functionPos************************')
        pp.pprint(parser.functionPos)
    expected__functionPos = [   {   'argument1': '12',
        'argument1EndPosition': 8,
        'argument1StartPosition': 6,
        'argument2': '8916100448256',
        'argument2EndPosition': 23,
        'argument2StartPosition': 10,
        'endPos': 4,
        'name': 'log',
        'startPos': 0,
        'type': 'backslash'}]
    print(f'expected__functionPos as expected? {parser.functionPos==expected__functionPos}')
    if verbose:
        print('openBracketsLocation************************')
        pp.pprint(parser.openBracketsLocation)
    expected__openBracketsLocation = {'(': [], '[': [], '{': []}
    print(f'expected__openBracketsLocation as expected? {parser.openBracketsLocation==expected__openBracketsLocation}')
    if verbose:
        print('matchingBracketsLocation************************')
        pp.pprint(parser.matchingBracketsLocation)
    expected__matchingBracketsLocation = [   {'endPos': 7, 'openBracketType': '(', 'startPos': 4},
    {'endPos': 18, 'openBracketType': '(', 'startPos': 16},
    {'endPos': 25, 'openBracketType': '(', 'startPos': 23}]
    print(f'expected__matchingBracketsLocation as expected? {parser.matchingBracketsLocation==expected__matchingBracketsLocation}')
    if verbose:
        print('infixOperatorPositions************************')
        pp.pprint(parser.infixOperatorPositions)
    expected__infixOperatorPositions = {'*': [], '+': [], '-': [], '/': [], '^': []}
    print(f'expected__infixOperatorPositions as expected? {parser.infixOperatorPositions==expected__infixOperatorPositions}')


def test__findingBackSlashAndInfixOperations_Log1(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\log(100)=2' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    if verbose:
        print('variablePos************************')
        pp.pprint(parser.variablesPos) # here we are only have variables that start with backslash.... not all the variables are captured.
    expected__variablesPos = []
    print(f'variablesPos as expected? {parser.variablesPos==expected__variablesPos}')
    if verbose:
        print('functionPos************************')
        pp.pprint(parser.functionPos)
    expected__functionPos = [   {   'argument1': 10,
        'argument1EndPosition': None,
        'argument1StartPosition': None,
        'argument2': '100',
        'argument2EndPosition': 8,
        'argument2StartPosition': 5,
        'endPos': 4,
        'name': 'log',
        'startPos': 0,
        'type': 'backslash'}]
    print(f'expected__functionPos as expected? {parser.functionPos==expected__functionPos}')
    if verbose:
        print('openBracketsLocation************************')
        pp.pprint(parser.openBracketsLocation)
    expected__openBracketsLocation = {'(': [], '[': [], '{': []}
    print(f'expected__openBracketsLocation as expected? {parser.openBracketsLocation==expected__openBracketsLocation}')
    if verbose:
        print('matchingBracketsLocation************************')
        pp.pprint(parser.matchingBracketsLocation)
    expected__matchingBracketsLocation = [   {'endPos': 7, 'openBracketType': '(', 'startPos': 4},
    {'endPos': 18, 'openBracketType': '(', 'startPos': 16},
    {'endPos': 25, 'openBracketType': '(', 'startPos': 23}]
    print(f'expected__matchingBracketsLocation as expected? {parser.matchingBracketsLocation==expected__matchingBracketsLocation}')
    if verbose:
        print('infixOperatorPositions************************')
        pp.pprint(parser.infixOperatorPositions)
    expected__infixOperatorPositions = {'*': [], '+': [], '-': [], '/': [], '^': []}
    print(f'expected__infixOperatorPositions as expected? {parser.infixOperatorPositions==expected__infixOperatorPositions}')

def test__findingBackSlashAndInfixOperations_tildeVariable(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\tilde{x}=2' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    if verbose:
        print('variablePos************************')
        pp.pprint(parser.variablesPos) # here we are only have variables that start with backslash.... not all the variables are captured.
    expected__variablesPos = []
    print(f'variablesPos as expected? {parser.variablesPos==expected__variablesPos}')
    if verbose:
        print('functionPos************************')
        pp.pprint(parser.functionPos)
    expected__functionPos = [   {   'argument1': 'x',
        'argument1EndPosition': 8,
        'argument1StartPosition': 7,
        'endPos': 6,
        'name': 'tilde',
        'startPos': 0,
        'type': 'backslash'}]
    print(f'expected__functionPos as expected? {parser.functionPos==expected__functionPos}')
    if verbose:
        print('openBracketsLocation************************')
        pp.pprint(parser.openBracketsLocation)
    expected__openBracketsLocation = {'(': [], '[': [], '{': []}
    print(f'expected__openBracketsLocation as expected? {parser.openBracketsLocation==expected__openBracketsLocation}')
    if verbose:
        print('matchingBracketsLocation************************')
        pp.pprint(parser.matchingBracketsLocation)
    expected__matchingBracketsLocation = [   {'endPos': 7, 'openBracketType': '(', 'startPos': 4},
    {'endPos': 18, 'openBracketType': '(', 'startPos': 16},
    {'endPos': 25, 'openBracketType': '(', 'startPos': 23}]
    print(f'expected__matchingBracketsLocation as expected? {parser.matchingBracketsLocation==expected__matchingBracketsLocation}')
    if verbose:
        print('infixOperatorPositions************************')
        pp.pprint(parser.infixOperatorPositions)
    expected__infixOperatorPositions = {'*': [], '+': [], '-': [], '/': [], '^': []}
    print(f'expected__infixOperatorPositions as expected? {parser.infixOperatorPositions==expected__infixOperatorPositions}')

def test__findingBackSlashAndInfixOperations_SchrodingerWaveEquation(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\\widehat{H}\\Psi=\\widehat{E}\\Psi' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    if verbose:
        print('variablePos************************')
        pp.pprint(parser.variablesPos) # here we are only have variables that start with backslash.... not all the variables are captured.
    expected__variablesPos = []
    print(f'variablesPos as expected? {parser.variablesPos==expected__variablesPos}')
    if verbose:
        print('functionPos************************')
        pp.pprint(parser.functionPos)
    expected__functionPos = [   {   'argument1': 'H',
        'argument1EndPosition': 10,
        'argument1StartPosition': 9,
        'endPos': 8,
        'name': 'widehat',
        'startPos': 0,
        'type': 'backslash'},
    {'endPos': 15, 'name': 'Psi', 'startPos': 11, 'type': 'backslash'},
    {   'argument1': 'E',
        'argument1EndPosition': 26,
        'argument1StartPosition': 25,
        'endPos': 24,
        'name': 'widehat',
        'startPos': 16,
        'type': 'backslash'},
    {'endPos': 31, 'name': 'Psi', 'startPos': 27, 'type': 'backslash'}]
    print(f'expected__functionPos as expected? {parser.functionPos==expected__functionPos}')
    if verbose:
        print('openBracketsLocation************************')
        pp.pprint(parser.openBracketsLocation)
    expected__openBracketsLocation = {'(': [], '[': [], '{': []}
    print(f'expected__openBracketsLocation as expected? {parser.openBracketsLocation==expected__openBracketsLocation}')
    if verbose:
        print('matchingBracketsLocation************************')
        pp.pprint(parser.matchingBracketsLocation)
    expected__matchingBracketsLocation = [   {'endPos': 7, 'openBracketType': '(', 'startPos': 4},
    {'endPos': 18, 'openBracketType': '(', 'startPos': 16},
    {'endPos': 25, 'openBracketType': '(', 'startPos': 23}]
    print(f'expected__matchingBracketsLocation as expected? {parser.matchingBracketsLocation==expected__matchingBracketsLocation}')
    if verbose:
        print('infixOperatorPositions************************')
        pp.pprint(parser.infixOperatorPositions)
    expected__infixOperatorPositions = {'*': [], '+': [], '-': [], '/': [], '^': []}
    print(f'expected__infixOperatorPositions as expected? {parser.infixOperatorPositions==expected__infixOperatorPositions}')


if __name__=='__main__':
    # test__findingBackSlashAndInfixOperations_Trig0()
    test__findingBackSlashAndInfixOperations_Trig1(True)
    # test__findingBackSlashAndInfixOperations_Trig2()
    # test__findingBackSlashAndInfixOperations_Sqrt0()
    # test__findingBackSlashAndInfixOperations_Sqrt1()
    # test__findingBackSlashAndInfixOperations_Ln()
    # test__findingBackSlashAndInfixOperations_Frac()
    # test__findingBackSlashAndInfixOperations_Log0()
    # test__findingBackSlashAndInfixOperations_Log1()
    # test__findingBackSlashAndInfixOperations_tildeVariable()
    # test__findingBackSlashAndInfixOperations_SchrodingerWaveEquation()