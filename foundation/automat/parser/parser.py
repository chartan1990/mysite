from abc import ABC

from foundation.automat.common import Backtracker, isFloat
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
        'html':'Htmlparser'
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
        ast, functions, variables, primitives, totalNodeCount = parser._parse()
        return ast, functions, variables, primitives, totalNodeCount



class Htmlparser(Parser):
    """
https://www.w3.org/1998/Math/MathML/

Example (this is similiar to latex...)

<img src="https://wikimedia.org/api/rest_v1/media/math/render/svg/95b72ff2accd775d082d041434acf09b4b7523f4" class="mwe-math-fallback-image-inline mw-invert skin-invert" aria-hidden="true" style="vertical-align: -6.171ex; width:22.568ex; height:13.509ex;" alt="{\displaystyle {\begin{aligned}I_{\text{E}}&amp;=I_{\text{ES}}\left(e^{\frac {V_{\text{BE}}}{V_{\text{T}}}}-1\right)\\I_{\text{C}}&amp;=\alpha _{\text{F}}I_{\text{E}}\\I_{\text{B}}&amp;=\left(1-\alpha _{\text{F}}\right)I_{\text{E}}\end{aligned}}}">
<img alt=alt="{\displaystyle {\begin{aligned}I_{\text{E}}&amp;=I_{\text{ES}}\left(e^{\frac {V_{\text{BE}}}{V_{\text{T}}}}-1\right)\\I_{\text{C}}&amp;=\alpha _{\text{F}}I_{\text{E}}\\I_{\text{B}}&amp;=\left(1-\alpha _{\text{F}}\right)I_{\text{E}}\end{aligned}}}">
    

https://developer.mozilla.org/en-US/docs/Web/MathML/Element/math
    """
    def __init__(self, equationStr, verbose=False):
        self._eqs = equationStr
        self.verbose = verbose


class Latexparser(Parser):
    """
    Naive Parser for Latex Strings. More details about 'Latex' format, check
    https://www.latex-project.org/help/documentation/classes.pdf

    According to :- https://sg.mirrors.cicku.me/ctan/info/symbols/comprehensive/symbols-a4.pdf

    $ % _ } & # {  are special characters, 
    we will pretend that %, & and # does not exist, since we are not doing matrices for now

    Also according to https://www.overleaf.com/learn/latex/Learn_LaTeX_in_30_minutes#Adding_math_to_LaTeX
    we need to enclose the MATH equation with one of these:
    1. \[ \]
    2. $ $
    3. \begin{displaymath} \end{displaymath}
    4. \begin{equation} \end{equation}

    But we will assume that there is no need for that now, and only when user execute toString, 
    will we return with enclosed \[\]
    """
    INFIX = ['+', '-', '*', '/']
    OPEN_BRACKETS = ['{', '[', '(']
    CLOSE_BRACKETS = ['}', ']', ')']
    close__open = dict(zip(OPEN_BRACKETS, CLOSE_BRACKETS))

    def __init__(self, equationStr, verbose=False):
        self._eqs = equationStr
        self.verbose = verbose

    def _parse(self):
        """
        First we convert all the infix-operators to LaTex-styled prefix operators:
        A+B ==> \+{A}{B}
        A-B ==> \-{A}{B}
        A*B ==> \*{A}{B}
        A/B ==> \/{A}{B}
        """
        #convert all the infix-operators to LateX
        #find all the positions of the infixes, and if there are round/square/curly brackets beside them...
        openBracketsLocation = dict(map(lambda openBracket: (openBracket, []), Latexparser.OPEN_BRACKETS))
        matchingBracketsLocation = []
        #infixOperatorPositions = dict(map(lambda infixOp: (infixOp, []), Latexparser.INFIX))
        for idx in enumerate(self._eqs):
            c = self._eqs[idx]
            if c in Latexparser.OPEN_BRACKETS:
                openBracketsLocation[c].append(idx) # this acts as a stack
            elif c in Latexparser.CLOSE_BRACKETS:
                matchingOpenBracketPos = openBracketsLocation[close__open[c]].pop(len(openBracketsLocation[c])-1) # take out from the bottom like a stack
                matchingBracketsLocation.append({'openBracketType':close__open[c], 'startPos':matchingOpenBracketPos, 'endPos':idx})
            elif c in Latexparser.INFIX:
                infixOperatorPositions[c].append({
                    'position':idx,
                    'leftCloseBracket':self._eqs[idx-1] if idx>0 and (self._eqs[idx-1] in Latexparser.CLOSE_BRACKETS) else None,
                    'rightOpenBracket':self._eqs[idx+1] if idx<len(self._eqs)-2 and (self._eqs[idx+1] in Latexparser.OPEN_BRACKETS) else None
                })
        #check for error, if there are any left-over brackets in any of the stacks, then there is unbalanced brackets
        mismatchedOpenBrackets = []
        for openBracket, bracketPosStack in openBracketsLocation.items():
            if len(openBracketLocation) > 0:
                mismatchedOpenBrackets.append(openBracket)
        if len(mismatchedOpenBrackets) > 0:
            raise Exception(f'Mismatched brackets: {mismatchedOpenBrackets}')
        newInfixOperatorPositions = copy.deepcopy(infixOperatorPositions)
        for openBracket, infoDict in infixOperatorPositions.items():
            #find left_bracket_positions (if any), find right_bracket_positions (if any), find tightest enclosing brackets, if any
            currentEnclosingBracketPos = {'startPos':-1, 'endPos':len(self._eqs), 'openBracketType':None}
            for infoDictMatchingBracketLoc in matchingBracketsLocation:
                #for finding tightest enclosing brackets
                if infoDictMatchingBracketLoc['startPos'] <= infoDict['position'] and infoDict['position'] <= infoDictMatchingBracketLoc['endPos']: # is enclosed by infoDictMatchingBracketLoc
                    if currentEnclosingBracketPos['startPos'] <= infoDictMatchingBracketLoc['startPos'] and infoDictMatchingBracketLoc['endPos'] <= currentEnclosingBracketPos['endPos']: #is a tighter bracket, then recorded on currentEnclosingBracketPos
                        currentEnclosingBracketPos['startPos'] = infoDictMatchingBracketLoc['startPos']
                        currentEnclosingBracketPos['endPos'] = infoDictMatchingBracketLoc['endPos']
                        currentEnclosingBracketPos['openBracketType'] = infoDictMatchingBracketLoc['openBracketType']
                #for finding bracket positions left of infixOp (for the swapping)... up til enclosing bracket?
                #for finding bracket positions right of infixOp (for the swapping)... up til enclosing bracket?
            #update newInfixOperatorPositions
        infixOperatorPositions = newInfixOperatorPositions
        #all pairs of infixOperatorPositions, form tree (relationship is who encloses who)
        #give level to all the nodes
        #swap the node from the same level together, rightmost to left most (minimise updates needed), BODMAS 








