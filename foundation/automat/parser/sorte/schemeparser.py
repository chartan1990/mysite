from foundation.automat.arithmetic.function import Function
from foundation.automat.common import Backtracker, findAllMatches, isNum, lenOrZero
from foundation.automat.parser.parser import Parser

class Schemeparser(Parser):
    """
    Naive Parser for Scheme Strings. More details about 'Scheme' format, check
    https://groups.csail.mit.edu/mac/ftpdir/scheme-7.4/doc-html/scheme_2.html
    """
    def __init__(self, equationStr=None, verbose=False, veryVerbose=False, ast=None):
        if ast is None:
            self._eqs = equationStr
            self.verbose = verbose
            self.veryVerbose = veryVerbose
            self.equalTuple = None
            self.ast, self.functions, self.variables, self.primitives, self.totalNodeCount = self._parse()
        else:
            self.ast = ast

    def _parse(self):
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
        backtrackerRoot = self._recursiveParse(self._eqs, 0) # return pointer to the root ( in process/thread memory)
        if self.verbose:
            print('return from _recursiveParse*************')
        ast = {}
        if self.verbose:
            print(f'return from _recursiveParse************* initialised ast: {ast}')
        currentId = 0
        stack = [{'bt':backtrackerRoot, 'tid':currentId}]
        while len(stack) != 0:
            currentBt = stack.pop(0)
            tid = currentBt['tid']
            current = currentBt['bt']
            if self.verbose:
                print(f'label: {current.label}, argumentIdx: {current.argumentIdx}, id: {current.id}, tid:{tid}')
            #do the tabulating
            totalNodeCount += 1
            if isNum(current.label):
                primitives += 1
            elif current.label in Function.FUNC_NAMES: # is a function
                functionsD[current.label] = functionsD.get(current.label, 0) + 1
            else: # is a variable
                variablesD[current.label] = variablesD.get(current.label, 0) + 1
            #end of tabulating
            #node = (current.label, id)
            #ast[node] = ast.get(node, []) + current.neighbours
            #id += 1
            thisNodeId = currentId
            neighbourNodes = []
            for neighbour in sorted(current.neighbours, key=lambda neigh: neigh.argumentIdx, reverse=False):
                currentId += 1
                neighbourNodes.append((neighbour.label, currentId))
                stack.append({'bt':neighbour, 'tid':currentId})
            currentNode = (current.label, (current.argumentIdx, current.id))
            if self.verbose:
                print(f'ast: {ast}, currentNode: {currentNode}')
            if len(neighbourNodes) > 0: # avoid putting leaves as keys
                ast[(current.label, tid)] = neighbourNodes

        return ast, functionsD, variablesD, primitives, totalNodeCount

    def _recursiveParse(self, eqs, level):
        """
        Handles the syntex of 'Scheme', but just stores the tree in the memory stack of the process/thread

        :param eqs: the equation string to be parsed
        :type eqs: str
        :param level: tree level
        :type level: int
        :return: root of the AST
        :rtype: :class:`Backtracker`
        """
        if self.verbose:
            print(f'recursive level: {level}, eqs: {eqs}')
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
            argumentsStr = strippedEqs[procedureEndPosition:].strip()
            if self.verbose:
                print(f'argumentsStr: {argumentsStr}')
            #find individual arguments START
            bracketCounter = 0 #+1 for '(', -1 for ')'
            currentArgumentStr = ''
            arguments = []
            for c in argumentsStr:
                if self.veryVerbose:
                    print(c, currentArgumentStr, c == ' ', bracketCounter == 0, '<<<<<<<<<<<<<<12<<<<<<<<<')  
                currentArgumentStr += c
                if c == '(':
                    bracketCounter += 1
                elif c == ')':
                    bracketCounter -= 1
                if c == ' ' and bracketCounter == 0: # (brackets are balanced) and this character c is a space
                    if self.veryVerbose:
                        print(c, currentArgumentStr, c == ' ', bracketCounter == 0, '<<<<<<<<<<<<<<<<<<<<<<<')
                    currentArgumentStr = currentArgumentStr.strip()
                    if len(currentArgumentStr) > 0:
                        arguments.append(currentArgumentStr)
                        currentArgumentStr = ''
            if len(currentArgumentStr) > 0: # left-overs, please eat!
                arguments.append(currentArgumentStr)
            #find individual argumets END
            if self.verbose:
                print(f'level: {level}, arguments: {arguments}')
            neighbours = []
            for argumentIdx, backtrackNeighbour in enumerate(map(lambda argu: self._recursiveParse(argu, level+1), arguments)):
                if self.verbose:
                    print(f'recursive level: {level}, eqs: {eqs}, argumentIdx: {argumentIdx}, id: {backtrackNeighbour.id}, label: {backtrackNeighbour.label}')
                backtrackNeighbour.argumentIdx = argumentIdx
                neighbours.append(backtrackNeighbour)
            rootNode = Backtracker(
                procedureLabel, # label
                neighbours, # neighbours
                0,#  argumentIdx, will be set by calling process (self._recursiveParse)
                None, #prev, not used
                level, #id,   (depthId)
            )
            #for backtrackNeighbour in neighbours:
            #    backtrackNeighbour.prev = rootNode

        else:#primitive or variable
            rootNode = Backtracker(
                eqs, # label
                [], # neighbours
                0, # not used, argumentIdx
                None, # not used, prev
                level # not used, id
            )
        return rootNode

    def _findEqualTuple(self):
        self.equalTuple = None
        for keyTuple in self.ast.keys():
            if keyTuple[0] == '=':
                self.equalTuple = keyTuple


    def _unparse(self):
        """

        :param abstractSyntaxTree:
        :type abstractSyntaxTree:
        """
        #find the (=, id)
        if self.equalTuple is None:
            self._findEqualTuple()
        if self.equalTuple is None:#noch equalTuple kann nicht finden
            raise Exception('No equal, Invalid Equation String')
        return self._recursiveUnparse(self.ast, self.equalTuple)

    def _recursiveUnparse(self, subAST, keyTuple):
        if keyTuple not in subAST: # is Leaf
            return keyTuple[0] # return the key, discard the ID
        argumentStr = ' '.join([self._recursiveUnparse(subAST, argumentTuple) for argumentTuple in subAST[keyTuple]])
        return f"({keyTuple[0]} {argumentStr})"


    def _toLatex(self):
        """
        #~ DRAFT ~#
        We convert self.ast to a Latex_AST...

        Die Verschiedenen, den wir vorsichtiger merken mussen:
        [Scheme] => `Latex`
        1. [nroot] => `\\sqrt[n]`
        2. [/] => `\\frac`
        3. [(log a )] => `\\log` {if a = 10} or `\\ln` {if a = e} or `\\log_{a}`


        We also need to fill up the 
        1. self.leaves
        2. self.backslashes
        both are list, and each item within, looks like this:
        {
            'argument1SubSuper':'',
            'argument1OpenBracket':'{',
            'argument1CloseBracket':'}',
            'hasArgument1':True,
            'argument2SubSuper':'',
            'argument2OpenBracket':'',
            'argument2CloseBracket':'',
            'hasArgument2':False
        }

        Then we call the _unparse function of Latex to get the NICESWEETSTRING
        """
        ##TODO check if self.leaves and self.backslashes are initialised
        ##TODO if not initialise here
        self.schemeToLatexAST = copy.deepcopy(self.ast)
        queue = [self.equalTuple]
        while len(queue) != 0:
            currentTuple = queue.pop()
            arguments = self.schemeToLatexAST[currentTuple]
            #####verandern den Verschiedenen, den wir vorhin gesagt haben
            newName = currentTuple[0] # default is we do not change the original
            if currentTuple[0] == 'nroot':
                newName = 'sqrt'
            elif currentTuple[0] == '/':
                newName = 'frac'
            elif currentTuple[0] == 'log':
                if arguments[0] == 'e':
                    newName = 'ln'
            #####
            for argument in arguments:
                ###check if arguments are leaves=variables/numbers
                ###use (1)primitives , or (2)variablesD
                ###primitives: isNum(current.label)
                ###variablesD: dict(name):count
                ###fill up self.leaves ...
                ###self.leaves = set()
                name = argument[0]
                if isNum(name) or name in variablesD: # is primitive
                    self.leaves.add(name)

                ###TODO use functionsD
                ###TODO functionsD: dict(name):count
                ###TODO fill up self.backslashes ...
                """
                self.backslashes = list
                each item:
                {
                    'argument1SubSuper':'_',
                    'argument1OpenBracket':'{',
                    'argument1CloseBracket':'}',
                    'hasArgument1':,
                    'argument2SubSuper':'^',
                    'argument2OpenBracket':'',
                    'argument2CloseBracket':'',
                    'hasArgument2':
                }
                """
                if name in functionsD:
                    #TODO need to break into cases... TODO good to refactor this into a common helper for latexparser._findBackSlashPositions
                    newName = name
                    if name =='nroot':
                        newName = 'sqrt'
                        #if arg1 is 2, then hasArgument1 == False
                        #else argument1OpenBracket = [
                        if str(arguments[0]) == '2':
                            argument1SubSuper = ''
                            argument1OpenBracket = ''
                            argument1CloseBracket = ''
                            hasArgument1 = False
                            argument2SubSuper = ''
                            argument2OpenBracket = '' if len(arguments[1]) <= 1 else '{'
                            argument2CloseBracket = '' if len(arguments[1]) <= 1 else '}'
                            hasArgument2 = True
                        else:
                            argument1SubSuper = ''
                            argument1OpenBracket = '' if len(arguments[0]) <= 1 else '[' # brackets only if argument length more than 1
                            argument1CloseBracket = '' if len(arguments[0]) <= 1 else ']'
                            hasArgument1 = True
                            argument2SubSuper = ''
                            argument2OpenBracket = '' if len(arguments[1]) <= 1 else '{'
                            argument2CloseBracket = '' if len(arguments[1]) <= 1 else '}'
                            hasArgument2 = True

                    elif name == '^' and arguments[0] in Function.TRIGONOMETRIC_NAMES(): #to check for trigpower
                        #no need to map name, since for latex, we restrict to Function.TRIGONOMETRIC_NAMES
                        #need to check for power of trigofunction.... need to re-order AST....
                        trigNode = arguments[0]
                        trigPowerNode = arguments[1]
                        #re-order AST
                        trigArg = self.schemeToLatexAST[trigNode][0]
                        self.schemeToLatexAST[trigNode] = [trigPowerNode, trigArg]
                        del self.schemeToLatexAST[currentTuple]
                    elif name == 'log':
                        #if arg1 is 10, then hasArgument1 == False
                        #if arg1 is e, then hasArgument1 == False (the renaming of log => ln, is done earlier)
                        #else argument1OpenBracket = {, argument1SubSuper = _
                        if str(arguments[0]) == '10':
                            argument1SubSuper = ''
                            argument1OpenBracket = ''
                            argument1CloseBracket = ''
                            hasArgument1 = False
                            argument2SubSuper = ''
                            argument2OpenBracket = '' if len(arguments[1]) <= 1 else '{'
                            argument2CloseBracket = '' if len(arguments[1]) <= 1 else '}'
                            hasArgument2 = True
                        elif arguments[0] == 'e':
                            newName = 'ln'
                            argument1SubSuper = ''
                            argument1OpenBracket = ''
                            argument1CloseBracket = ''
                            hasArgument1 = True
                            argument2SubSuper = ''
                            argument2OpenBracket = '' if len(arguments[1]) <= 1 else '{'
                            argument2CloseBracket = '' if len(arguments[1]) <= 1 else '}'
                            hasArgument2 = True
                        else:
                            argument1SubSuper = '_'
                            argument1OpenBracket = '' if len(arguments[0]) <= 1 else '{' # brackets only if argument length more than 1
                            argument1CloseBracket = '' if len(arguments[0]) <= 1 else '}'
                            hasArgument1 = True
                            argument2SubSuper = ''
                            argument2OpenBracket = '' if len(arguments[1]) <= 1 else '{'
                            argument2CloseBracket = '' if len(arguments[1]) <= 1 else '}'
                            hasArgument2 = True

                    elif name == '/': # frac
                        newName = 'frac'
                        argument1SubSuper = ''
                        argument1OpenBracket = '{'
                        argument1CloseBracket = '}'
                        hasArgument1 = True
                        argument2SubSuper = ''
                        argument2OpenBracket = '{'
                        argument2CloseBracket = '}'
                        hasArgument2 = True
                    self.backslashes[newName].append({
                        'argument1SubSuper':argument1SubSuper,
                        'argument1OpenBracket':argument1OpenBracket,
                        'argument1CloseBracket':argument1CloseBracket,
                        'hasArgument1':hasArgument1,
                        'argument2SubSuper':argument2SubSuper,
                        'argument2OpenBracket':argument2OpenBracket,
                        'argument2CloseBracket':argument2CloseBracket,
                        'hasArgument2':hasArgument2
                    })
                queue.append(argument)
        #latexparser = Latexparser("") # we cannot put empty.... TODO need some reconfiguring of code structure of Latexparser
        #latexparser._unparse(self.schemeToLatexAST) #TODO, Latexparser._unparse does not take external arguments...