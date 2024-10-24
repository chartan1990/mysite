from abc import ABC

from foundation.automat.common.backtracker import Backtracker
from foundation.automat.common.checker import isFloat
from foundation.automat.arithmetic.function import Function

class Parser(ABC):
    """
    Abstract class for :class:`Equation` to parse an equation string

    :param parserName: the name of the parser
    :type parserName: str
    """
    PARSERNAME_PARSERCLASSSTR = {
        'scheme':'Schemeparser',
        'latex':'Latexparser',
        'javascript':'Javascriptparser'
    }

    def __init__(self, parserName):
        """
        constructor, but initialise the correct parser child instead

        :param parserName: the name of the parser
        :type parserName: str
        """
        self.parserName = parserName
        self.PARSERNAME_PARSERCLASSSTR = Parser.PARSERNAME_PARSERCLASSSTR

    def parse(self, equationStr):
        """
        get the parser class lazily (because of circular import)
        and then initialises it

        :param equationStr: equation string to be parsed to ast
        :type equationStr: str
        :return: tuple of
            - ast (Abstract Syntax Tree), map, key:tuple(label, id), value:list[tuple[label, id]]
            - functions (map from function_label_str to number of such functions there are in the equation
            - variables (map from variable_label_str to number of such variables there are in the equation
            - primitives (amount of primitives there are in the equation
            - totalNodeCount (total number of nodes in the ast)
        :rtype: tuple[
            dict[tuple[str, int], list[tuple[str, int]]],
            dict[str, int],
            dict[str, int],
            int,
            int]
        """
        # will raise exception if parserName not in PARSERNAME_PARSERCLASSSTR
        # actual parsing is done in individual child class
        parser = globals()[self.PARSERNAME_PARSERCLASSSTR[self.parserName]](equationStr)
        ast, functions, variables, primitives, totalNodeCount = parser._parse(equationStr)
        return ast, functions, variables, primitives, totalNodeCount



class Javascriptparser(Parser):
    pass#TODO


class Latexparser(Parser):
    """
    Parser for Latex Strings. More details about 'Latex' format, check
    https://www.latex-project.org/help/documentation/classes.pdf
    """
    pass#TODO

class Schemeparser(Parser):
    """
    Parser for Scheme Strings. More details about 'Scheme' format, check
    https://groups.csail.mit.edu/mac/ftpdir/scheme-7.4/doc-html/scheme_2.html
    """
    def __init__(self, equationStr):
        self._eqs = equationStr
        self.ast, self.functions, self. = self._parse(equationStr)

    def _parse(self, equationStr):
        """
        parses Scheme Strings into AST. eqs must be in 'Scheme' format.
        Each term starts with '(' and ends with ')'.
        After the first '(', is the procedure name, than a space
        Then followed by arguments, which can be a term or primitive, delimited by space.

        :param equationStr: the equation string to be parsed
        :type equationStr: str
        :return: tuple of
            - ast (Abstract Syntax Tree), map, key:tuple(label, id), value:list[tuple[label, id]]
            - functionsD (map from function_label_str to number of such functions there are in the equation
            - variablesD (map from variable_label_str to number of such variables there are in the equation
            - primitives (amount of primitives there are in the equation
            - totalNodeCount (total number of nodes in the ast)
        :rtype: tuple[
            dict[tuple[str, int], list[tuple[str, int]]],
            dict[str, int],
            dict[str, int],
            int,
            int]
        """
        functionsD = {}# function(str) to no_of_such_functions in the ast(int)
        variablesD = {}# variable(str) to no_of_such_variables in the ast(int)
        primitives = 0#count of the number of primitives in the ast
        totalNodeCount = 0# total number of nodes in the ast
        backtracker = self._recursiveParse(equationStr) # return pointer to the root ( in process/thread memory)
        ast = {}
        stack = [backtracker]
        id = 0
        while len(stack) != 0:
            current = stack.pop()
            #do the tabulating
            totalNodeCount += 1
            if isFloat(current.label):
                primitives += 1
            elif current.label in Function.FUNC_NAMES: # is a function
                functionsD[current.label] = functionsD.get(current.label, 0) + 1
            else: # is a variable
                variablesD[current.label] = variablesD.get(current.label, 0) + 1
            #end of tabulating
            node = (current.label, id)
            ast[node] = ast.get(node, []) + current.neighbours
            id += 1
            for neighbour in current.neighbours:# neighbour is a backtracker
                stack.append(neighbour)
        return ast, functionsD, variablesD, primitives, totalNodeCount

    def _recursiveParse(self, eqs):
        """
        Handles the syntex of 'Scheme', but just stores the tree in the memory stack of the process/thread

        :param eqs: the equation string to be parsed
        :type eqs: str
        :return: root of the AST
        :rtype: :class:`Backtracker`
        """
        if (eqs.startswith('(') and not eqs.endswith(')')) or \
                (not eqs.startswith('(') and eqs.endswith(')')):
            raise Exception('Closing Brackets Mismatch')

        if eqs.startswith('('): # then it is a procedure
            strippedEqs = eqs[1:-1] # remove start and end brackets
            #find procedure label and end position of procedure label
            procedureLabel = ''
            procedureEndPosition = None
            for idx, c in enumerate(strippedEqs):
                if c == ' ': # is a space...
                    procedureEndPosition = idx
                    break
                procedureLabel += c
            argumentsStr = strippedEqs[procedureEndPosition]
            #find individual arguments
            bracketCounter = 0 #+1 for '(', -1 for ')'
            currentArgumentStr = ''
            arguments = []
            for c in argumentsStr:
                currentArgumentStr += c
                if c == '(':
                    bracketCounter += 1
                elif c == ')':
                    bracketCounter -= 1
                if bracketCounter == 0 and c == ' ': # (brackets are balanced) and this character c is a space
                    arguments.append(currentArgumentStr)
                    currentArgumentStr = ''
            rootNode = Backtracker(
                procedureLabel, # label
                list(map(lambda argu: self._recursiveParse(argu), arguments)), # neighbours
                None,# not used, argumentIdx
                None, #not used, prev
                None, #not used, id
            )
        else:#primitive or variable
            rootNode = Backtracker(
                eqs, # label
                [], # neighbours
                None, # not used, argumentIdx
                None, # not used, prev
                None # not used, id
            )
        return rootNode

    def _unparse(self, abstractSyntaxTree):
        pass #TODO