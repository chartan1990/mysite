from foundation.automat.parser.parser import Latexparser


def test__findingBackSlashAndInfixOperations():
    equationStr = '\sin(2x) = 2\sin(x)\cos(x)'
    parser = Latexparser(equationStr)
    parser._findVariablesFunctionsPositions()
    parser._findInfixAndEnclosingBrackets()
    #TODO try to find what symbols are left over at what positions?



if __name__=='__main__':
    test__findingBackSlashAndInfixOperations()