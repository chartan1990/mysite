import pprint

from foundation.automat.parser.parser import Latexparser


def test__findingBackSlashAndInfixOperations_Trig0():
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\sin(2x) = 2\sin(x)\cos(x)' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    #parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    print('variablePos************************')
    pp.pprint(parser.variablesPos)
    print('functionPos************************')
    pp.pprint(parser.functionPos)
    #print('openBracketsLocation************************')
    #pp.pprint(parser.openBracketsLocation)
    #print('matchingBracketsLocation************************')
    #pp.pprint(parser.matchingBracketsLocation)
    #print('infixOperatorPositions************************')
    #pp.pprint(parser.infixOperatorPositions)


def test__findingBackSlashAndInfixOperations_Trig1():
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\sin^2(x)+\cos^2(x)=1' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    #parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    print('variablePos************************')
    pp.pprint(parser.variablesPos)
    print('functionPos************************')
    pp.pprint(parser.functionPos)
    #print('openBracketsLocation************************')
    #pp.pprint(parser.openBracketsLocation)
    #print('matchingBracketsLocation************************')
    #pp.pprint(parser.matchingBracketsLocation)
    #print('infixOperatorPositions************************')
    #pp.pprint(parser.infixOperatorPositions)


def test__findingBackSlashAndInfixOperations_Trig2():
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\sin^{2}(x)+\cos^{2}(x)=1' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    #parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    print('variablePos************************')
    pp.pprint(parser.variablesPos)
    print('functionPos************************')
    pp.pprint(parser.functionPos)
    #print('openBracketsLocation************************')
    #pp.pprint(parser.openBracketsLocation)
    #print('matchingBracketsLocation************************')
    #pp.pprint(parser.matchingBracketsLocation)
    #print('infixOperatorPositions************************')
    #pp.pprint(parser.infixOperatorPositions)


#sqrt
def test__findingBackSlashAndInfixOperations_Sqrt0():
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'sqrt(4)=2' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    #parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    print('variablePos************************')
    pp.pprint(parser.variablesPos)
    print('functionPos************************')
    pp.pprint(parser.functionPos)
    #print('openBracketsLocation************************')
    #pp.pprint(parser.openBracketsLocation)
    #print('matchingBracketsLocation************************')
    #pp.pprint(parser.matchingBracketsLocation)
    #print('infixOperatorPositions************************')
    #pp.pprint(parser.infixOperatorPositions)

def test__findingBackSlashAndInfixOperations_Sqrt1():
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = 'sqrt[3](9)=2' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    #parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    print('variablePos************************')
    pp.pprint(parser.variablesPos)
    print('functionPos************************')
    pp.pprint(parser.functionPos)
    #print('openBracketsLocation************************')
    #pp.pprint(parser.openBracketsLocation)
    #print('matchingBracketsLocation************************')
    #pp.pprint(parser.matchingBracketsLocation)
    #print('infixOperatorPositions************************')
    #pp.pprint(parser.infixOperatorPositions)

#ln
def test__findingBackSlashAndInfixOperations_Ln():
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\ln(e)=1' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    #parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    print('variablePos************************')
    pp.pprint(parser.variablesPos)
    print('functionPos************************')
    pp.pprint(parser.functionPos)
    #print('openBracketsLocation************************')
    #pp.pprint(parser.openBracketsLocation)
    #print('matchingBracketsLocation************************')
    #pp.pprint(parser.matchingBracketsLocation)
    #print('infixOperatorPositions************************')
    #pp.pprint(parser.infixOperatorPositions)
#frac
def test__findingBackSlashAndInfixOperations_Frac():
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\frac{2}{4}=\frac{1}{2}' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    #parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    print('variablePos************************')
    pp.pprint(parser.variablesPos)
    print('functionPos************************')
    pp.pprint(parser.functionPos)
    #print('openBracketsLocation************************')
    #pp.pprint(parser.openBracketsLocation)
    #print('matchingBracketsLocation************************')
    #pp.pprint(parser.matchingBracketsLocation)
    #print('infixOperatorPositions************************')
    #pp.pprint(parser.infixOperatorPositions)
#log
def test__findingBackSlashAndInfixOperations_Log0():
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\log_{2}(8)=3' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    #parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    print('variablePos************************')
    pp.pprint(parser.variablesPos)
    print('functionPos************************')
    pp.pprint(parser.functionPos)
    #print('openBracketsLocation************************')
    #pp.pprint(parser.openBracketsLocation)
    #print('matchingBracketsLocation************************')
    #pp.pprint(parser.matchingBracketsLocation)
    #print('infixOperatorPositions************************')
    #pp.pprint(parser.infixOperatorPositions)


def test__findingBackSlashAndInfixOperations_Log1():
    pp = pprint.PrettyPrinter(indent=4)

    equationStr = '\log(100)=2' # should add the implicit multiplications first...
    parser = Latexparser(equationStr, verbose=True)
    parser._findVariablesFunctionsPositions()
    #parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?
    print('equationStr************************')
    print(equationStr)
    print('variablePos************************')
    pp.pprint(parser.variablesPos)
    print('functionPos************************')
    pp.pprint(parser.functionPos)
    #print('openBracketsLocation************************')
    #pp.pprint(parser.openBracketsLocation)
    #print('matchingBracketsLocation************************')
    #pp.pprint(parser.matchingBracketsLocation)
    #print('infixOperatorPositions************************')
    #pp.pprint(parser.infixOperatorPositions)

if __name__=='__main__':
    #test__findingBackSlashAndInfixOperations_Trig0()
    #test__findingBackSlashAndInfixOperations_Trig1()
    test__findingBackSlashAndInfixOperations_Trig2()
    test__findingBackSlashAndInfixOperations_Sqrt0()
    test__findingBackSlashAndInfixOperations_Sqrt1()
    test__findingBackSlashAndInfixOperations_Ln()
    test__findingBackSlashAndInfixOperations_Frac()
    test__findingBackSlashAndInfixOperations_Log0()
    test__findingBackSlashAndInfixOperations_Log1()