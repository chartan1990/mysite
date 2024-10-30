from abc import ABC
from copy import copy
import multiprocessing as mp # TODO for Django, we might need to re-int  Django

from foundation.automat.common import Backtracker, findAllMatches, isFloat
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

    More concise guide to LaTeX mathematical symbols (courtsey of Rice University):
    https://www.cmor-faculty.rice.edu/~heinken/latex/symbols.pdf
    offline copy in parser.docs as "symbols.pdf"

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
    INFIX = ['+', '-', '*', '/', '^'] # somehow, exponential is an infix IN LATEX too. \tan^{power}(\theta), need to reconcile backslash and infix....
    OPEN_BRACKETS = ['{', '[', '(']
    CLOSE_BRACKETS = ['}', ']', ')']
    close__open = dict(zip(CLOSE_BRACKETS, OPEN_BRACKETS))
    open__close = dict(zip(OPEN_BRACKETS, CLOSE_BRACKETS))

    VARIABLENAMESTAKEANARG = ['overline', 'underline', 'widehat', 'widetilde', 'overrightarrow', 'overleftarrow', 'overbrace', 'underbrace'
    #Math mode accents
    'acute', 'breve', 'ddot', 'grave', 'tilde', 'bar', 'check', 'dot', 'hat', 'vec'
    ] # these 'functions' must be preceded by {
    TRIGOFUNCTION = ['arccos', 'cos', 'arcsin', 'sin', 'arctan', 'tan', 
    'arccsc', 'csc', 'arcsec', 'sec', 'arccot', 'cot', 'arsinh', 'sinh', 'arcosh', 'cosh', 
    'artanh', 'tanh', 'arcsch', 'csch', 'arsech', 'sech', 'arcoth', 'coth']
    FUNCTIONNAMES = TRIGOFUNCTION + ['frac', 'sqrt',  'log', 'ln'] #+ ['int', 'oint', 'iint'] # TODO this is important... but i am weak now

    def __init__(self, equationStr, verbose=False):
        self._eqs = equationStr
        self.verbose = verbose
        """
        From ChatGPT:
        multiprocessing.Value:

        'b': signed char (integer, 1 byte)
        'B': unsigned char (integer, 1 byte)
        'h': signed short (integer, 2 bytes)
        'H': unsigned short (integer, 2 bytes)
        'i': signed int (integer, typically 4 bytes)
        'I': unsigned int (integer, typically 4 bytes)
        'l': signed long (integer, typically 4 bytes)
        'L': unsigned long (integer, typically 4 bytes)
        'q': signed long long (integer, 8 bytes)
        'Q': unsigned long long (integer, 8 bytes)
        'f': float (single-precision, typically 4 bytes)
        'd': double (double-precision, typically 8 bytes)
        """
        self.lock__findVariablesFunctionsPositions = mp.Lock()
        self.lock__findInfixAndEnclosingBrackets = mp.Lock()



    def _findVariablesFunctionsPositions(self):
        """
        this is done with :

        https://www.cmor-faculty.rice.edu/~heinken/latex/symbols.pdf
        offline copy in parser.docs as "symbols.pdf"

        as requirements.

        From the requirements, we leave these as FUTUREWORK:
        1. all the "Delimiters" 
        2. all the "Binary Operation/Relation Symbols"
        3. all the "Arrow symbols"
        4. all the "Variable-sized symbols"
        5. all the "Miscellaneous symbols"
        6. the double-functioned variables of "Math mode accents" like: \Acute{\Acute{}}
        7. "Array environment, examples" (will be neccesary later for matrices... TODO)
        8. "Other Styles (math mode only)"
        9. "Font sizes"


        From the requirements, we ignore these:
        1. all the "Text Mode: Accents and Symbols" 
        """
        self.lock__findVariablesFunctionsPositions.acquire(block=True, timeout=300) # others are waiting for you...
        self.variablesPos = [] # str, startPos, endPos,
        self.functionPos = [] # functionName, startPos, endPos, _, ^, arguments

        #find \\functionName with regex (neater than character-by-character)
        for reMatch in findAllMatches('\\\\([a-zA-Z]+)', self._eqs): #capturing group omit the backslash
            positionTuple = reMatch.span()
            labelName = reMatch.groups()[0] # if use group, it comes with \\ at the front, not sure why
            if self.verbose:
                print('labelName', labelName, '<<<<<<')
                print('positionTuple', positionTuple, '<<<<<')
            if labelName in Latexparser.VARIABLENAMESTAKEANARG: # it is actually a special kind of variable
                if self._eqs[positionTuple[1]] != '{':
                    raise Exception(f'after {labelName} should have {{')
                argument1StartPosition = positionTuple[1]+1 # because of the {
                closingCurlyBracketPos = self._eqs.index('}', argument1StartPosition)
                argument1 = self._eqs[argument1StartPosition:closingCurlyBracketPos]
                argument1EndPosition = closingCurlyBracketPos
                self.variablesPos.append({
                    'name':labelName,
                    'startPos':positionTuple[0],
                    'endPos':positionTuple[1],
                    'argument1':argument1,
                    'argument1StartPosition':argument1StartPosition,
                    'argument1EndPosition':argument1EndPosition,
                    'argument1BracketType':'{',
                    'type':'backslash'
                })
            elif labelName in Latexparser.FUNCTIONNAMES: #all the function that we accept, TODO link this to automat.arithmetic module
                """
                sqrt - \sqrt[rootpower]{rootand} # note if rootand is a single character, then curly braces are not needed, if no rootpower, then rootpower=2
                trig - \tan^{power}(Any) # note if power is a single character, then curly braces are not needed 
                ln - \ln(Any)
                frac - \frac{numerator}{denominator} # note if numerator/denominator is single character, then curly braces are not needed 
                log - \log_{base}(Any) # note if base is a single character, then curly braces are not needed
                (TODO hereon not done)
                One may or may not specify d... at the end of the integral...
                int - \int_{}^{} \int^{}_{} \int_{} \int^{} \int, not if numerator/denominator is single character, then curly braces are not needed
                iint - \iint_{}^{} \iint^{}_{} \iint_{} \iint^{} \iint, not if numerator/denominator is single character, then curly braces are not needed
                iiint - \iiint_{}^{} \iiint^{}_{} \iiint_{} \iiint^{} \iiint, not if numerator/denominator is single character, then curly braces are not needed
                oint - \int_{}^{} \int^{}_{} \int_{} \int^{} \int, not if numerator/denominator is single character, then curly braces are not needed
                """
                argument1 = None
                argument1StartPosition = None
                argument1EndPosition = None
                argument1BracketType = None
                argument2 = None
                argument2StartPosition = None
                argument2EndPosition = None
                argument2BracketType = None
                if labelName == 'sqrt':
                    if self._eqs[positionTuple[1]] == '[': # then we need to capture the rootpower as an argument
                        argument1StartPosition = positionTuple[1]+1
                        closingSquareBracketPos = self._eqs.index(']', argument1StartPosition)
                        argument1 = self._eqs[argument1StartPosition:closingSquareBracketPos] # argument1 == rootpower
                        argument1EndPosition = closingSquareBracketPos
                        argument1BracketType = '['
                        nextPos = argument1EndPosition + 1 #because of the ]
                    else:
                        argument1StartPosition = None
                        argument1 = 2 # default rootpower is square root
                        argument1EndPosition = None
                        nextPos = positionTuple[1]
                    if self._eqs[nextPos] != '(': #TODO this is not true
                        raise Exception('Sqrt functions must be succeded by (')
                    argument2StartPosition = nextPos+1
                    closingRoundBracketPos = self._eqs.index(')', argument2StartPosition)
                    argument2 = self._eqs[argument2StartPosition:closingRoundBracketPos] # argument2 == rootand
                    argument2EndPosition = closingRoundBracketPos
                    argument2BracketType = '('
                elif labelName in Latexparser.TRIGOFUNCTION:
                    nextPos = positionTuple[1]# default if there is no ^
                    if self._eqs[positionTuple[1]] == '^': # then we need to capture the power as an argument
                        if self._eqs[positionTuple[1]+1] == '{': # we need to find the close curly and take everything in between as arg1
                            argument1StartPosition = positionTuple[1]+2
                            closingCurlyBracketPos = self._eqs.index('}', argument1StartPosition)
                            argument1 = self._eqs[argument1StartPosition:closingCurlyBracketPos]# argument1 == power
                            argument1EndPosition = closingCurlyBracketPos
                            nextPos = argument1EndPosition + 1 # because of curly bracket }
                            argument1BracketType = '{'
                        else: # must be followed by a single character
                            argument1StartPosition = positionTuple[1]+1
                            argument1EndPosition = positionTuple[1]+2
                            argument1 = self._eqs[argument1StartPosition:argument1EndPosition]
                            nextPos = argument1EndPosition
                    #must be followed by round brackets.
                    if self.verbose:
                        print(self._eqs[nextPos], 'TRIG succedor')
                    if self._eqs[nextPos] != '(':
                        raise Exception('Trignometric functions must be succeded by (')
                    argument2StartPosition = nextPos+1
                    closingRoundBracketPos = self._eqs.index(')', argument2StartPosition)
                    argument2 = self._eqs[argument2StartPosition:closingRoundBracketPos] # argument2 == angle
                    argument2EndPosition = closingRoundBracketPos
                    argument2BracketType = '('
                elif labelName == 'ln':
                    argument1StartPosition = None
                    argument1 = 'e' # defintion of natural log
                    argument1EndPosition = None
                    if self._eqs[positionTuple[1]] != '(':
                        raise Exception('Natural Log must be succeded by (')
                    argument2StartPosition = positionTuple[1]+1
                    closingRoundBracketPos = self._eqs.index(')', argument2StartPosition)
                    argument2 = self._eqs[argument2StartPosition:closingRoundBracketPos] # argument1 == logged
                    argument2EndPosition = closingRoundBracketPos
                    argument2BracketType = '('
                elif labelName == 'frac': # TODO here could be differentiation here...
                    # must have 2 curly brackets
                    if self._eqs[positionTuple[1]] != '{':
                        raise Exception('Frac must be succeded by {') # complain if cannot find first curly bracket
                    argument1StartPosition = positionTuple[1]+1
                    closingCurlyBracketPos = self._eqs.index('}', argument1StartPosition)
                    argument1 = self._eqs[argument1StartPosition:closingCurlyBracketPos] # argument1 == numerator
                    argument1EndPosition = closingCurlyBracketPos
                    argument1BracketType = '{'
                    if self._eqs[argument1EndPosition+1] != '{':
                        raise Exception('Frac numerator must be succeded by {') # complain if cannot find second curly bracket
                    argument2StartPosition = argument1EndPosition+2 # because of {
                    closingCurlyBracketPos = self._eqs.index('}', argument2StartPosition)
                    argument2 = self._eqs[argument2StartPosition:closingCurlyBracketPos] # argument2 == denominator
                    argument2EndPosition = closingCurlyBracketPos
                    argument2BracketType = '{'
                elif labelName == 'log':
                    #might not have {base} then we assume base=10
                    if self._eqs[positionTuple[1]] == '_': # user fixing the base of this log
                        if self._eqs[positionTuple[1]+1] == '{':
                            argument1StartPosition = positionTuple[1]+2
                            closingCurlyBracketPos = self._eqs.index('}', argument1StartPosition)
                            argument1 = self._eqs[argument1StartPosition:closingCurlyBracketPos] # argument1 == base
                            argument1EndPosition = closingCurlyBracketPos
                            argument1BracketType = '{'
                            nextPos = argument1EndPosition + 1
                        else: # expect a single character
                            argument1StartPosition = positionTuple[1]+1
                            argument1 = self._eqs[positionTuple[1]+1]
                            argument1EndPosition = positionTuple[1]+1
                            nextPos = argument1EndPosition
                    else:
                        argument1 = 10 # default base=10
                        nextPos = positionTuple[1]
                    if self.verbose:
                        print(self._eqs[nextPos], '<<<<<nextPos')
                    if self._eqs[nextPos] != '(':
                        raise Exception('Log must be succeded by (')
                    argument2StartPosition = nextPos+1
                    closingRoundBracketPos = self._eqs.index(')', argument2StartPosition)
                    argument2 = self._eqs[argument2StartPosition:closingRoundBracketPos] # argument2 == logant
                    argument2EndPosition = closingRoundBracketPos
                    argument2BracketType = '('
                else:
                    raise Exception(f'{labelName} is not implemented') # my fault.

                self.functionPos.append({
                    'name':labelName,
                    'startPos':positionTuple[0],
                    'endPos':positionTuple[1],
                    'argument1':argument1,
                    'argument1StartPosition':argument1StartPosition,
                    'argument1EndPosition':argument1EndPosition,
                    'argument1BracketType':argument1BracketType,
                    'argument2':argument2,
                    'argument2StartPosition':argument2StartPosition,
                    'argument2EndPosition':argument2EndPosition,
                    'argument2BracketType':argument2BracketType,
                    'type':'backslash'
                })
            else: #has a backspace, but we have not targeted it... , we assume that its a zero-argument == variable...
                self.variablesPos.append({
                        'name':labelName,
                        'startPos':positionTuple[0],
                        'endPos':positionTuple[1],
                        'type':'backslash',
                        'argument1':None,
                    })
        self.lock__findVariablesFunctionsPositions.release() # others are waiting for you...




    def _addImplicitMultiply(self):
        """
        some times there is no multiply operator in the equation str when there should be, tatoeba
        \sin(2x) = 2\sin(x)\cos(x)
        should have been
        \sin(2*x) = 2*\sin(x)*\cos(x)

        ChatGPT suggests 3 things to take note:
        1. variables/functions
        2. numbers
        3. parentheses
        """
        pass


    def _findInfixAndEnclosingBrackets(self):
        self.lock__findInfixAndEnclosingBrackets.acquire(block=True, timeout=300)
        #find all the positions of the infixes, and if there are round/square/curly brackets beside them...
        self.openBracketsLocation = dict(map(lambda openBracket: (openBracket, []), Latexparser.OPEN_BRACKETS))
        self.matchingBracketsLocation = []
        self.infixOperatorPositions = dict(map(lambda infixOp: (infixOp, []), Latexparser.INFIX))
        for idx, c in enumerate(self._eqs):
            if c in Latexparser.OPEN_BRACKETS:
                self.openBracketsLocation[c].append(idx) # this acts as a stack
            elif c in Latexparser.CLOSE_BRACKETS:
                o = Latexparser.close__open[c]
                matchingOpenBracketPos = self.openBracketsLocation[o].pop(len(self.openBracketsLocation[o])-1) # take out from the bottom like a stack
                self.matchingBracketsLocation.append({'openBracketType':o, 'startPos':matchingOpenBracketPos, 'endPos':idx})
                if self.verbose:
                    print('popped', matchingOpenBracketPos, 'remaining bracket:', self.openBracketsLocation[o])
            elif c in Latexparser.INFIX: # TODO need to include ^, but need to check if ^ is part of a backslash.
                self.infixOperatorPositions[c].append({
                    'position':idx,
                    'leftCloseBracket':self._eqs[idx-1] if idx>0 and (self._eqs[idx-1] in Latexparser.CLOSE_BRACKETS) else None,
                    'rightOpenBracket':self._eqs[idx+1] if idx<len(self._eqs)-2 and (self._eqs[idx+1] in Latexparser.OPEN_BRACKETS) else None
                })
        #check for error, if there are any left-over brackets in any of the stacks, then there is unbalanced brackets
        mismatchedOpenBrackets = []
        for openBracket, bracketPosStack in self.openBracketsLocation.items():
            if len(bracketPosStack) > 0:
                mismatchedOpenBrackets.append(openBracket)
        if len(mismatchedOpenBrackets) > 0:
            raise Exception(f'Mismatched brackets: {mismatchedOpenBrackets}')
        newInfixOperatorPositions = dict(map(lambda infixOp: (infixOp, []), Latexparser.INFIX))
        for openBracket, infoDictList in self.infixOperatorPositions.items():
            for infoDict in infoDictList:
                #find left_bracket_positions (if any), find right_bracket_positions (if any), find tightest enclosing brackets, if any
                currentEnclosingPos = {'startPos':-1, 'endPos':len(self._eqs), 'startSymbol':None, 'endSymbol':None}
                """
    # TODO binarySearch with sorted matchingBracketsLocations, may be faster with more brackets... EXPERIMENT: two different sets of code, find parametrised "Sweet Spot" to swap between code...
    https://en.wikipedia.org/wiki/Segment_tree
    #copy and paste:
    https://www.geeksforgeeks.org/segment-tree-efficient-implementation/
                """
                for infoDictMatchingBracketLoc in self.matchingBracketsLocation: 
                    #for finding tightest enclosing brackets
                    if self.verbose:
                        print(infoDict)
                    if infoDictMatchingBracketLoc['startPos'] <= infoDict['position'] and infoDict['position'] <= infoDictMatchingBracketLoc['endPos']: # is enclosed by infoDictMatchingBracketLoc
                        if currentEnclosingPos['startPos'] <= infoDictMatchingBracketLoc['startPos'] and infoDictMatchingBracketLoc['endPos'] <= currentEnclosingBracketPos['endPos']: #is a tighter bracket, then recorded on currentEnclosingBracketPos
                            currentEnclosingPos['startPos'] = infoDictMatchingBracketLoc['startPos']
                            currentEnclosingPos['endPos'] = infoDictMatchingBracketLoc['endPos']
                            currentEnclosingPos['startSymbol'] = infoDictMatchingBracketLoc['openBracketType']
                            currentEnclosingPos['endSymbol'] = open__close[infoDictMatchingBracketLoc['openBracketType']]
                    #if there are no enclosing brackets.... have to take the nearest infixOpPos....
                if currentEnclosingPos['startSymbol'] is None: # no enclosing Brackets, look for other infix
                    #for finding bracket positions left of infixOp (for the swapping)... nearest infixOpPos ? did i miss anything else
                    #we will iterate through the infix captured, instead of the entire formula again (usually less infix than characters in entire formula)
                    nearestLeftInfixInfo = {'symbol':None, 'position':-1}
                    nearestRightInfixInfo = {'symbol':None, 'position':len(self._eqs)}
                    for oOpenBracket, oInfoDictList in self.infixOperatorPositions.items():
                        for oInfoDict in oInfoDictList:
                            if nearestLeftInfixInfo['position'] <= oInfoDict['position']:
                                nearestLeftInfixInfo = {'symbol':oOpenBracket, 'position':oInfoDict['position']}
                            if nearestRightInfixInfo['position'] >= oInfoDict['position']:
                                nearestRightInfixInfo = {'symbol':oOpenBracket, 'position':oInfoDict['position']}
                    currentEnclosingPos['startPos'] = nearestLeftInfixInfo['position']
                    currentEnclosingPos['endPos'] = nearestRightInfixInfo['position']
                    currentEnclosingPos['startSymbol'] = nearestLeftInfixInfo['symbol']
                    currentEnclosingPos['endSymbol'] = nearestRightInfixInfo['symbol']
                #update newInfixOperatorPositions
                infoDict.update(currentEnclosingPos)
                newInfixOperatorPositions[openBracket].append(infoDict)
            self.infixOperatorPositions = newInfixOperatorPositions
            #TODO need to find the left and right arguments to do the swapping..
        self.lock__findInfixAndEnclosingBrackets.release()

    # def _findEnclosingBrackets(self):
    #     """
    #     a lot of the brackets belong to backslash function/variables...
    #     find unqiue set of brackets that are meant to enclosing terms.... (real brackets)

    #     """
    #     Condition(lock=self.lock__findVariablesFunctionsPositions).wait()# findVariablesFunctionsPositions should be processed first...
    #     Condition(lock=self.lock__findInfixAndEnclosingBrackets).wait()# depends on 
    #     self.enclosingBrackets = []
    #     for infoDictMatchingBracketLoc in self.matchingBracketsLocation: #{'openBracketType':, 'startPos':, 'endPos':}
    #         for variablePosDict in self.variablesPos:
    #             if 'argument1BracketType' in variablePosDict:
    #                 #check if equals infoDictMatchingBracketLoc
    #                 #if equals, record and break
    #             if 'argument2BracketType' in variablePosDict:
    #                 #check if equals infoDictMatchingBracketLoc
    #                 #if equals, record and break
    #         #if not found in variable, then search here
    #         for functionPosDict in self.functionPos:
    #             if 'argument1BracketType' in functionPosDict:
    #                 #check if equals infoDictMatchingBracketLoc
    #                 #if equals, record and break
    #             if 'argument2BracketType' in functionPosDict:
    #                 #check if equals infoDictMatchingBracketLoc
    #                 #if equals, record and break
    #         #if not equals, self.enclosingBracket.append() # thats it.


    def _formBackSlashEnclosureTree(self):
        """"""
        Condition(lock=self.lock__findVariablesFunctionsPositions).wait()# findVariablesFunctionsPositions should be processed first...
        Condition(lock=self.lock__findInfixAndEnclosingBrackets).wait()# depends on 
        #

    def _findParentChildDifferenceInEnclosureTree(self):
        pass


    def _infixToPrefix(self):
        """
        First we convert all the infix-operators to LaTex-styled prefix operators:
        A+B ==> \+{A}{B}
        A-B ==> \-{A}{B}
        A*B ==> \*{A}{B}
        A/B ==> \/{A}{B}
        """
        #convert all the infix-operators to LateX
        self._findInfixAndEnclosingBrackets() # TODO maybe just wait for it to complete using Lock
        #TODO should put into different methods for future parallelisation....

        #all pairs of infixOperatorPositions, form tree (relationship is who encloses who)
        enclosureTree = {}
        for openBracket_0, infoDict_0 in infixOperatorPositions.items():
            for openBracket_1, infoDict_1 in infixOperatorPositions.items():
                if infoDict_1['startPos'] <= infoDict_0['position'] and infoDict_0['position'] <= infoDict_1['endPos']: # 1 <= 0
                    existingChildren = enclosureTree.get(infoDict_1['position'], [])
                    existingChildren.append(infoDict_0['position'])
                    enclosureTree[infoDict_1['position']] = existingChildren
                elif infoDict_0['startPos'] <= infoDict_1['position'] and infoDict_1['position'] <= infoDict_0['endPos']: # 0 <= 1
                    existingChildren = enclosureTree.get(infoDict_0['position'], [])
                    existingChildren.append(infoDict_1['position'])
                    enclosureTree[infoDict_0['position']] = existingChildren
        #give level to all the nodes
        #find root... all roads(leaves/branch[anyNodePos]) lead to rome(root) [because its a tree.]
        anyNodePos = enclosureTree.items()[0][0] # key of the first item
        #just keep getting parent, until we reach root
        updated = True
        while updated:
            updated = False
            for pos, childenPos in enclosureTree.items():
                if anyNodePos in childenPos:
                    anyNodePos = pos
                    updated = True
        rootPos = anyNodePos
        #give level to all the nodes
        levelToPos = {}
        queue = [{'id':rootPos, 'level':0}]
        while len(queue) > 0:
            current = queue.pop(0)
            currentPoss = levelToPos.get(current['level'], [])
            currentPoss.append(current['id'])
            levelToPos[current['level']] = currentPoss
            for childPos in enclosureTree[current['id']]:
                queue.append({'id':childPos, 'level':current['level']+1})
        #swap the node from the same level together, rightmost to left most (minimise updates needed), BODMAS 
        for level, infixPos in sorted(levelToPos.items(), key=lambda item: item[0], reverse=True): # lowest level has the biggest number
            for infixOperatorPos in sorted(infixPos, reverse=True): # rightmost of equation has the largest index
                pass#swap
                #update... which DS....

    def _parse(self):
        self._findVariablesFunctionsPositions()
        self._addImplicitMultiply()
        self._infixToPrefix()
        #self._schemeStyledParsing()







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

    #import pprint
    #pp = pprint.PrettyPrinter(indent=4)
    #eqs = 'a+b=c'
    #latexParser = Latexparser(eqs, verbose=True)
    #ast = latexParser.ast
    #print('*********ast:')
    #pp.pprint(ast)
    """
    ast = {
    ('=', 0):[(('a', 1), ('+', 2)],
    ('+', 2):[('b', 3), ('c', 4)]
    }
    """
    #unparsedStr = latexParser._unparse()
    #print(f'***********unparsedStr: modorimashitaka: {eqs==unparsedStr}')
    #print(unparsedStr)

    #TODO