class Schemeparser(Parser):
    """
    Parser for Scheme Strings. More details about 'Scheme' format, check
    https://groups.csail.mit.edu/mac/ftpdir/scheme-7.4/doc-html/scheme_2.html
    """
    def __init__(self, equationStr, verbose=False, veryVerbose=False):
        self._eqs = equationStr
        self.verbose = verbose
        self.veryVerbose = veryVerbose
        self.ast, self.functions, self.variables, self.primitives, self.totalNodeCount = self._parse(equationStr)

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
            if isFloat(current.label):
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

    def _unparse(self):
        """

        :param abstractSyntaxTree:
        :type abstractSyntaxTree:
        """
        #find the (=, id)
        equalTuple = None
        for keyTuple in self._ast.keys():
            if keyTuple[0] == '=':
                equalTuple = keyTuple
                break
        if equalTuple is None:
            raise Exception('No equal, Invalid Equation String')
        return self._recursiveUnparse(self._ast, equalTuple)

    def _recursiveUnparse(self, subAST, keyTuple):
        if keyTuple not in subAST: # is Leaf
            return keyTuple[0] # return the key, discard the ID
        argumentStr = ' '.join([self._recursiveUnparse(subAST, argumentTuple) for argumentTuple in subAST[keyTuple]])
        return f"({keyTuple[0]} {argumentStr})"


if __name__=='__main__':

    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    eqs = 'a+b=c'
    latexParser = Latexparser(eqs, verbose=True)
    ast = latexParser.ast
    print('*********ast:')
    pp.pprint(ast)
    """
    ast = {
    ('=', 0):[(('a', 1), ('+', 2)],
    ('+', 2):[('b', 3), ('c', 4)]
    }
    """
    unparsedStr = latexParser._unparse()
    print(f'***********unparsedStr: modorimashitaka: {eqs==unparsedStr}')
    print(unparsedStr)

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

