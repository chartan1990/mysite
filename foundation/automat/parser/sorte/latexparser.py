import inspect
import multiprocessing as mp # TODO for Django, we might need to re-int  Django

from foundation.automat.common import findAllMatches, isNum, lenOrZero, EnclosureTree
from foundation.automat.arithmetic.function import Function
from foundation.automat.parser.parser import Parser


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
    PRIOIRITIZED_INFIX = ['^', '/', '*', '-', '+']#['^', '/', '*', '-', '+'] # the smaller the number the higher the priority
    INFIX = PRIOIRITIZED_INFIX+['=']
    OPEN_BRACKETS = ['{', '[', '(']
    CLOSE_BRACKETS = ['}', ']', ')']
    close__open = dict(zip(CLOSE_BRACKETS, OPEN_BRACKETS))
    open__close = dict(zip(OPEN_BRACKETS, CLOSE_BRACKETS))

    VARIABLENAMESTAKEANARG = ['overline', 'underline', 'widehat', 'widetilde', 'overrightarrow', 'overleftarrow', 'overbrace', 'underbrace'
    #Math mode accents
    'acute', 'breve', 'ddot', 'grave', 'tilde', 'bar', 'check', 'dot', 'hat', 'vec'
    ] # these 'functions' must be preceded by {
    TRIGOFUNCTION = Function.TRIGONOMETRIC_NAMES() # then no need to map between latex and scheme
    """['arccos', 'cos', 'arcsin', 'sin', 'arctan', 'tan', 
    'arccsc', 'csc', 'arcsec', 'sec', 'arccot', 'cot', 'arsinh', 'sinh', 'arcosh', 'cosh', 
    'artanh', 'tanh', 'arcsch', 'csch', 'arsech', 'sech', 'arcoth', 'coth']"""
    FUNCTIONNAMES = TRIGOFUNCTION + ['frac', 'sqrt',  'log', 'ln'] #+ ['int', 'oint', 'iint'] # TODO this is important... but i am weak now

    def __init__(self, equationStr, verbose=False, parallelise=False):
        self._eqs = equationStr
        self.verbose = verbose
        self.alleDing = [] # collect all symbol after interlevelsubtreegrafting
        #method specfific verbosity
        self.methodVerbose = {
            '_findInfixAndEnclosingBrackets':False,
            '_findBackSlashPositions':False,
            '_updateInfixNearestBracketInfix':False,
            '__updateInfixNearestBracketInfix':False,#
            '_removeCaretThatIsNotExponent':False,
            '_findLeftOverPosition':False,
            '_contiguousLeftOvers':False,
            '_collateBackslashInfixLeftOversToContiguous':False,
            '_graftGrenzeRangesIntoContainmentTree':False,#
            '__addImplicitZero':False,
            '__addImplicitMultiply':False,
            '__intraGrenzeSubtreeUe':False,#
            '__interLevelSubtreeGrafting':False,
            '_reformatToAST':False,
            '_latexSpecialCases':False
        }
        def showError(): # TODO this call is very expensive..., maybe write everything to a log file?
            if self.verbose:
                for frame in inspect.stack():
                    methodName = frame.function
                    #try to get the first frame that is in methodVerbose:
                    show = self.methodVerbose.get(methodName)
                    if show is not None: # found methodName
                        return show # show is True/False (not None)
            return False
            # methodName = inspect.currentframe().f_back.f_code.co_name#f_back goes 1 frame up the call stack.
            # return self.verbose and methodName in self.methodVerbose and self.methodVerbose[methodName]
        self.showError = showError

        #########DEBUGGING TOOL FOR RESULT OF BUBBLE MERGE:

        def ppprint(cg, scgi):#Debugging tool TODO refactor
            m = {}
            for grange, dings in cg.items():
                sdings = []
                for ding in dings:
                    if ding['type'] == 'infix':
                        sdings.append((ding['name'], ding['position'], ding['position']+len(ding['name'])))
                    else:
                        sdings.append((ding['name'], ding['ganzStartPos'], ding['ganzEndPos']))
                m[grange] = sdings
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(m)
            n = []
            for grange, dings in scgi:
                sdings = []
                for ding in dings:
                    if ding['type'] == 'infix':
                        sdings.append((ding['name'], ding['position'], ding['position']+len(ding['name'])))
                    else:
                        sdings.append((ding['name'], ding['ganzStartPos'], ding['ganzEndPos']))
                n.append([grange, sdings])
            pp.pprint(n)

        self.ppprint = ppprint

        self.parallelise = parallelise
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
        self.equalPos = self._eqs.index('=') # will explode if no equals :)
        #maybe set all EVENT to false(clear()) before parsing, then
        #dump each "method" as processes into Pool
        #each method will have a .wait() for the oMethod/s, its waiting for
        #oMethod/s that complete will call set(), signalling method (waiting for oMethod) to start. :)

        if self.parallelise:
            self.event__findBackSlashPositions = mp.Event()
            self.event__findInfixAndEnclosingBrackets = mp.Event()
            self.event__updateInfixNearestBracketInfix = mp.Event()
            self.event__removeCaretThatIsNotExponent = mp.Event()
            self.event__findLeftOverPosition = mp.Event()
            self.event__contiguousLeftOvers = mp.Event()
            self.event__addImplicitZero = mp.Event()
            self.event__collateBackslashInfixLeftOversToContiguous = mp.Event()
            self.event__addImplicitMultipy = mp.Event()
            self.event__subTreeGraftingUntilTwoTrees = mp.Event()
            self.event__reformatToAST = mp.Event()



    def _findInfixAndEnclosingBrackets(self):
        #find all the positions of the infixes, and if there are round/square/curly brackets beside them...
        openBracketsLocation = dict(map(lambda openBracket: (openBracket, []), Latexparser.OPEN_BRACKETS))
        self.bracketStartToEndMap = {}
        self.matchingBracketsLocation = []
        self.infixList = []
        for idx, c in enumerate(self._eqs):
            if c in Latexparser.OPEN_BRACKETS:
                openBracketsLocation[c].append(idx) # this acts as a stack
            elif c in Latexparser.CLOSE_BRACKETS:
                o = Latexparser.close__open[c]
                matchingOpenBracketPos = openBracketsLocation[o].pop(len(openBracketsLocation[o])-1) # take out from the bottom like a stack
                self.matchingBracketsLocation.append({
                    'openBracketType':o, 
                    'closeBracketType':self.open__close[o], 
                    'openBracketPos':matchingOpenBracketPos, 
                    'closeBracketPos':idx
                })
                self.bracketStartToEndMap[matchingOpenBracketPos+len(o)] = idx # this is for _findBackSlashPositions, which takes argstartpos, statt bracketstartpos.
                # if self.showError():
                #     print('popped', matchingOpenBracketPos, 'remaining bracket:', openBracketsLocation[o])
            #Latexparser.PRIOIRITIZED_INFIX  has no =, which we should ignore for now
            elif c in Latexparser.PRIOIRITIZED_INFIX: # TODO what if infix is MULTI-CHARACTER? (then i am fucked, and also i need a sliding window, where the windowLen = max(map(lambda infixSym: len(infixSym), Latexparser.INFIX)))
                self.infixList.append({
                    'name':c,
                    'position':idx,
                    'startPos':idx,
                    'endPos':idx+len(c)
                })
        #check for error, if there are any left-over brackets in any of the stacks, then there is unbalanced brackets
        mismatchedOpenBrackets = []
        for openBracket, bracketPosStack in openBracketsLocation.items():
            if len(bracketPosStack) > 0:
                mismatchedOpenBrackets.append(openBracket)
        if len(mismatchedOpenBrackets) > 0:
            raise Exception(f'Mismatched brackets: {mismatchedOpenBrackets}')
        # import pdb;pdb.set_trace()
        if self.showError():
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(self.bracketStartToEndMap)
        if self.parallelise:
            self.event__findInfixAndEnclosingBrackets.set()


    def _findBackSlashPositions(self):
        """
        THE BACKSLASH FINDER! 
        _findInfixAndEnclosingBrackets wo tanomu

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
        6. the double-functioned variables of "Math mode accents" like: \\Acute{\\Acute{}}
        7. "Array environment, examples" (will be neccesary later for matrices... TODO)
        8. "Other Styles (math mode only)"
        9. "Font sizes"


        From the requirements, we ignore these:
        1. all the "Text Mode: Accents and Symbols" 
        """
        self.variablesPos = [] # name, startPos, endPos, | argument1, argument1StartPosition, argument1EndPosition, argumentBracketType
        self.functionPos = [] # functionName, startPos, endPos, _, ^, arguments, TODO rename to functionsPos
        self.noBraBackslashPos = [] # are variables, but no brackets
        self.backslashes = {} # for unparsing function

        #find \\functionName with regex (neater than character-by-character)
        for reMatch in findAllMatches('\\\\([a-zA-Z]+)', self._eqs): #capturing group omit the backslash
            positionTuple = reMatch.span()
            labelName = reMatch.groups()[0] # if use group, it comes with \\ at the front, not sure why
            if self.showError():
                print('labelName', labelName, '<<<<<<')
                print('positionTuple', positionTuple, '<<<<<')
            if labelName in Latexparser.VARIABLENAMESTAKEANARG: # it is actually a special kind of variable
                if self._eqs[positionTuple[1]] != '{':
                    raise Exception(f'after {labelName} should have {{')
                argument1StartPosition = positionTuple[1]+1 # because of the {
                closingCurlyBracketPos = self.bracketStartToEndMap[argument1StartPosition]#self._eqs.index('}', argument1StartPosition)
                argument1 = self._eqs[argument1StartPosition:closingCurlyBracketPos]
                argument1EndPosition = closingCurlyBracketPos
                self.variablesPos.append({
                    'name':labelName,
                    'startPos':positionTuple[0], # of the label, not the whole ding
                    'endPos':positionTuple[1], # of the label, not the whole ding
                    'argument1':argument1,
                    'argument1StartPosition':argument1StartPosition,
                    'argument1EndPosition':argument1EndPosition,
                    'argument1BracketType':'{',
                    'ganzStartPos':positionTuple[0],#startPos inclusive of argument
                    'ganzEndPos':max((argument1EndPosition if argument1EndPosition is not None else -1) + len('{'), positionTuple[1]),#endPos inclusive of argument
                    'type':'backslash_variable',
                    'child':{1:None},
                    'parent':None,
                    'position':positionTuple[0]
                })
                self.backslashes[labelName] = {
                    'argument1SubSuper':'',
                    'argument1OpenBracket':'{',
                    'argument1CloseBracket':'}',
                    'hasArgument1':True,
                    'argument2SubSuper':'',
                    'argument2OpenBracket':'',
                    'argument2CloseBracket':'',
                    'hasArgument2':False
                } # for unparsing function
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
                argument1SubSuperType = None # if argument1 was a superscript, argument1SubSuperType = ^, if argument1 was subscript, argument1SubSuperType = _
                argument1SubSuperPos = None # position of the argument1SubSuperPos
                argument2 = None
                argument2StartPosition = None
                argument2EndPosition = None
                argument2BracketType = None 
                argument2SubSuperType = None# if argument2 was a superscipt, argument2SubSuperType = ^, if argument2 was subscript, argument2SubSuperTyoe = _
                argument2SubSuperPos = None # position of the argument1SubSuperPos
                if labelName == 'sqrt':
                    if self._eqs[positionTuple[1]] == '[':# then we need to capture the rootpower as an argument
                        argument1StartPosition = positionTuple[1]+1 # +1 is for the '['
                        closingSquareBracketPos = self.bracketStartToEndMap[argument1StartPosition]#self._eqs.index(']', argument1StartPosition) # TODO i assume that there is not more [] between this and the other....
                        argument1 = self._eqs[argument1StartPosition:closingSquareBracketPos] # argument1 == rootpower
                        argument1EndPosition = closingSquareBracketPos
                        argument1BracketType = '['
                        nextPos = argument1EndPosition + 1 #because of the ]
                    else:
                        argument1StartPosition = positionTuple[1]#None
                        argument1 = 2 # default rootpower is square root
                        argument1EndPosition = positionTuple[1]#None
                        nextPos = positionTuple[1]
                    if self._eqs[nextPos] != '{': #TODO this is not true
                        raise Exception('Sqrt functions must be succeded by {')
                    argument2StartPosition = nextPos+1
                    closingRoundBracketPos = self.bracketStartToEndMap[argument2StartPosition]#self._eqs.index(')', argument2StartPosition)# TODO i assume that there is not more [] between this and the other....
                    argument2 = self._eqs[argument2StartPosition:closingRoundBracketPos] # argument2 == rootand
                    argument2EndPosition = closingRoundBracketPos
                    argument2BracketType = '{'
                elif labelName in Latexparser.TRIGOFUNCTION:
                    nextPos = positionTuple[1]# default if there is no ^
                    if self._eqs[positionTuple[1]] == '^': # then we need to capture the power as an argument
                        argument1SubSuperType = '^'
                        argument1SubSuperPos = positionTuple[1]
                        if self._eqs[positionTuple[1]+1] == '{': # we need to find the close curly and take everything in between as arg1
                            argument1StartPosition = positionTuple[1]+2
                            closingCurlyBracketPos = self.bracketStartToEndMap[argument1StartPosition]#self._eqs.index('}', argument1StartPosition) # TODO i assume that there is not more [] between this and the other....
                            argument1 = self._eqs[argument1StartPosition:closingCurlyBracketPos]# argument1 == power
                            argument1EndPosition = closingCurlyBracketPos
                            nextPos = argument1EndPosition + 1 # because of curly bracket }
                            argument1BracketType = '{'
                        else: # must be followed by a single character
                            argument1StartPosition = positionTuple[1]+1
                            argument1EndPosition = positionTuple[1]+2
                            argument1 = self._eqs[argument1StartPosition:argument1EndPosition]
                            nextPos = argument1EndPosition
                    else: # will lead to ugly AST, TODO need to simplify AST later to get rid of (^ sin 1)
                        argument1SubSuperType = None
                        argument1SubSuperPos = None
                        argument1StartPosition = -1
                        argument1EndPosition = -1
                        argument1 = "1"
                        argument1BracketType = None
                    #must be followed by round brackets.
                    if self.showError():
                        print(self._eqs[nextPos], 'TRIG succedor')
                    if self._eqs[nextPos] != '(':
                        raise Exception('Trignometric functions must be succeded by (')
                    argument2StartPosition = nextPos+1
                    closingRoundBracketPos = self.bracketStartToEndMap[argument2StartPosition]#self._eqs.index(')', argument2StartPosition)# TODO i assume that there is not more [] between this and the other....
                    argument2 = self._eqs[argument2StartPosition:closingRoundBracketPos] # argument2 == angle
                    argument2EndPosition = closingRoundBracketPos
                    argument2BracketType = '('
                    #########
                    # if self.showError():
                    #     print('Trigo function checking**************')
                    #     import pdb;pdb.set_trace()
                    #########
                elif labelName == 'ln':
                    argument1StartPosition = -1
                    argument1 = 'e' # defintion of natural log
                    argument1EndPosition = -1
                    if self._eqs[positionTuple[1]] != '(':
                        raise Exception('Natural Log must be succeded by (')
                    argument2StartPosition = positionTuple[1]+1
                    closingRoundBracketPos = self.bracketStartToEndMap[argument2StartPosition]#self._eqs.index(')', argument2StartPosition)# TODO i assume that there is not more [] between this and the other....
                    argument2 = self._eqs[argument2StartPosition:closingRoundBracketPos] # argument1 == logged
                    argument2EndPosition = closingRoundBracketPos
                    argument2BracketType = '('
                elif labelName == 'frac': # TODO here could be differentiation here...
                    # must have 2 curly brackets
                    if self._eqs[positionTuple[1]] != '{':
                        raise Exception('Frac must be succeded by {') # complain if cannot find first curly bracket
                    argument1StartPosition = positionTuple[1]+1
                    closingCurlyBracketPos = self.bracketStartToEndMap[argument1StartPosition]#self._eqs.index('}', argument1StartPosition)# TODO i assume that there is not more [] between this and the other....
                    argument1 = self._eqs[argument1StartPosition:closingCurlyBracketPos] # argument1 == numerator
                    argument1EndPosition = closingCurlyBracketPos
                    argument1BracketType = '{'
                    if self._eqs[argument1EndPosition+1] != '{':
                        raise Exception('Frac numerator must be succeded by {') # complain if cannot find second curly bracket
                    argument2StartPosition = argument1EndPosition+2 # because of {
                    closingCurlyBracketPos = self.bracketStartToEndMap[argument2StartPosition]#self._eqs.index('}', argument2StartPosition)# TODO i assume that there is not more [] between this and the other....
                    argument2 = self._eqs[argument2StartPosition:closingCurlyBracketPos] # argument2 == denominator
                    argument2EndPosition = closingCurlyBracketPos
                    argument2BracketType = '{'
                elif labelName == 'log':
                    #might not have {base} then we assume base=10
                    if self._eqs[positionTuple[1]] == '_': # user fixing the base of this log
                        argument1SubSuperType = '_'
                        argument1SubSuperPos = positionTuple[1]
                        if self._eqs[positionTuple[1]+1] == '{':
                            argument1StartPosition = positionTuple[1]+2
                            closingCurlyBracketPos = self.bracketStartToEndMap[argument1StartPosition]#self._eqs.index('}', argument1StartPosition)# TODO i assume that there is not more [] between this and the other....
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
                        argument1StartPosition = -1
                        argument1EndPosition = -1
                    if self.showError():
                        print(self._eqs[nextPos], '<<<<<nextPos')
                    if self._eqs[nextPos] != '(':
                        raise Exception('Log must be succeded by (')
                    argument2StartPosition = nextPos+1
                    closingRoundBracketPos = self.bracketStartToEndMap[argument2StartPosition]#self._eqs.index(')', argument2StartPosition)# TODO i assume that there is not more [] between this and the other....
                    argument2 = self._eqs[argument2StartPosition:closingRoundBracketPos] # argument2 == logant
                    argument2EndPosition = closingRoundBracketPos
                    argument2BracketType = '('
                else:
                    raise Exception(f'{labelName} is not implemented') # my fault.

                self.functionPos.append({
                    'name':labelName,
                    'startPos':positionTuple[0], # of the label not the whole ding
                    'endPos':positionTuple[1], # of the label not the whole ding
                    'position':positionTuple[0],
                    'argument1':argument1,
                    'argument1StartPosition':argument1StartPosition,
                    'argument1EndPosition':argument1EndPosition,
                    'argument1BracketType':argument1BracketType,
                    'argument1SubSuperType':argument1SubSuperType,
                    'argument1SubSuperPos':argument1SubSuperPos,
                    'argument2':argument2,
                    'argument2StartPosition':argument2StartPosition,
                    'argument2EndPosition':argument2EndPosition,
                    'argument2BracketType':argument2BracketType,
                    'argument2SubSuperType':argument2SubSuperType,
                    'argument2SubSuperPos':argument2SubSuperPos,
                    'ganzStartPos':positionTuple[0],
                    'ganzEndPos':max(
                        (argument1EndPosition if argument1EndPosition is not None else -1) + (len(argument1BracketType) if argument1BracketType is not None else 0), 
                        (argument2EndPosition if argument2EndPosition is not None else -1) + (len(argument2BracketType) if argument2BracketType is not None else 0),
                        positionTuple[1]
                    ),
                    'type':'backslash_function',
                    'child':{1:None, 2:None},
                    'parent':None
                })
                # import pdb;pdb.set_trace()
                self.backslashes[labelName] = {
                    'argument1SubSuper':argument1SubSuperType,
                    'argument1OpenBracket':argument1BracketType,
                    'argument1CloseBracket':self.open__close.get(argument1BracketType),
                    'hasArgument1': argument1EndPosition is not None,
                    'argument2SubSuper':argument2SubSuperType,
                    'argument2OpenBracket':argument2SubSuperType,
                    'argument2CloseBracket':self.open__close.get(argument2BracketType),
                    'hasArgument2': argument2BracketType is not None
                }#for unparsing function
            else: #has a backspace, but we have not targeted it... , we assume that its a zero-argument == variable...
                # put this seperate from self.variablesPos, 
                self.noBraBackslashPos.append({
                        'name':labelName,
                        'startPos':positionTuple[0], # of the label not the whole ding
                        'endPos':positionTuple[1], # of the label not the whole ding
                        'type':'variable', # same type as contiguous, davor, during AST building, we don't have to check for 2 ding
                        'parent':None,
                        'ganzStartPos':positionTuple[0],
                        'ganzEndPos':positionTuple[1]
                    })
                self.backslashes[labelName] = {
                    'argument1SubSuper':'',
                    'argument1OpenBracket':'',
                    'argument1CloseBracket':'',
                    'hasArgument1':False,
                    'argument2SubSuper':'',
                    'argument2OpenBracket':'',
                    'argument2CloseBracket':'',
                    'hasArgument2':False
                }#for unparsing function

        if self.showError():
            print('event__findBackSlashPositions IS RELEASED')
        if self.parallelise:
            self.event__findBackSlashPositions.set() # Trigger the event to notify the waiting process


    def __updateInfixNearestBracketInfix(self, tempInfixList0, tempInfixList1):
        ###########helpers
        #check if the bracket belongs to fBackslash/vBackslash
        def collideWithNonEnclosingBackslashBrackets(startBracketPos, endBracketPos):#, infixPosition):
            #TODO 
            """
            'z=\\sqrt(x^2+y^2)'
                     ^
                     This bracket is part of a backslashArg, so it was deliberately ignored...
                     So if it was an enclosing backslashArg, it should not be ignored... ?
            """
            if self.showError():
                print('collideWithNonEnclosingBackslashBrackets~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~', startBracketPos, endBracketPos)
            #######
            # print('collideWithNonEnclosingBackslashBrackets self.variablesPos: ', self.variablesPos)
            # import pdb;pdb.set_trace()
            #######
            for vInfoDict in self.variablesPos:
                """
                #has to be equals/ not contains/ because
                #\\frac{}{(x-3)^3}
                #        ^    ^
                #        1    2
                #so that 1 belongs to backslashargs
                #but 2 is enclosing
                #das ist fur unterscheide zweischen occupiedBracketPos(2) und interlevelSubTreeGrafting(1)
                #contains/ gives both (1) and (2) the same value.
                """
                if vInfoDict['argument1StartPosition'] is not None and (vInfoDict['argument1StartPosition'] - lenOrZero(vInfoDict['argument1BracketType'])) == startBracketPos:# and (vInfoDict['argument1StartPosition'] - lenOrZero(vInfoDict['argument1BracketType'])) <= startBracketPos and endBracketPos <= (vInfoDict['argument1EndPosition'] + lenOrZero(vInfoDict['argument1BracketType'])):
                # #check if arg1(vInfoDict) encloses infixPosition, if so ignore vInfoDict
                #     #######
                #     print("collideWithNonEnclosingBackslashBrackets vInfoDict['argument1StartPosition']: ", vInfoDict['argument1StartPosition'], " same bracket ? ", startBracketPos == vInfoDict['argument1StartPosition'] - lenOrZero(vInfoDict['argument1BracketType']))
                #     # import pdb;pdb.set_trace()
                #     #######
                #     #check
                #     if vInfoDict['argument1StartPosition'] <= infixPosition and infixPosition <= vInfoDict['argument1EndPosition']:
                #         ########
                #         print('ignoring seitdem, ', fInfoDict["argument1StartPosition"], ' <= ', infixPosition, ' <= ', fInfoDict['argument1EndPosition'])
                #         # import pdb;pdb.set_trace()
                #         ########
                #         continue
                    return True
            #######
            # print('collideWithNonEnclosingBackslashBrackets self.functionPos: ')
            # print(list(map(lambda f:(f['name'], f['startPos'], f['endPos']), self.functionPos)))
            # import pdb;pdb.set_trace()
            #######
            for fInfoDict in self.functionPos:
                ##########################
                # print("f1looking at: ", (fInfoDict['name'], fInfoDict['startPos'], fInfoDict['endPos']), "(arg1)'s ", fInfoDict['argument1StartPosition'] - lenOrZero(fInfoDict['argument1BracketType']), ' == ', startBracketPos)
                # import pdb;pdb.set_trace()
                ##########################
                if fInfoDict['argument1BracketType'] is not None and (fInfoDict['argument1StartPosition'] - lenOrZero(fInfoDict['argument1BracketType'])) == startBracketPos :# and (fInfoDict['argument1StartPosition'] - lenOrZero(fInfoDict['argument1BracketType'])) <= startBracketPos and endBracketPos <= (fInfoDict['argument1EndPosition'] + lenOrZero(fInfoDict['argument1BracketType'])):
                # #check if arg1(fInfoDict) encloses infixPosition, if so ignore fInfoDict
                #     ###########################
                #     print('startBracketPos : ', startBracketPos, ' collide with arg1 : ', (fInfoDict['name'], fInfoDict['startPos'], fInfoDict['endPos']))
                #     # import pdb;pdb.set_trace()
                #     ###########################
                #     if fInfoDict['argument1StartPosition'] <= infixPosition and infixPosition <= fInfoDict['argument1EndPosition']:
                #         ##########################
                #         print('ignoring seitdem, ', fInfoDict["argument1StartPosition"], ' <= ', infixPosition, ' <= ', fInfoDict['argument1EndPosition'])
                #         # import pdb;pdb.set_trace()
                #         ##########################
                #         continue
                    return True
                ##########################
                # print("f2looking at: ", (fInfoDict['name'], fInfoDict['startPos'], fInfoDict['endPos']), "(arg2)'s ", fInfoDict['argument2StartPosition'] - lenOrZero(fInfoDict['argument2BracketType']), ' == ', startBracketPos)
                # import pdb;pdb.set_trace()
                ##########################
                if fInfoDict['argument2BracketType'] is not None and (fInfoDict['argument2StartPosition'] - lenOrZero(fInfoDict['argument2BracketType'])) == startBracketPos:# and (fInfoDict['argument2StartPosition'] - lenOrZero(fInfoDict['argument2BracketType'])) <= startBracketPos and endBracketPos <= (fInfoDict['argument2EndPosition'] + lenOrZero(fInfoDict['argument2BracketType'])):
                # #check if arg2(fInfoDict) encloses infixPosition, if so ignore fInfoDict
                #     ###########################
                #     print('startBracketPos : ', startBracketPos, ' collide with arg2 : ', (fInfoDict['name'], fInfoDict['startPos'], fInfoDict['endPos']))
                #     # import pdb;pdb.set_trace()
                #     ###########################
                #     if fInfoDict['argument2StartPosition'] <= infixPosition and infixPosition <= fInfoDict['argument2EndPosition']:
                #         ############
                #         print('ignoring seitdem, ', fInfoDict["argument2StartPosition"], ' <= ', infixPosition, ' <= ', fInfoDict['argument2EndPosition'], 'infix in f_arg2')
                #         # import pdb;pdb.set_trace()
                #         ############
                #         continue
                    return True
            return False
        #are dic0 and dic1 on the same side?
        def sameSideAsInfoDictOfEqual(dic0, dic1):
            if dic0['position'] < self.equalPos:
                return dic1['position'] < self.equalPos
            else:
                return dic1['position'] > self.equalPos

        # self.tempInfixList = self.infixList # self.tempInfixList can be replaced with desired list
        # self.tempInfixList0 = self.infixList # self.tempInfixList0 can be replaced with desired list
        # self.tempInfixList1 = self.infixList # self.tempInfixList1 can be replaced with desired list
        # this allows this function to be re-used lorsque findFakeExponent, so for now it allows everything TODO override during find exponent
        def ali(a, b):
            return True
        self.allowedInfix = ali
        for infixInfoDict0 in tempInfixList0:
            ############
            if self.showError():
                print('infixBracMatch: ', (infixInfoDict0['name'], infixInfoDict0['startPos'], infixInfoDict0['endPos']), '^^^<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
            ############
            #ignore = and self
            # if infixInfoDict0['name'] == '=': # already ignored
            #     continue
            nearestLeftInfix = {'name':None, 'position':-1, 'startPos':-1, 'endPos':-1}
            nearestRightInfix = {'name':None, 'position':len(self._eqs), 'startPos':len(self._eqs), 'endPos':len(self._eqs)}
            #TODO binary search on self.infixList, why not build a datastructure here, so that is can be used later? (space for time)
            for infixInfoDict1 in tempInfixList1:
                #ignore if infixInfoDict1 === infixInfoDict0
                if infixInfoDict0['name'] == infixInfoDict1['name'] and infixInfoDict0['startPos'] == infixInfoDict1['startPos'] and infixInfoDict0['endPos'] == infixInfoDict1['endPos']:
                    continue
                if self.allowedInfix(infixInfoDict0, infixInfoDict1) and sameSideAsInfoDictOfEqual(infixInfoDict0, infixInfoDict1):
                    #left-side (of infixInfoDict0)
                    if infixInfoDict1['position'] < infixInfoDict0['position']:
                        #nearer than recorded?
                        if nearestLeftInfix['position'] < infixInfoDict1['position']: #recorded is further from infixInfoDict0
                            nearestLeftInfix = infixInfoDict1
                    else: # since we are on a line, (not left-side => right-side)
                        #nearer than recorded?
                        if nearestRightInfix['position'] > infixInfoDict0['position']: #recored is further from infixInfoDict0
                            nearestRightInfix = infixInfoDict1
            #find tightest bracket that directly left/right of infixInfoDict0
            isBackSlashBrackets = collideWithNonEnclosingBackslashBrackets(
                infixInfoDict0['ganzStartPos'], 
                infixInfoDict0['ganzEndPos']
            ) if 'ganzStartPos' in infixInfoDict0 else False # default assume not a backslashbracket
            tightLeftBracket = {
                'openBracketType':None, 
                'closeBracketType':None, 
                'openBracketPos':0 if infixInfoDict0['position'] < self.equalPos else self.equalPos + 1, #most narrow 
                'closeBracketPos':infixInfoDict0['position']-len(infixInfoDict0['name']),
                'belongToBackslash':isBackSlashBrackets
            }
            wideLeftBracket = {
                'openBracketType':None,
                'closeBracketType':None,
                'openBracketPos':infixInfoDict0['position']-len(infixInfoDict0['name']),
                'closeBracketPos':infixInfoDict0['position']-len(infixInfoDict0['name']),
                'belongToBackslash':isBackSlashBrackets
            }
            tightRightBracket = {
                'openBracketType':None, 
                'closeBracketType':None, 
                'openBracketPos':infixInfoDict0['position']+len(infixInfoDict0['name']), #most narrow
                'closeBracketPos':self.equalPos - 1 if infixInfoDict0['position'] < self.equalPos else len(self._eqs),
                'belongToBackslash':isBackSlashBrackets
            }
            wideRightBracket = {
                'openBracketType':None,
                'closeBracketType':None,
                'openBracketPos':infixInfoDict0['position']+len(infixInfoDict0['name']),
                'closeBracketPos':infixInfoDict0['position']+len(infixInfoDict0['name']),
                'belongToBackslash':isBackSlashBrackets
            }

            # defaultEnclosingOpenBracketPos = 0 if infixInfoDict0['position'] < self.equalPos else self.equalPos + 1 #infixInfoDict0['position']+len(infixInfoDict0['name'])
            tightLeftEnclosingBracket = {#also called openBracket
                'openBracketType':None,
                'openBracketPos':0 if infixInfoDict0['position'] < self.equalPos else self.equalPos + 1, # most narrow
                'belongToBackslash':isBackSlashBrackets
            }
            wideLeftEnclosingBracket = {
                'openBracketType':None,
                'openBracketPos':infixInfoDict0['position']+len(infixInfoDict0['name']),
                'belongToBackslash':isBackSlashBrackets
            }
            # defaultEnclosingCloseBracketPos = self.equalPos - 1 if infixInfoDict0['position'] < self.equalPos else len(self._eqs) #infixInfoDict0['position']-len(infixInfoDict0['name'])
            tightRightEnclosingBracket = {#also called closeBracket
                'closeBracketType':None,
                'closeBracketPos':self.equalPos - 1 if infixInfoDict0['position'] < self.equalPos else len(self._eqs), # most narrow
                'belongToBackslash':isBackSlashBrackets
            }
            wideRightEnclosingBracket = {
                'closeBracketType':None,
                'closeBracketPos':infixInfoDict0['position']-len(infixInfoDict0['name']),
                'belongToBackslash':isBackSlashBrackets
            }
            for bracketInfoDict in self.matchingBracketsLocation: 
                ###################START leftRight Brackets
                ######
                if self.showError():
                    print((infixInfoDict0['name'], infixInfoDict0['startPos'], infixInfoDict0['endPos']), 'brack:', (bracketInfoDict['openBracketPos'], bracketInfoDict['closeBracketPos']), ' checking for collision with backslash arguments')
                #TODO tag the brackets to backslashes
                isBackSlashBrackets = collideWithNonEnclosingBackslashBrackets(bracketInfoDict['openBracketPos'], bracketInfoDict['closeBracketPos'])

                #check if enclosing
                if bracketInfoDict['openBracketPos'] + len(bracketInfoDict['openBracketType']) <= infixInfoDict0['startPos'] and infixInfoDict0['endPos'] <= bracketInfoDict['closeBracketPos'] + len(bracketInfoDict['closeBracketType']):
                    ##########
                    if self.showError():
                        print('ENCLOSING~~, belongToBackslash: ', isBackSlashBrackets)
                        print('widestLeftOpen: ', wideLeftEnclosingBracket['openBracketPos'])
                        print('tightestLeftOpen: ', tightLeftEnclosingBracket['openBracketPos'])
                        print('newLeftOpen: ', bracketInfoDict['openBracketPos'])
                        print('widestRightOpen: ', wideRightEnclosingBracket['closeBracketPos'])
                        print('tightestRightClose: ', tightRightEnclosingBracket['closeBracketPos'])
                        print('newRightClose: ', bracketInfoDict['closeBracketPos'])
                    if tightLeftEnclosingBracket['openBracketPos'] <= bracketInfoDict['openBracketPos']: # bracketInfoDict is wider than recorded
                        tightLeftEnclosingBracket['openBracketPos'] = bracketInfoDict['openBracketPos']
                        tightLeftEnclosingBracket['openBracketType'] = bracketInfoDict['openBracketType']
                        tightLeftEnclosingBracket['belongToBackslash'] = isBackSlashBrackets
                        if self.showError():
                            print('updated tightLeftEnclosingBracket: ', tightLeftEnclosingBracket)
                    if bracketInfoDict['openBracketPos'] <= wideLeftEnclosingBracket['openBracketPos']:
                        wideLeftEnclosingBracket['openBracketPos'] = bracketInfoDict['openBracketPos']
                        wideLeftEnclosingBracket['openBracketType'] = bracketInfoDict['openBracketType']
                        wideLeftEnclosingBracket['belongToBackslash'] = isBackSlashBrackets
                        if self.showError():
                            print('updated wideLeftEnclosingBracket: ', wideLeftEnclosingBracket)
                    if bracketInfoDict['closeBracketPos'] <= tightRightEnclosingBracket['closeBracketPos']: # bracketInfoDict is wider than recorded
                        tightRightEnclosingBracket['closeBracketPos'] = bracketInfoDict['closeBracketPos']
                        tightRightEnclosingBracket['closeBracketType'] = bracketInfoDict['closeBracketType']
                        tightRightEnclosingBracket['belongToBackslash'] = isBackSlashBrackets
                        if self.showError():
                            print('updated tightRightEnclosingBracket: ', tightRightEnclosingBracket)
                    if wideRightEnclosingBracket['closeBracketPos'] <= bracketInfoDict['closeBracketPos']:
                        wideRightEnclosingBracket['closeBracketPos'] = bracketInfoDict['closeBracketPos']
                        wideRightEnclosingBracket['closeBracketType'] = bracketInfoDict['closeBracketType']
                        wideRightEnclosingBracket['belongToBackslash'] = isBackSlashBrackets
                        if self.showError():
                            print('updated wideRightEnclosingBracket: ', wideRightEnclosingBracket)

                #direct left-side (of infixInfoDict0)
                if bracketInfoDict['closeBracketPos'] + len(bracketInfoDict['closeBracketType']) == infixInfoDict0['startPos']:
                    ############
                    if self.showError():
                        print('LEFTBRACK~~~~, belongToBackslash: ', isBackSlashBrackets)
                    ############
                    #engste als recorded?
                    if tightLeftBracket['openBracketPos'] <= bracketInfoDict['openBracketPos'] and bracketInfoDict['closeBracketPos'] <= tightLeftBracket['closeBracketPos']:
                        tightLeftBracket = bracketInfoDict
                        tightLeftBracket['belongToBackslash'] = isBackSlashBrackets
                        if self.showError():
                            print('updated tightLeftBracket: ', tightLeftBracket)
                    #breiter als recorded?
                    if bracketInfoDict['openBracketPos'] <= wideLeftBracket['openBracketPos'] and wideLeftBracket['closeBracketPos'] <= bracketInfoDict['closeBracketPos']:
                        wideLeftBracket = bracketInfoDict
                        wideLeftBracket['belongToBackslash'] = isBackSlashBrackets
                        if self.showError():
                            print('updated wideLeftBracket: ', wideLeftBracket)
                elif infixInfoDict0['endPos'] == bracketInfoDict['openBracketPos'] - len(bracketInfoDict['openBracketType']):
                    ############
                    if self.showError():
                        print('RIGHTBRACK~~~~, belongToBackslash: ', isBackSlashBrackets)
                    ############
                    #wider than recorded?
                    if tightRightBracket['openBracketPos'] <= bracketInfoDict['openBracketPos'] and bracketInfoDict['closeBracketPos'] <= tightRightBracket['closeBracketPos']:
                        tightRightBracket = bracketInfoDict
                        tightRightBracket['belongToBackslash'] = isBackSlashBrackets
                        if self.showError():
                            print('updated tightRightBracket: ', tightRightBracket)
                    #breiter als recorded?
                    if bracketInfoDict['openBracketPos'] <= wideRightBracket['openBracketPos'] and wideRightBracket['closeBracketPos'] <= bracketInfoDict['closeBracketPos']:
                        wideRightBracket = bracketInfoDict
                        wideRightBracket['belongToBackslash'] = isBackSlashBrackets
                        if self.showError():
                            print('updated wideLeftBracket: ', wideRightBracket)

                ############
                if self.showError():
                    print('nearestLeftInfix:')
                    print(nearestLeftInfix)
                    print('nearestRightInfix:')
                    print(nearestRightInfix)
                    print('tightLeftBracket:')
                    print(tightLeftBracket)
                    print('tightRightBracket:')
                    print(tightRightBracket)
                    print('tightLeftEnclosingBracket:')
                    print(tightLeftEnclosingBracket)
                    print('tightRightEnclosingBracket')
                    print(tightRightEnclosingBracket)
                    print('wideLeftBracket:')
                    print(wideLeftBracket)
                    print('wideRightBracket:')
                    print(wideRightBracket)
                    print('wideLeftEnclosingBracket:')
                    print(wideLeftEnclosingBracket)
                    print('wideRightEnclosingBracket')
                    print(wideRightEnclosingBracket)
                    print('infixBracMatch: ', (infixInfoDict0['name'], infixInfoDict0['startPos'], infixInfoDict0['endPos']), '^^^<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                ############

            #choose (or store everything TODO for now, we assume that people don't write equations like: "((a+b)-(c+d))", instead, they write it like this: "(a+b)-(c+d)" ) between
            #1. enclosing
            #2. one-sided bracket (leftRight)
            #3. nearest-infix (infix)

            #but, first, update common information, needed later but too early to add, at discovery.... is this better though?
            infixInfoDict0.update({
                'type':'infix',
                'child':{1:None, 2:None},
                'parent':None,
                #fill up with None
                'ganzStartPos':None, # infix with args and brackets
                'ganzEndPos':None, # infix with args and brackets

                #for finding occupied brackets in _findLeftOverPosition ===========TODO, tight is for finding occupied brackets, wide is for others..... RENAMEPLEASE
                'tight__leftStartType':None,
                'tight__leftStartPos':None,
                'tight__leftEndType':None,
                'tight__leftEndPos':None,
                'tight__leftType':None,

                'tight__rightStartType':None,
                'tight__rightStartPos':None,
                'tight__rightEndType':None,
                'tight__rightEndPos':None,
                'tight__rightType':None,


                'left__startBracketPos':None,
                'left__startBracketType':None,
                'left__endBracketPos':None,
                'left__endBracketType':None,
                'left__argStart':None,
                'left__argEnd':None,#everything before infixInfoDict0
                'left__type':None,

                'right__startBracketPos':None,
                'right__startBracketType':None,
                'right__endBracketPos':None,
                'right__endBracketType':None,
                'right__argStart':None,#everything after infixInfoDict0
                'right__argEnd':None,
                'right__type':None

            })

            ############
            if self.showError():
                print('bracket FOUND STATS:')
                print("left will take enclosing", tightLeftEnclosingBracket['openBracketType'] is not None)
                print("left will take leftRight", tightLeftBracket['openBracketType'] is not None)
                print("left will take infix", nearestLeftInfix['name'] is not None)
                print("right will take enclosing", tightRightEnclosingBracket['closeBracketType'] is not None)
                print("right will take leftRight", tightRightBracket['closeBracketType'] is not None)
                print("right will take infix", nearestRightInfix['name'] is not None)
            ############

            #TIGHT-THINGS: for finding occupied brackets in _findLeftOverPosition
            if tightLeftEnclosingBracket['openBracketType'] is not None:
                infixInfoDict0.update({
                    'tight__leftStartType':tightLeftEnclosingBracket['openBracketType'],
                    'tight__leftStartPos':tightLeftEnclosingBracket['openBracketPos'],
                    'tight__leftType':'backslashArg' if tightLeftEnclosingBracket['belongToBackslash'] else 'enclosing',
                })
            elif tightLeftBracket['openBracketType'] is not None:
                infixInfoDict0.update({
                    'tight__leftStartType':tightLeftBracket['openBracketType'],
                    'tight__leftStartPos':tightLeftBracket['openBracketPos'],
                    'tight__leftType':'backslashArg' if tightLeftBracket['belongToBackslash'] else 'leftRight',
                    'tight__leftEndType':tightLeftBracket['closeBracketType'],
                    'tight__leftEndPos':tightLeftBracket['closeBracketPos'],
                })

            if tightRightEnclosingBracket['closeBracketType'] is not None:
                infixInfoDict0.update({
                    'tight__rightEndType':tightRightEnclosingBracket['closeBracketType'],
                    'tight__rightEndPos':tightRightEnclosingBracket['closeBracketPos'],
                    'tight__rightType':'backslashArg' if tightRightEnclosingBracket['belongToBackslash'] else 'enclosing',
                })
            elif tightRightBracket['closeBracketType'] is not None:
                infixInfoDict0.update({
                    'tight__leftStartType':tightRightBracket['openBracketType'],
                    'tight__leftStartPos':tightRightBracket['openBracketPos'],
                    'tight__leftType':'backslashArg' if tightRightBracket['belongToBackslash'] else 'leftRight',
                    'tight__leftEndType':tightRightBracket['closeBracketType'],
                    'tight__leftEndPos':tightRightBracket['closeBracketPos'],
                })

            #check left
            if wideLeftEnclosingBracket['openBracketType'] is not None:# or wideLeftEnclosingBracket['openBracketPos'] != defaultEnclosingOpenBracketPos: # it is possible, to have openBracketType=None but openBracketPos!=None, like a implicit-multiply between 2 non-infix dings
             # has left brackets
                infixInfoDict0.update({
                    'startPos':infixInfoDict0['startPos'], # only the infix character/s
                    # 'endPos':infixInfoDict0['endPos'], # only the infix character/s
                    'ganzStartPos':wideLeftEnclosingBracket['openBracketPos'], # infix with args and brackets
                    # 'ganzEndPos':, # infix with args and brackets, only checking left, cannot get the rightEnding

                    'left__startBracketPos':wideLeftEnclosingBracket['openBracketPos'],
                    'left__startBracketType':wideLeftEnclosingBracket['openBracketType'],
                    # 'left__endBracketPos':wideLeftBracket['closeBracketPos'],
                    # 'left__endBracketType':wideLeftBracket['closeBracketType'],
                    'left__argStart':wideLeftEnclosingBracket['openBracketPos']+lenOrZero(wideLeftEnclosingBracket['openBracketType']),
                    # 'left__argEnd':wideLeftBracket['closeBracketPos']+len(wideLeftBracket['closeBracketType']),
                    #if halfEnclosing, we should not try to add implicit-multiply, only when enclosing, then we try to add implicit-multiply
                    'left__type':'backslashArg' if wideLeftEnclosingBracket['belongToBackslash'] else 'enclosing'
                    #'left__type':'enclosing' if wideRightEnclosingBracket['closeBracketType'] is not None else 'halfEnclosing'
                })

            elif wideLeftBracket['openBracketType'] is not None:# or wideLeftBracket['openBracketPos'] != defaultLeftBracketOpenBracketPos:
             # has left brackets
                infixInfoDict0.update({
                    'startPos':infixInfoDict0['startPos'], # only the infix character/s
                    'endPos':infixInfoDict0['endPos'], # only the infix character/s
                    'ganzStartPos':wideLeftBracket['openBracketPos'], # infix with args and brackets
                    # 'ganzEndPos':, # infix with args and brackets, only checking left, cannot get the rightEnding

                    'left__startBracketPos':wideLeftBracket['openBracketPos'],
                    'left__startBracketType':wideLeftBracket['openBracketType'],
                    'left__endBracketPos':wideLeftBracket['closeBracketPos'],
                    'left__endBracketType':wideLeftBracket['closeBracketType'],
                    'left__argStart':wideLeftBracket['openBracketPos']+lenOrZero(wideLeftBracket['openBracketType']),
                    'left__argEnd':wideLeftBracket['closeBracketPos']+lenOrZero(wideLeftBracket['closeBracketType']),
                    'left__type':'backslashArg' if wideLeftBracket['belongToBackslash'] else 'leftRight'
                    # 'left__type':'leftRight' if wideRightBracket['closeBracketType'] is not None else 'halfLeftRight'
                })
            elif nearestLeftInfix['name'] is not None: # has left infix
                infixInfoDict0.update({
                    'startPos':infixInfoDict0['startPos'], # only the infix character/s
                    'endPos':infixInfoDict0['endPos'], # only the infix character/s
                    'ganzStartPos':nearestLeftInfix['startPos'], # infix with args and brackets
                    # 'ganzEndPos':, # infix with args and brackets, only checking left, cannot get the rightEnding

                    'left__startBracketPos':nearestLeftInfix['startPos'],
                    'left__startBracketType':nearestLeftInfix['name'],
                    'left__endBracketPos':nearestLeftInfix['endPos'],
                    'left__endBracketType':nearestLeftInfix['name'],
                    'left__argStart':nearestLeftInfix['startPos'] + len(nearestLeftInfix['name']),
                    'left__argEnd':nearestLeftInfix['endPos'] - len(nearestLeftInfix['name']),
                    'left__type':'infix'
                })
            else: # no, enclosing, leftbrackets nor left infix, WE STILL NEED TO SET left__argStart & left__argEnd
                infixInfoDict0.update({
                    'startPos':infixInfoDict0['startPos'], # only the infix character/s
                    'endPos':infixInfoDict0['endPos'], # only the infix character/s
                    'ganzStartPos':0 if infixInfoDict0['position'] < self.equalPos else self.equalPos + 1, # infix with args and brackets, # + 1 because len(self.equalPos) = 1
                    # 'ganzEndPos':, # infix with args and brackets, only checking left, cannot get the rightEnding

                    'left__startBracketPos':None,
                    'left__startBracketType':None,
                    'left__endBracketPos':None,
                    'left__endBracketType':None,
                    #if infix0 before =, [ (...)+...=.... ]
                    #leftargStart at 0 [we already checked there are no infix left of infix0]
                    #else [ ....=(...)+... ]
                    #leftargStart after equal
                    'left__argStart':0 if infixInfoDict0['position'] < self.equalPos else self.equalPos + 1, # + 1 because len(self.equalPos) = 1
                    #if infix0 before =, [ (...)+...=.... ]
                    #leftargEnd before infix0
                    #else [ ....=(...)+... ]
                    #leftargEnd at infix0
                    'left__argEnd':infixInfoDict0['position'] - len(infixInfoDict0['name']),
                    'left__type':'arg'
                })


            # import pdb;pdb.set_trace()
            #check right
            if wideRightEnclosingBracket['closeBracketType'] is not None:# or wideRightEnclosingBracket['closeBracketType'] != defaultEnclosingCloseBracketPos:
                infixInfoDict0.update({
                    # 'startPos':infixInfoDict0['startPos'], # only the infix character/s
                    'endPos':infixInfoDict0['endPos'], # only the infix character/s
                    # 'ganzStartPos':, # infix with args and brackets, only checking right, cannot get the leftEnding
                    'ganzEndPos':wideRightEnclosingBracket['closeBracketPos'], # infix with args and brackets

                    # 'right__startBracketPos':wideRightBracket['openBracketPos'],
                    # 'right__startBracketType':wideRightBracket['openBracketType'],
                    'right__endBracketPos':wideRightEnclosingBracket['closeBracketPos'],
                    'right__endBracketType':wideRightEnclosingBracket['closeBracketType'],
                    # 'right__argStart':wideRightBracket['openBracketPos']+len(wideRightBracket['openBracketType']),
                    'right__argEnd':wideRightEnclosingBracket['closeBracketPos']+lenOrZero(wideRightEnclosingBracket['closeBracketType']),
                    #if halfEnclosing, we should not try to add implicit-multiply, only when enclosing, then we try to add implicit-multiply
                    'right__type':'backslashArg' if wideRightEnclosingBracket['belongToBackslash'] else 'enclosing'
                    # 'right__type':'enclosing' if wideLeftEnclosingBracket['openBracketType'] is not None else 'halfEnclosing'
                })
            elif wideRightBracket['closeBracketType'] is not None:# or wideRightBracket['closeBracketType'] != defaultRightBracketCloseBracketPos: # has right brackets
                # import pdb;pdb.set_trace()
                infixInfoDict0.update({
                    'startPos':infixInfoDict0['startPos'], # only the infix character/s
                    'endPos':infixInfoDict0['endPos'], # only the infix character/s
                    # 'ganzStartPos':, # infix with args and brackets, only checking right, cannot get the leftEnding
                    'ganzEndPos':wideRightBracket['closeBracketPos'], # infix with args and brackets

                    'right__startBracketPos':wideRightBracket['openBracketPos'],
                    'right__startBracketType':wideRightBracket['openBracketType'],
                    'right__endBracketPos':wideRightBracket['closeBracketPos'],
                    'right__endBracketType':wideRightBracket['closeBracketType'],
                    'right__argStart':wideRightBracket['openBracketPos']+lenOrZero(wideRightBracket['openBracketType']),
                    'right__argEnd':wideRightBracket['closeBracketPos']+lenOrZero(wideRightBracket['closeBracketType']),
                    'right__type':'backslashArg' if wideRightBracket['belongToBackslash'] else 'leftRight'
                    # 'right__type':'leftRight' if wideLeftBracket['openBracketType'] is not None else 'halfLeftRight'
                })
            elif nearestRightInfix['name'] is not None: # has right infix
                infixInfoDict0.update({
                    'startPos':infixInfoDict0['startPos'], # only the infix character/s
                    'endPos':infixInfoDict0['endPos'], # only the infix character/s
                    # 'ganzStartPos':, # infix with args and brackets, only checking right, cannot get the leftEnding
                    'ganzEndPos':nearestRightInfix['endPos'], # infix with args and brackets

                    'right__startBracketPos':nearestRightInfix['startPos'],
                    'right__startBracketType':nearestRightInfix['name'],
                    'right__endBracketPos':nearestRightInfix['endPos'],
                    'right__endBracketType':nearestRightInfix['name'],
                    'right__argStart':nearestRightInfix['startPos'] + len(nearestRightInfix['name']),
                    'right__argEnd':nearestRightInfix['endPos'] - len(nearestRightInfix['name']),
                    'right__type':'infix'
                })
            else: # no, enclosing, rightbrackets nor right infix, WE STILL NEED TO SET right__argStart & right__argEnd
                infixInfoDict0.update({
                    'startPos':infixInfoDict0['startPos'], # only the infix character/s
                    'endPos':infixInfoDict0['endPos'], # only the infix character/s
                    # 'ganzStartPos':, # infix with args and brackets, only checking right, cannot get the leftEnding
                    'ganzEndPos':self.equalPos - 1 if infixInfoDict0['position'] < self.equalPos else len(self._eqs), # infix with args and brackets

                    'right__startBracketPos':None,
                    'right__startBracketType':None,
                    'right__endBracketPos':None,
                    'right__endBracketType':None,
                    #if infix0 before =, [ ....+(...)=.... ]
                    #rightargStart after infix0
                    #else [ ....=....+(...) ]
                    #rightargStart after infix0
                    'right__argStart':infixInfoDict0['position'],
                    #if infix0 before =, [ ....+(...)=.... ]
                    #rightargEnd before =
                    #else [ ....=....+(...) ]
                    #rightargEnd at self._eqs
                    'right__argEnd':self.equalPos - 1 if infixInfoDict0['position'] < self.equalPos else len(self._eqs),
                    'right__type':'arg'
                })

            if self.showError():
                print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
                print('infixBracket: ', (infixInfoDict0['name'], infixInfoDict0['startPos'], infixInfoDict0['endPos']))
                print('ganzStartPos: ', infixInfoDict0['ganzStartPos'], ' ganzEndPos: ', infixInfoDict0['ganzEndPos'])
                print('left__type: ', infixInfoDict0['left__type'], ' right__type: ', infixInfoDict0['right__type'])
                print('tight__leftType: ', infixInfoDict0['tight__leftType'], ' tight__rightType', infixInfoDict0['tight__rightType'])
                print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')


    def _updateInfixNearestBracketInfix(self):

        if self.parallelise:
            self.event__findBackSlashPositions.wait()
            self.event__findInfixAndEnclosingBrackets.wait()
        self.__updateInfixNearestBracketInfix(self.infixList, self.infixList)
        # import pdb;pdb.set_trace()
        if self.parallelise:
            self.event__updateInfixNearestBracketInfix.set() ##########~~~


    def _removeCaretThatIsNotExponent(self):
        """
        """
        if self.parallelise:
            self.event__findBackSlashPositions.wait() #~~~~
            self.event__findInfixAndEnclosingBrackets.wait()
        #^ would have been picked up by "findInfixAndEnclosingBrackets" as infix
        fakeExponents = []
        fakeExponentsQuickCheck = set()
        newListOfInfixInfoDict = []
        #######TODO refactor using   event__updateInfixNearestBracketInfix
        for infixInfoDict in self.infixList:
            if infixInfoDict['name'] == '^':
                notExponent = False
                for backslashFunction in self.functionPos:
                    if (infixInfoDict['position'] == backslashFunction['argument1SubSuperPos'] and backslashFunction['argument1SubSuperType'] == '^') or \
                    (infixInfoDict['position'] == backslashFunction['argument2SubSuperPos'] and backslashFunction['argument2SubSuperType'] == '^'):
                        #this is not a exponent, sondern a superscript of backslashFunction, should not be left in the infixOperatorPositions
                        notExponent = True
                        fakeExponents.append(infixInfoDict) # actually we don't need to keep the whole infixInfoDict, just a few information
                        #elem(fakeExponentsQuickCheck) = (startBracketPos, endBracketPos)
                        fakeExponentsQuickCheck.add((infixInfoDict['position'], infixInfoDict['position']+len(infixInfoDict['name']))) # allows syntacal sugar when looking for the next infix, that is not a fakeExponent
                        break
                if not notExponent: # it is a exponent, put it back, else discard
                    newListOfInfixInfoDict.append(infixInfoDict)
            else: # jede andere infix sollt diese Problem haben nicht
                newListOfInfixInfoDict.append(infixInfoDict)
        #clear the infixInfoDict left__arg and right__arg if they are fakeExponent
        ###############
        if self.showError():
            print('original newListOfInfixInfoDict<<<<<<<<<<<<<<<<<<<<<<<<<<')
            print(newListOfInfixInfoDict)
            print('<<<<<<<<<<<<<ORIGINAL newListOfInfixInfoDict<<<<<<<<<<<<<')
        ###############
        #here we want to update the left/Right 'bracket/infix' of each infix, 
        for infixInfoDict in newListOfInfixInfoDict:
            #match left args of infixInfoDict with fakeExponents
            #match right args of infixInfoDict with fakeExponents
            for fakeExponent in fakeExponents:
                if infixInfoDict['left__startBracketType'] == '^' and infixInfoDict['left__startBracketPos'] == fakeExponent['position']:
                    # infixInfoDict leftArg look for further infix (we already search for enclosing/leftRight brackets before infix, if we landed with infix, this means that we do not have enclosing/leftRight brackets...)
                    nextInfix = {
                        'left__startBracketPos':-1, 
                        'left__startBracketType':None,
                        'left__endBracketPos':-1,
                        'left__endBracketType':None,
                        'left__argStart':None,
                        'left__argEnd':None,
                        'left__type':None, # enclosing
                        'ganzStartPos':None
                    }
                    #there is duplicated code from _findInfixAndEnclosingBrackets, TODO refactor
                    for infixInfoDict0 in newListOfInfixInfoDict:
                        infixOp0 = infixInfoDict0['name']
                        if infixInfoDict0['position'] < infixInfoDict['position'] and (infixInfoDict0['position'], infixInfoDict0['position']+len(infixInfoDict0['name'])) not in fakeExponentsQuickCheck:
                            if nextInfix['left__startBracketPos'] < infixInfoDict0['position']:
                                nextInfix['left__startBracketPos'] = infixInfoDict0['position']
                                nextInfix['left__startBracketType'] = infixOp0#infoDict0['name']
                                nextInfix['left__endBracketPos'] = infixInfoDict0['position'] + len(infixOp0)
                                nextInfix['left__endBracketType'] = infixOp0#infoDict0['name']
                                nextInfix['left__argStart'] = infixInfoDict0['position'] + len(infixOp0)
                                nextInfix['left__argEnd'] = infoDict['position'] - len(infixOp)
                                nextInfix['left__type'] = 'infix'
                                nextInfix['ganzStartPos'] = infixInfoDict0['position'] + len(infixOp0)

                    if nextInfix['left__startBracketType'] is None:#no left neighbouring infix
                        #still must have left__argStart and left__argEnd, note that '-' has a special case, wie "-ab=-ba", where the len(leftArg) = 0 and leftArg=0...TODO
                        #...+...=  (position < equalPos)
                        #=...+...  (position > equalPos)
                        
                        if self.showError():
                            print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<no left neighbouring infix')
                        nextInfix['left__argStart'] = 0 if infixInfoDict['position'] < self.equalPos else self.equalPos + 1 # everything to the left of infoDict
                        nextInfix['left__argEnd'] = infixInfoDict['position'] - 1 if infixInfoDict['position'] < self.equalPos else self.equalPos
                        nextInfix['ganzStartPos'] = nextInfix['left__argStart']
                        nextInfix['left__type'] = 'arg'
                    infixInfoDict.update(nextInfix)
                if infixInfoDict['right__startBracketType'] == '^' and infixInfoDict['right__startBracketPos'] == fakeExponent['position']:
                    #scrub infixInfoDict rightArg clean
                    nextInfix = {
                        'right__startBracketPos':-1,
                        'right__startBracketType':None,
                        'right__endBracketPos':-1,
                        'right__endBracketType':None,
                        'right__argStart':None,
                        'right__argEnd':None,
                        'right__type':None, #enclosing
                        'ganzEndPos':None
                    }
                    #there is duplicated code from _findInfixAndEnclosingBrackets, TODO refactor
                    for infixInfoDict0 in newListOfInfixInfoDict:
                        infixOp0 = infixInfoDict0['name']
                        if infixInfoDict0['position'] > infixInfoDict['position'] and (infixInfoDict0['position'], infixInfoDict0['position']+len(infixInfoDict0['name'])) not in fakeExponentsQuickCheck:
                            if infixInfoDict0['position'] < nextInfix['right__startBracketPos']:
                                nextInfix['right__startBracketPos'] = infixInfoDict0['position']
                                nextInfix['right__startBracketType'] = infixOp0
                                nextInfix['right__endBracketPos'] = infixInfoDict0['position'] + len(infixOp0)
                                nextInfix['right__endBracketType'] = infixOp0
                                nextInfix['right__argStart'] = infoDict['position'] + len(infixOp)
                                nextInfix['right__argEnd'] = infixInfoDict0['position'] - len(infixOp0)
                                nextInfix['right__type'] = 'infix'
                                nextInfix['ganzEndPos'] = infixInfoDict0['position'] - len(infixOp0)
                    if nextInfix['right__startBracketType'] is None:#no right neighbouring infix
                        #still must have right__argStart and right__argEnd, note that '-' has a special case, wie "-ab=-ba", where the len(leftArg) = 0 and leftArg=0...TODO
                        #...+...=  (position < equalPos)
                        #=...+...  (position > equalPos)
                        
                        if self.showError():
                            print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<no right neighbouring infix')
                        nextInfix['right__argStart'] = infixInfoDict['position'] + 1 
                        nextInfix['right__argEnd'] = self.equalPos if infixInfoDict['position'] < self.equalPos else len(self._eqs)
                        nextInfix['ganzEndPos'] = nextInfix['right__argStart']
                        nextInfix['right__type'] = 'arg'
                    infixInfoDict.update(nextInfix)
            # import pdb;pdb.set_trace()
        self.infixList = newListOfInfixInfoDict
        if self.showError():
            print('<<<<<<<<<<<<<<<<<<<REMOVED ALL ^ pretending to be exponent?')
            print(self.infixList)
            print('<<<<<<<<<<<<<<<<<<<')
        ###what about infixes, whose left and right are pretending to be exponents? TODO
        if self.parallelise:
            self.event__removeCaretThatIsNotExponent.set()


    def _findLeftOverPosition(self):
        if self.parallelise:
            self.event__removeCaretThatIsNotExponent.wait()
        listOfOccupiedRanges = set() # note that ranges should not overlapp
        # import pdb;pdb.set_trace()

        for vInfoDict in self.noBraBackslashPos:
            listOfOccupiedRanges.add((vInfoDict['startPos'], vInfoDict['endPos']))

        for variableInfoDict in self.variablesPos:
            listOfOccupiedRanges.add((variableInfoDict['startPos'], variableInfoDict['endPos']))
            if variableInfoDict['argument1StartPosition'] is not None: # just take the bracket start and end Pos
                listOfOccupiedRanges.add((variableInfoDict['argument1StartPosition']-len(variableInfoDict['argument1BracketType']), variableInfoDict['argument1StartPosition']))
            if variableInfoDict['argument1EndPosition'] is not None: # just take the bracket start and end Pos
                listOfOccupiedRanges.add((variableInfoDict['argument1EndPosition'], variableInfoDict['argument1EndPosition']+len(variableInfoDict['argument1BracketType'])))
        for functionInfoDict in self.functionPos:
            listOfOccupiedRanges.add((functionInfoDict['startPos'], functionInfoDict['endPos']))
            if functionInfoDict['argument1BracketType'] is not None: # there is opening and closing brackets for argument1
                listOfOccupiedRanges.add((functionInfoDict['argument1StartPosition']-len(functionInfoDict['argument1BracketType']), functionInfoDict['argument1StartPosition']))
                listOfOccupiedRanges.add((functionInfoDict['argument1EndPosition'], functionInfoDict['argument1EndPosition']+len(functionInfoDict['argument1BracketType'])))
            if functionInfoDict['argument2BracketType'] is not None: # there is opening and closing brackets for argument2
                listOfOccupiedRanges.add((functionInfoDict['argument2StartPosition']-len(functionInfoDict['argument2BracketType']), functionInfoDict['argument2StartPosition']))
                listOfOccupiedRanges.add((functionInfoDict['argument2EndPosition'], functionInfoDict['argument2EndPosition']+len(functionInfoDict['argument2BracketType'])))
            if functionInfoDict['argument1SubSuperPos'] is not None: # there is a ^ or _ on argument1
                listOfOccupiedRanges.add((functionInfoDict['argument1SubSuperPos'], functionInfoDict['argument1SubSuperPos']+len(functionInfoDict['argument1SubSuperType'])))
            if functionInfoDict['argument2SubSuperPos'] is not None: # there is a ^ or _ on argument2
                listOfOccupiedRanges.add((functionInfoDict['argument2SubSuperPos'], functionInfoDict['argument2SubSuperPos']+len(functionInfoDict['argument2SubSuperType'])))
        # sortedListOfOccupiedRanges = sorted(listOfOccupiedRanges, key=lambda tup: tup[0]) # TODO sort for binary search

        self.occupiedBrackets = []# for bubble merge later, these entreSpaces are connected
        #self.infixOperatorPositions
        for infixInfoDict in self.infixList:
            ##############
            if self.showError():
                print('recording occupied positions for ')
                print((infixInfoDict['name'], infixInfoDict['startPos'], infixInfoDict['endPos'], infixInfoDict['tight__leftType'], infixInfoDict['tight__rightType']))
                # import pdb;pdb.set_trace()
            ##############
            listOfOccupiedRanges.add((infixInfoDict['position'], infixInfoDict['position']+len(infixInfoDict['name']))) # might have repeats since some 'brackets' are infixes
            # import pdb;pdb.set_trace()
            if infixInfoDict['left__type'] != 'infix' and infixInfoDict['left__startBracketType'] is not None:
                listOfOccupiedRanges.add((infixInfoDict['left__startBracketPos'], infixInfoDict['left__startBracketPos']+len(infixInfoDict['left__startBracketType'])))
                #backslashargs not occupiedBrackets, partialFrac test case
                if infixInfoDict['tight__leftType'] in ['enclosing', 'leftRight']:#if infixInfoDict['left__type'] in ['enclosing', 'leftRight']:##############TODO does it work for other polynomial like things?
                    for pos in range(infixInfoDict['left__startBracketPos'], infixInfoDict['left__startBracketPos']+len(infixInfoDict['left__startBracketType'])):
                        self.occupiedBrackets.append(pos)
                        if self.showError():
                            print('>>>>adding :', self._eqs[pos], ' >>>> to self.occupiedBrackets')
            if infixInfoDict['left__type'] != 'infix' and infixInfoDict['left__endBracketType'] is not None: # left__startBracketType is not None =/=> left__endBracketType is not None, since we may have enclosing brackets
                listOfOccupiedRanges.add((infixInfoDict['left__endBracketPos'], infixInfoDict['left__endBracketPos']+len(infixInfoDict['left__endBracketType'])))
                #backslashargs not occupiedBrackets, partialFrac test case
                if infixInfoDict['tight__leftType'] in ['enclosing', 'leftRight']:#if infixInfoDict['left__type'] in ['enclosing', 'leftRight']:##############TODO does it work for other polynomial like things?
                    for pos in range(infixInfoDict['left__endBracketPos'], infixInfoDict['left__endBracketPos']+len(infixInfoDict['left__endBracketType'])):
                        self.occupiedBrackets.append(pos)
                        if self.showError():
                            print('>>>>adding :', self._eqs[pos], ' >>>> to self.occupiedBrackets')
            if infixInfoDict['right__type'] != 'infix' and infixInfoDict['right__startBracketType'] is not None:
                listOfOccupiedRanges.add((infixInfoDict['right__startBracketPos'], infixInfoDict['right__startBracketPos']+len(infixInfoDict['right__startBracketType'])))
                #backslashargs not occupiedBrackets, partialFrac test case
                if infixInfoDict['tight__rightType'] in ['enclosing', 'leftRight']:#if infixInfoDict['right__type'] in ['enclosing', 'leftRight']:##############TODO does it work for other polynomial like things?
                    for pos in range(infixInfoDict['right__startBracketPos'], infixInfoDict['right__startBracketPos']+len(infixInfoDict['right__startBracketType'])):
                        self.occupiedBrackets.append(pos)
                        if self.showError():
                            print('>>>>adding :', self._eqs[pos], ' >>>> to self.occupiedBrackets')
            if infixInfoDict['right__type'] != 'infix' and infixInfoDict['right__endBracketType'] is not None: # right__startBracketType is not None =/=> right__endBracketType is not None, since we may have enclosing brackets
                listOfOccupiedRanges.add((infixInfoDict['right__endBracketPos'], infixInfoDict['right__endBracketPos']+len(infixInfoDict['right__endBracketType'])))
                #backslashargs not occupiedBrackets, partialFrac test case
                if infixInfoDict['tight__rightType'] in ['enclosing', 'leftRight']:##############TODO does it work for other polynomial like things?
                    for pos in range(infixInfoDict['right__endBracketPos'], infixInfoDict['right__endBracketPos']+len(infixInfoDict['right__endBracketType'])):
                        self.occupiedBrackets.append(pos)
                        if self.showError():
                            print('>>>>adding :', self._eqs[pos], ' >>>> to self.occupiedBrackets')

        """
        after putting all the backslash_function, backslash_variable, infix, we still have brackets like these that are not removed:
        (x-3)(x+1)=x^2-6x-3
        """
        self.unoccupiedPoss = set()
        for pos in range(0, len(self._eqs)):
            # TODO binary search
            occupied = False 
            for occupiedRange in listOfOccupiedRanges:
                if occupiedRange[0] <= pos and pos < occupiedRange[1]:
                    occupied = True
            if not occupied:
                if self._eqs[pos] in (Latexparser.OPEN_BRACKETS+Latexparser.CLOSE_BRACKETS):
                    self.occupiedBrackets.append(pos)
                else:
                    self.unoccupiedPoss.add(pos)
                # if self._eqs[pos] not in (Latexparser.OPEN_BRACKETS+Latexparser.CLOSE_BRACKETS): # exclude brackets from becoming variables and numbers
                #     self.unoccupiedPoss.add(pos)
        self.unoccupiedPoss = sorted(list(self.unoccupiedPoss))
        if self.showError():
            print('leftOverPoss*******unoccupiedPoss*****************')
            print(self.unoccupiedPoss)
            unOccupiedChars = list(map(lambda pos: self._eqs[pos], self.unoccupiedPoss))
            print('unoccupiedChars**********')
            print(unOccupiedChars)
            occupiedStrs = list(map(lambda ran: self._eqs[ran[0]:ran[1]], listOfOccupiedRanges))
            print('listOfOccupiedRanges**********')
            print(listOfOccupiedRanges)
            print('occupiedStrs**********')
            print(occupiedStrs)
            print('occupiedBrackets****************')
            print(self.occupiedBrackets)
            occupiedBracketsStr = list(map(lambda pos: self._eqs[pos], self.occupiedBrackets))
            print('occupiedBracket(Actual)********************')
            print(occupiedBracketsStr)
            # import pdb;pdb.set_trace()
        if self.parallelise:
            self.event__findLeftOverPosition.set()


    def _contiguousLeftOvers(self): # left overs can be part of infix as well...., self.infixOperatorPositions, infix with no enclosing brackets are the top?
        """
        N=>number character
        V=>non-number character

        At the beginning, where we have no previous to compare type with, we just take it as word.
        This case, is handled by this logic:
        previousIsNume is None
        and we set previousIsNume = None
        Later previousIsNume will be a boolean, so its ok.

        we can have
        NN
        VV
        VN (like x0, or x_0)

        case 1 and 2 are handled by 
        isNume == previousIsNume
        case 3 is handled by 
        (not previousIsNume) and isNume

        but we cannot have 
        NV (like 2x, this requires a implicit-multiplication, deviens: 2*x)
        """
        if self.parallelise:
            self.event__findLeftOverPosition.wait()
        self.contiguousInfoList = []
        self.leaves = set() # for the unparsing function to check for base case
        previousIsNume = None
        previousPos = -1
        word = ""
        #wordPosRange = [None, None]
        wordStartPos = None
        ###############
        if self.showError():
            print('*************** grouping _contiguousLeftOvers')
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(self.unoccupiedPoss)
            print('***************END grouping _contiguousLeftOvers')
            # import pdb;pdb.set_trace()
        ###############
        for unoccupiedPos in self.unoccupiedPoss: # start with left-most leftover
            leftOverC = self._eqs[unoccupiedPos]
            isNume = isNum(leftOverC)
            #############
            if self.showError():
                print('leftOverC: ', leftOverC)
                print("leftOverC not in ['=', ' '] ", " (unoccupiedPos == previousPos+1) ", " previousIsNume is None ", " isNume == previousIsNume ", " (not previousIsNume) and isNume ")
                print(f"""{leftOverC not in ['=', ' ']} and (({(unoccupiedPos == previousPos+1)}) and ({previousIsNume is None} or {isNume == previousIsNume} or {(not previousIsNume) and isNume}))""")
                # import pdb;pdb.set_trace()
            #############
            if leftOverC not in ['=', ' '] and ((unoccupiedPos == previousPos+1) and (previousIsNume is None or (isNume == previousIsNume) or ((not previousIsNume) and isNume))): #contiguous
                word += leftOverC # word coagulation
                # if wordPosRange[0] is None:
                #     wordPosRange[0] = unoccupiedPos
                # else:
                #     wordPosRange[1] = unoccupiedPos # TODO refactor, we do not need this, use start+end instead
                if wordStartPos is None:
                    wordStartPos = unoccupiedPos
            else: # not contiguous
                # we are going to put in, if wordPosRange[1] still None, then its a single char.
                if len(word) > 0:
                    # if wordPosRange[1] is None:
                    #     print(leftOverC)
                    #     wordPosRange[1] = wordPosRange[0]+1 # for easy array index, python array indexing endPos always plus 1
                    self.contiguousInfoList.append({
                        'name':word, 
                        'startPos':wordStartPos,#wordPosRange[0],
                        'endPos':wordStartPos+len(word),#wordPosRange[0]+len(word),#wordPosRange[1],
                        'parent':None,
                        'type':'number' if isNum(word) else 'variable',
                        'ganzStartPos':wordStartPos,#wordPosRange[0],
                        'ganzEndPos':wordStartPos+len(word),#wordPosRange[0]+len(word),
                        'position':wordStartPos,#wordPosRange[0]#this is for building AST's convienence
                    })#, 'parentsInfo':self.wordLowestBackSlashArgumentParents}) # 
                    self.leaves.add(word)
                if leftOverC not in ['=', ' ']:
                    word = leftOverC
                    # wordPosRange = [unoccupiedPos, None]
                    wordStartPos = unoccupiedPos
                else:
                    word = ''
                    # wordPosRange = [None, None]
                    wordStartPos = None
            ############################
            if self.showError():
                print('_________loCha:  ', leftOverC)
                print('collectedWORD:  ', word)
                print('---------------------------------')
                pp.pprint(self.contiguousInfoList)
                print('---------------------------------')
                # import pdb;pdb.set_trace()
            ############################
            previousIsNume = isNume
            previousPos = unoccupiedPos
        self.contiguousInfoList.append({
            'name':word, 
            'startPos':wordStartPos,#wordPosRange[0],
            'endPos':wordStartPos+len(word),#wordPosRange[0]+len(word),
            'parent':None,
            'type':'number' if isNum(word) else 'variable',
            'ganzStartPos':wordStartPos,#wordPosRange[0],
            'ganzEndPos':wordStartPos+len(word),#wordPosRange[0]+len(word),
            'position':wordStartPos#wordPosRange[0]#this is for building AST's convienence
        })#, 'parentsInfo':self.wordLowestBackSlashArgumentParents}) # 
        self.leaves.add(word)
        #debugging double check that we got the contiguous right....
        if self.showError():
            print('&&&&&&&&&&&&&&&contiguousInfoList&&&&&&&&&&&&&&&&&')
            print(self.contiguousInfoList)
            print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&shorter:')
            print(list(map(lambda conti: (conti['name'], conti['startPos'], conti['endPos']), self.contiguousInfoList)))
            print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
            # import pdb;pdb.set_trace()
        if self.parallelise:
            self.event__contiguousLeftOvers.set()


    def _collateBackslashInfixLeftOversToContiguous(self):
        """
        #TODO maybe this can be a general algorithm.... grouping by consecutiveness.... even in 3D space... like how bubbles come together to make bigger bubbles (or atoms => molecules :))
        
        we do this with bubble-merge, comes with a debugging tool <<ppprint>>
        so that we can see whats going on
        """
        if self.parallelise:
            self.event__addImplicitZero.wait()
        allDings = sorted(self.contiguousInfoList+self.noBraBackslashPos+self.variablesPos+self.functionPos+self.infixList,key=lambda item: item['startPos'])
        self.consecutiveGroups = {} # (grenzeStartPos, grenzeEndPos) : [ding0, ding1, ...]

        #load each ding as keys first....
        for ding in allDings:
            if ding['type'] == 'infix':
                self.consecutiveGroups[(ding['position'], ding['position']+len(ding['name']))] = [ding]
            else:
                sKey = 'ganzStartPos'
                eKey = 'ganzEndPos'
                self.consecutiveGroups[(ding[sKey], ding[eKey])] = [ding]

        def rangesConsecutiveInEqsIgnoringSpace(grenzeRange0, grenzeRange1):
            start0 = grenzeRange0[0]
            end0 = grenzeRange0[1]
            start1 = grenzeRange1[0]#ding['ganzStartPos']
            end1 = grenzeRange1[1]#ding['ganzEndPos']
            ##############
            if self.showError():
                print(start0, end0, start1, end1, '<<<<rcieis<<<append<<', ' end0<=start1 ', end0<=start1, ' self._eqs[end0:start1].strip() ', self._eqs[end0:start1].strip(), ' len(self._eqs[end0:start1].strip()) ', len(self._eqs[end0:start1].strip()))
                print('<<<<rcieis<<<prepend<<', ' end1<=start0 ', end1<=start0, ' self._eqs[end1:start0].strip() ', self._eqs[end1:start0].strip(), ' len(self._eqs[end1:start0].strip()) ', len(self._eqs[end1:start0].strip()))
                # import pdb;pdb.set_trace()

            ##############
            hikinoko = []
            for hiki in range(end0, start1):
                if hiki not in self.occupiedBrackets:
                    hikinoko.append(self._eqs[hiki])
            # if end0<=start1 and len(self._eqs[end0:start1].strip()) == 0:#len(''.join(hikinoko).strip()) == 0:
            if end0<=start1 and len(''.join(hikinoko).strip()) == 0:
                # print('>>>>>>>>>>>>>>>>>>>>append')
                return 'append'
            hikinoko = []
            for hiki in range(end1, start0):
                if hiki not in self.occupiedBrackets:
                    hikinoko.append(self._eqs[hiki])
            # if end1<=start0 and len(self._eqs[end1:start0].strip()) == 0:#len(''.join(hikinoko).strip()) == 0:
            if end1<=start0 and len(''.join(hikinoko).strip()) == 0:
                # print('>>>>>>>>>>>>>>>>>>>>prepend')
                return 'prepend'
            return None

        sortedConsecutiveGroupsItems = sorted(self.consecutiveGroups.items(), key=lambda item: item[0][0])
        ###################################
        if self.showError():
            print('))))))))))))))))))))))))))))')
            self.ppprint(self.consecutiveGroups, sorted(self.consecutiveGroups.items(), key=lambda item: item[0][0]))
            print('SGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGI')
            print('))))))))))))))))))))))))))))')
        ###################################
        changed = True
        while changed:
            #sortedConsecutiveGroupsItems = sorted(self.consecutiveGroups.items(), key=lambda item: item[0][0])
            changed = False
            ###################
            if self.showError():
                print('@@@@@@@@@@@@@@@@@@@@@@@, reset sortedConsecutiveGroupsItems')
                self.ppprint(self.consecutiveGroups, sortedConsecutiveGroupsItems)
                print('@@@@@@@@@@@@@@@@@@@@@@@, reset sortedConsecutiveGroupsItems')
            ###################
            for grenzeRange0, existingDings0 in sortedConsecutiveGroupsItems: # TODO refactor to more dimensions

                if changed:
                    if self.showError():
                        print('BREAKKKKKKKKKKKKKKKKKKKKKKKKKKKK2')
                    break
                for grenzeRange1, existingDings1 in sortedConsecutiveGroupsItems:
                    if grenzeRange0 == grenzeRange1:
                        continue
                    #########
                    if self.showError():
                        def slst(existingD):
                            nD = []
                            for din in existingD:
                                if din['type'] == 'infix':
                                    dingTup = lambda ding : (ding['name'], ding['position'], ding['position']+len(ding['name']))
                                else:
                                    dingTup = lambda ding : (ding['name'], ding['ganzStartPos'], ding['ganzEndPos'])
                                nD.append(dingTup(din))
                            return nD
                        print('w', grenzeRange0, slst(existingDings0),'||||||', grenzeRange1, slst(existingDings1))
                    #########
                    action = rangesConsecutiveInEqsIgnoringSpace(grenzeRange0, grenzeRange1)
                    if action is not None:
                        if action == 'append':
                            newGrenzeRange = (grenzeRange0[0], grenzeRange1[1])
                            newExistingDings = existingDings0 + existingDings1
                        else: #action == 'prepend'
                            newGrenzeRange = (grenzeRange1[0], grenzeRange0[1])
                            newExistingDings = existingDings1 + existingDings0
                        if grenzeRange0 in self.consecutiveGroups:
                            del self.consecutiveGroups[grenzeRange0]
                        if grenzeRange1 in self.consecutiveGroups:
                            del self.consecutiveGroups[grenzeRange1]
                        self.consecutiveGroups[newGrenzeRange] = newExistingDings
                        sortedConsecutiveGroupsItems = sorted(self.consecutiveGroups.items(), key=lambda item: item[0][0])
                        changed = True
                        #############
                        if self.showError():
                            print('====================', action)
                            if action == 'append':
                                if ding['type'] == 'infix':
                                    dingTup = lambda ding : (ding['name'], ding['position'], ding['position']+len(ding['name']))
                                else:
                                    dingTup = lambda ding : (ding['name'], ding['ganzStartPos'], ding['ganzEndPos'])
                                print(grenzeRange0, list(map(lambda ding: dingTup(ding), existingDings0)))
                                print('++++++++++++++++++++')
                                print(grenzeRange1, list(map(lambda ding: dingTup(ding), existingDings1)))
                            else:
                                print(grenzeRange1, list(map(lambda ding: dingTup(ding), existingDings1)))
                                print('++++++++++++++++++++')
                                print(grenzeRange0, list(map(lambda ding: dingTup(ding), existingDings0)))
                            self.ppprint(self.consecutiveGroups, sortedConsecutiveGroupsItems)
                            print('====================')
                        #############
                        if self.showError():
                            print('BREAKKKKKKKKKKKKKKKKKKKKKKKKKKKK1')
                        break
                    if self.showError():
                        print('AFTER BREAK1, changed: ', changed)

        #here we would have allDings in consecutive-groupings, then we add the implicit multiplications yay! Complete answer....

        ##############
        if self.showError():
            print('self.consecutiveGroups<<<<<<<<<<<<<<')
            self.ppprint(self.consecutiveGroups, sorted(self.consecutiveGroups.items(), key=lambda item: item[0][0]))
            print('self.consecutiveGroups<<<<<<<<<<<<<<')
            # import pdb;pdb.set_trace()
        ##############

        if self.parallelise:
            self.event__collateBackslashInfixLeftOversToContiguous.set()


    def _graftGrenzeRangesIntoContainmentTree(self):
        """
        Order the grenze(key) of self.consecutiveGroups into a tree.
        If A=(a0, a1) and B=(b0, b1), 
        IF [A <= B] (a0<=b0 and b1<=a1), 
            THEN B is parent of A (A is child of B)
            egalment: self.grenzeChildrenOf[B] = [A]
        IF [B <= A] (b0<=a0 and a1<=b1), 
            THEN A is parent of B (B is child of A)
            egalment: self.grenzeChildrenOf[A] = [B]

        #
        """

        listPoss = list(self.consecutiveGroups.keys())
        def firstContainsSecond(p0, p1):
            return p0[0] <= p1[0] and p1[1] <= p0[1]
        def getId(p0):
            return p0

        roots, leaves, enclosureTree, levelToIDs, idToLevel = EnclosureTree.makeEnclosureTreeWithLevelRootLeaves(listPoss, firstContainsSecond, getId)
        #sort enclosureTree's leaves to ensure consistent
        enclosureTree = dict(map(lambda t: (t[0], sorted(t[1], key=lambda grenzeRange:grenzeRange[0])), enclosureTree.items()))
        #################
        if self.showError():
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            print('*******************************')
            print('enclosureTree:::')
            pp.pprint(enclosureTree)
            print('levelToIDs')
            pp.pprint(levelToIDs)
            print('mapped levelToIDs:')
            levelToShortDingsByConsecutiveness = {}
            for level, grenzeRanges in sorted(list(levelToIDs.items()), key=lambda t: t[0]):
                grenzeRangeToShortDings = {}
                for grenzeRange in grenzeRanges:
                    dings = self.consecutiveGroups[grenzeRange]
                    shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                    grenzeRangeToShortDings[grenzeRange] = shortDings
                levelToShortDingsByConsecutiveness[level] = grenzeRangeToShortDings
            pp.pprint(levelToShortDingsByConsecutiveness)
            print('idToLevel')
            pp.pprint(idToLevel)
            print('*******************************')
        #################
        def getParent(grenzeRange):
            for parent, children in enclosureTree.items():
                if grenzeRange in children:
                    return parent
        #####################
        if self.showError():
            print('**********************alleDing:')
            print(list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), self.alleDing)))
            print('**********************')
        #####################
        levelTo_grenzeRangeToRoot = {}
        for level, grenzeRanges in sorted(list(levelToIDs.items()), key=lambda t: t[0]): # t[0] is the level
            ################
            if self.showError():
                grenzeRangeToShortDings = {}
                for grenzeRange in grenzeRanges:
                    dings = self.consecutiveGroups[grenzeRange]
                    shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                    grenzeRangeToShortDings[grenzeRange] = shortDings
                print('level: ', level, 'grenzeRanges: ', grenzeRanges, 'grenzeRangeToShortDings', )
                pp.pprint(grenzeRangeToShortDings)
                print('**************************')
            ################
            grenzeRangeToRoot = {}
            for grenzeRange in grenzeRanges:
                dings = self.consecutiveGroups[grenzeRange]
                ################
                if self.showError():
                    print('**************************')
                    shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                    print('level: ', level, 'grenzeRange: ', grenzeRange, 'shortDings: ', shortDings)
                    print('BEGINT dings: ', list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), dings)))
                    print('**************************')
                ################
                #here, we need to 
                #__addImplicitZero
                dings = self.__addImplicitZero(dings)
                ################
                if self.showError():
                    print('**************************')
                    shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                    print('level: ', level, 'grenzeRange: ', grenzeRange, 'shortDings: ', shortDings)
                    print('After implicitzero dings: ', list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), dings)))
                    print('**************************')
                ################
                #__addImplicitMultiply
                dings = self.__addImplicitMultiply(dings) 
                ################
                if self.showError():
                    print('**************************')
                    shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                    print('level: ', level, 'grenzeRange: ', grenzeRange, 'shortDings: ', shortDings)
                    print('After implicitmultiply dings: ', list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), dings)))
                    print('**************************')
                ################
                self.consecutiveGroups[grenzeRange] = dings # replace with the new dings
                #__intraGrenzeSubtreeUe
                rootOfDingsWithGanzRange = self.__intraGrenzeSubtreeUe(dings) #{'root':ding, 'ganzStartPos':[of the whole tree], 'ganzEndPos':[of the whole tree]}
                grenzeRangeToRoot[grenzeRange] = rootOfDingsWithGanzRange
                ################
                if self.showError():
                    shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                    print('level: ', level, 'grenzeRange: ', grenzeRange, 'shortDings: ', shortDings)
                    print('After __intraGrenzeSubtreeUe dings: ', list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), dings)))
                    print('root: ', (rootOfDingsWithGanzRange['root']['name'], rootOfDingsWithGanzRange['root']['startPos'], rootOfDingsWithGanzRange['root']['endPos']), ' ganzrange: ', (rootOfDingsWithGanzRange['ganzStartPos'], rootOfDingsWithGanzRange['ganzEndPos']))
                    print('**************************')
                ################
            levelTo_grenzeRangeToRoot[level] = grenzeRangeToRoot
            ################
            if self.showError():
                grenzeRangeToShortDings = {}
                for grenzeRange in grenzeRanges:
                    dings = self.consecutiveGroups[grenzeRange]
                    shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                    grenzeRangeToShortDings[grenzeRange] = shortDings
                print('level: ', level, 'grenzeRanges: ', grenzeRanges, 'grenzeRangeToShortDings', )
                pp.pprint(grenzeRangeToShortDings)
                print('**************************')
            ################
        # print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@DOING INTERLEVEL')
        for level, grenzeRanges in sorted(list(levelToIDs.items()), key=lambda t: t[0]): # t[0] is the level
            grenzeRangeToRoot = levelTo_grenzeRangeToRoot[level]
            for grenzeRange in grenzeRanges:
                dings = self.consecutiveGroups[grenzeRange]
                #interlevel subtreeGrafting
                grenzeRangeParent = getParent(grenzeRange)
                ################
                if self.showError():
                    print('*********__interLevelSubtreeGraftingVOR*****************')
                    shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                    print('level: ', level, 'grenzeRange: ', grenzeRange, 'shortDings: ', shortDings)
                    print('After __interLevelSubtreeGrafting dings: ', list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), dings)))
                    print('grenzeRangeParent: ', grenzeRangeParent, ' PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPParent')
                    print('*************__interLevelSubtreeGraftingNACH*************')
                ################
                if grenzeRangeParent is not None: # we reached =, not need to interlevelsubtreegrafting
                    parentDings = self.consecutiveGroups[grenzeRangeParent]
                    rootOfDingsWithGanzRange = grenzeRangeToRoot[grenzeRange]
                    #replace the rootOfSubtree in the getParent(grenzeRange)=grenzeRange in self.consecutiveGroups
                    #update the parent/child relationship
                    parentDings = self.__interLevelSubtreeGrafting(rootOfDingsWithGanzRange, parentDings)#<<<<<<<<<<<<<<<<<TODO rootDIngsWithGanzRange NOT UPDATED!!!!!
                    self.consecutiveGroups[grenzeRangeParent] = parentDings

                    ################
                    if self.showError():
                        print('*********__interLevelSubtreeGraftingNACH***************** grenzeRangeParent: ', grenzeRangeParent)
                        shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                        print('level: ', level, 'grenzeRange: ', grenzeRange, 'shortDings: ', shortDings)
                        print('After __interLevelSubtreeGrafting dings: ', list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), dings)))
                        print('parentDings: ', list(map(lambda ding:(ding['name'], ding['startPos'], ding['endPos']), parentDings)))
                        print('**************************')
                    ################
                self.alleDing += dings # TODO something wrong with alleDing, its repeating dings that should not be

                #####################
                if self.showError():
                    print('**********************alleDing: <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    print(list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), self.alleDing)))
                    print('**********************alleDing:')
                #####################
        # self.__latexSpecialCases() #changes are made to the AST...


    def __addImplicitZero(self, dings):
        """
        we might have this:
        -ab=-ba

        Need to add a zero to this:

        self.contiguousInfoList.append({
            'word':word, 
            'startPos':wordPosRange[0],
            'endPos':wordPosRange[1],
            'parent':None,
            'type':'number' if isNum(word) else 'variable',
            'ganzStartPos':wordPosRange[0],
            'ganzEndPos':wordPosRange[1]
        })#, 'parentsInfo':self.wordLowestBackSlashArgumentParents}) # 


        contiguousInfoDict['parent'] = {
            'name':fInfoDict['name'],
            'startPos':fInfoDict['startPos'],
            'endPos':fInfoDict['endPos'],
            'type':'backslash_function',
            'childIdx':1,
            'ganzStartPos':fInfoDict['ganzStartPos'],
            'ganzEndPos':fInfoDict['ganzEndPos']
        }


                    'child':{1:{'name', 'startPos', 'endPos', 'type', 'ganzStartPos', 'ganzEndPos'}, 2:},

        """
        if self.showError():
            # for d in self.contiguousInfoList:
            #     print('>>>', d['name'], d['startPos'], d['endPos'], '<<<')
            # import pdb;pdb.set_trace()
            # print('self.consecutiveGroups<<<<<<<<<<<<<< _addImplicitZero')
            # self.ppprint(self.consecutiveGroups, sorted(self.consecutiveGroups.items(), key=lambda item: item[0][0]))
            # print('self.consecutiveGroups<<<<<<<<<<<<<<')
            # import pdb;pdb.set_trace()
            print('dings ~~~~~~~~addImplicitZero VOR')
            print(list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings)))
        if len(dings) > 1 and dings[0]['name'] == '-':
            dings[0]['child'][1] = {
                'name':'0',
                'startPos':dings[0]['startPos'],
                'endPos':dings[0]['startPos'], # implicit-zero is slim :)
                'type':'number',
                'ganzStartPos':dings[0]['ganzStartPos'],
                'ganzEndPos':dings[0]['ganzStartPos']
            }
            implicitZero = {
                'name':'0',
                'startPos':dings[0]['startPos'],
                'endPos':dings[0]['startPos'], # implicit-zero is slim :)
                'type':'number',
                'ganzStartPos':dings[0]['ganzStartPos'],
                'ganzEndPos':dings[0]['ganzStartPos'],
                'parent':{
                    'name':dings[0]['name'],
                    'startPos':dings[0]['startPos'],
                    'endPos':dings[0]['endPos'],
                    'type':'infix',
                    'childIdx':1,
                    'ganzStartPos':dings[0]['left__startBracketPos'],
                    'ganzEndPos':dings[0]['right__endBracketPos']
                }
            }
            self.contiguousInfoList.append(implicitZero)
            #also need to add to consecutiveGroups....
            dings.insert(0, implicitZero)

        if self.showError():
            # for d in self.contiguousInfoList:
            #     print('>>>', d['name'], d['startPos'], d['endPos'], '<<<')
            # import pdb;pdb.set_trace()
            # print('self.consecutiveGroups<<<<<<<<<<<<<< _addImplicitZero')
            # self.ppprint(self.consecutiveGroups, sorted(self.consecutiveGroups.items(), key=lambda item: item[0][0]))
            # print('self.consecutiveGroups<<<<<<<<<<<<<<')
            # import pdb;pdb.set_trace()
            print('dings ~~~~~~~~addImplicitZero NACH')
            print(list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings)))
        return dings


    def __addImplicitMultiply(self, dings):
        """
        _addImplicitMultiply cannot have left/Right_enclosing that is a backslash_arg

        start leftovers and noBra, others must have children, since child=argument, and only leftovers and noBra have no argument

        #turn the leftOvers into an AST with these rules:
        #if number|number, then (if consecutive{touzen hazu desu...}) scream
        #if number|variable, then add implicit multiply
        #if variable|number, then (if consecutive{touzen hazu desu...}) scream
        #if variable|variable, then add implicit multiply 
        """

        #there can be implicit multiply for infix, example "(1+1)(1+1)=4", only works for infix enclosed by brackets.
        #there can be implicit multiply for backslash_function, example "\sin(x)\cos(x)=\frac{1}{2}\sin(2x)"
        #there can be implicit multiply for backslash_variable. example "\\widehat{H}\\Psi=\\widehat{E}\\Psi"
        #there can be implicit multiply for mixed, like the above example with schrodinger Equation

        #subete wo mazereba...soshite, "renzokusei" ni shitagatte gumini shireba...
        #but sorting is useless, like in 
        #"\sin(x)\cos(x)=\frac{1}{2}\sin(2x)", the consecutiveness of \sin with \cos will be broken by x...
        #but sorting prevents cases like, say, A, B, C are consecutive,
        #but allDing = [A, C, B]
        #then
        #B will not be groupped together with A and C, only with either B and C, unless we re-check those existing in self.consecutiveGroups...
        #SO PLEASE NARABEKAENASAI! (startPos ni shitagatte ne)
        #have to do all-pairs consecutiveness checking.
        self.addedSymbolId = 0
        ding = dings[0] # this will be the root of treeified-dings (or be replaced)
        newDings = [ding]

        #dings are in consecutive order ... by way it was constructed above.
        if len(dings) > 1: # must have at least 2 items in dings, sonst kann nicht implicitMultiply beibringen
            for idx in range(1, len(dings)): # assumes that dings are sorted by startPos

                #all the types are number, variable (leftOvers&backslashNoBra); backslash_variable, backslash_function, infixes...
                prevDing = dings[idx-1]
                ding = dings[idx]
                if (prevDing['type'] == 'number' and ding['type'] == 'number') or (prevDing['type'] == 'variable' and ding['type'] == 'number'):
                    if not((prevDing['startPos'] == prevDing['endPos']) or (ding['startPos'] == ding['endPos'])): #then its added zero to the hanging minus infix
                        ###########
                        import pdb;pdb.set_trace()
                        ###########
                        raise Exception('number&number, variable&number should have been catch earlier')

                ################### find nearest infix with rightCloseBracket, left of dding, then first Ding in dings
                def findLeftestInfixFrom(dding):
                    leftest = dings[0]
                    for ding in dings: # assumes that dings are sorted by startPos
                        if ding['name'] == dding['name'] and ding['startPos'] == dding['startPos']: # if dding is the leftest infix, then return dding
                            return leftest
                        if ding['type'] == 'infix' and (ding['right__type'] =='enclosing' or ding['right__type'] == 'leftRight'):
                            leftest = ding
                    return leftest
                ################### find nearest infix with leftOpenBracket, right of dding, if no, then last Ding in dings
                def findRightestInfixFrom(dding):
                    rightest = dings[-1]
                    for ding in reversed(dings): # assumes that dings are sorted by startPos
                        if ding['name'] == dding['name'] and ding['startPos'] == dding['startPos']: # if dding is the rightest infix, then return dding
                            return rightest
                        if ding['type'] == 'infix' and (ding['left__type'] =='enclosing' or ding['left__type'] == 'leftRight'):
                            rightest = ding
                    return rightest
                ###################

                if prevDing['type'] == 'infix' and ding['type'] == 'infix':
                    #if prevDing['right__startBracketType'] is not None and prevDing['right__endBracketType'] is not None and ding['left__startBracketType'] is not None and ding['left__endBracketType']: 
                    if prevDing['right__type'] == 'leftRight' and ding['left__type'] == 'leftRight':# ???+(...)*(...)+???
                        # implicitMultiplyNode = ('*', (self.addedSymbolId, -1))
                        self.addedSymbolId += 1
                        implicitMultiplyInfoDict = { # rightarg * leftarg
                            'name':'*',
                            'position':prevDing['right__endBracketPos']+lenOrZero(prevDing['right__endBracketType']),
                            'type':'implicit',
                            'startPos':prevDing['right__startBracketPos'],
                            'endPos':ding['left__endBracketPos'],
                            'ganzStartPos':prevDing['right__startBracketPos'],
                            'ganzEndPos':ding['left__endBracketPos'],
                            # rightarg
                            'left__startBracketPos':prevDing['right__startBracketPos'], #TODO to test leaves with brackets..
                            'left__startBracketType':prevDing['right__startBracketType'], #TODO to test leaves with brackets..
                            'left__endBracketPos':prevDing['right__endBracketPos'], #TODO to test leaves with brackets..
                            'left__endBracketType':prevDing['right__endBracketType'], #TODO to test leaves with brackets..
                            'left__argStart':prevDing['right__startBracketPos'] + lenOrZero(prevDing['right__startBracketType']), # without the bracket
                            'left__argEnd':prevDing['right__endBracketPos'] - lenOrZero(prevDing['right__endBracketType']), # without the bracket
                            # leftarg
                            'right__startBracketPos':ding['left__startBracketPos'], #TODO to test leaves with brackets..
                            'right__startBracketType':ding['left__startBracketType'], #TODO to test leaves with brackets..
                            'right__endBracketPos':ding['left__endBracketPos'], #TODO to test leaves with brackets...
                            'right__endBracketType':ding['left__startBracketPos'], #TODO to test leaves with brackets...
                            'right__argStart':ding['left__startBracketPos'] + lenOrZero(ding['left__startBracketType']),
                            'right__argEnd':ding['left__endBracketPos'] - lenOrZero(ding['left__endBracketType']),

                            'child':{1:None, 2:None},
                            'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                        }
                        self.infixList.append(implicitMultiplyInfoDict)
                        newDings.append(implicitMultiplyInfoDict)
                        ###################
                        if self.showError():
                            print('(infix|leftRight)(infix|leftRight)adding implicit-multiply between')
                            print((prevDing['name'], prevDing['startPos'], prevDing['endPos']))
                            print('vs')
                            print((ding['name'], ding['startPos'], ding['endPos']))
                            print('*******************************adding implicit-multiply')
                        ###################
                    #elif prevDing['right__startBracketType'] is not None and prevDing['right__endBracketType'] is not None and ding['left__startBracketType'] is not None: 
                    elif prevDing['right__type'] == 'leftRight' and ding['left__type'] == 'enclosing': #???+(...)*(...+???)
                        #could be ding['right__type'] == 'enclosing' too
                        # implicitMultiplyNode = ('*', (self.addedSymbolId, -1))
                        self.addedSymbolId += 1
                        implicitMultiplyInfoDict = {# rightarg * ganz
                            'name':'*',
                            'position':prevDing['right__endBracketPos']+lenOrZero(prevDing['right__endBracketType']),
                            'type':'implicit',
                            'startPos':prevDing['right__startBracketPos'],
                            'endPos':ding['ganzEndPos'],
                            'ganzStartPos':prevDing['right__startBracketPos'],
                            'ganzEndPos':ding['ganzEndPos'],
                            #rightarg
                            'left__startBracketPos':prevDing['right__startBracketPos'], #TODO to test leaves with brackets..
                            'left__startBracketType':prevDing['right__startBracketType'], #TODO to test leaves with brackets..
                            'left__endBracketPos':prevDing['right__endBracketPos'], #TODO to test leaves with brackets..
                            'left__endBracketType':prevDing['right__endBracketType'], #TODO to test leaves with brackets..
                            'left__argStart':prevDing['right__startBracketPos'] + lenOrZero(prevDing['right__startBracketType']), # without the bracket
                            'left__argEnd':prevDing['right__endBracketPos'] - lenOrZero(prevDing['right__endBracketType']), # without the bracket
                            #ganz
                            'right__startBracketPos':ding['ganzStartPos'], #TODO to test leaves with brackets..
                            'right__startBracketType':ding['left__startBracketType'], #TODO to test leaves with brackets..
                            'right__endBracketPos':ding['ganzEndPos'], #TODO to test leaves with brackets...
                            'right__endBracketType':ding['right__endBracketType'], #TODO to test leaves with brackets...
                            'right__argStart':ding['ganzStartPos'] + lenOrZero(ding['left__startBracketType']), # without the bracket
                            'right__argEnd':ding['ganzEndPos'] - lenOrZero(ding['right__endBracketType']), # without the bracket

                            'child':{1:None, 2:None},
                            'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                        }
                        self.infixList.append(implicitMultiplyInfoDict)
                        newDings.append(implicitMultiplyInfoDict)
                        ###################
                        if self.showError():
                            print('(infix|leftRight)(infix|enclosing)adding implicit-multiply between')
                            print((prevDing['name'], prevDing['startPos'], prevDing['endPos']))
                            print('vs')
                            print((ding['name'], ding['startPos'], ding['endPos']))
                            print('*******************************adding implicit-multiply')
                        ###################
                    #elif prevDing['right__endBracketType'] is not None and ding['left__startBracketType'] is not None and ding['left__endBracketType'] is not None: 
                    elif prevDing['right__type'] == 'enclosing' and ding['left__type'] == 'leftRight': #(???+...)*(...)+???
                        # could be prevDing['left__type'] == 'enclosing'
                        # implicitMultiplyNode = ('*', (self.addedSymbolId, -1))
                        self.addedSymbolId += 1
                        implicitMultiplyInfoDict = {# ganz * leftarg
                            'name':'*',
                            'position':prevDing['right__endBracketPos']+lenOrZero(prevDing['right__endBracketType']),
                            'type':'implicit',
                            'startPos':prevDing['ganzStartPos'],
                            'endPos':ding['left__endBracketPos'],
                            'ganzStartPos':prevDing['ganzStartPos'],
                            'ganzEndPos':ding['left__endBracketPos'],
                            #ganz
                            'left__startBracketPos':prevDing['ganzStartPos'], #TODO to test leaves with brackets..
                            'left__startBracketType':prevDing['left__startBracketType'], #TODO to test leaves with brackets..
                            'left__endBracketPos':prevDing['ganzEndPos'], #TODO to test leaves with brackets..
                            'left__endBracketType':prevDing['right__endBracketType'], #TODO to test leaves with brackets..
                            'left__argStart':prevDing['ganzStartPos'] + lenOrZero(prevDing['left__startBracketType']), # without the bracket
                            'left__argEnd':prevDing['ganzEndPos'] - lenOrZero(prevDing['right__endBracketType']), # without the bracket
                            #leftarg
                            'right__startBracketPos':ding['left__startBracketPos'], #TODO to test leaves with brackets..
                            'right__startBracketType':ding['left__startBracketType'], #TODO to test leaves with brackets..
                            'right__endBracketPos':ding['left__endBracketPos'], #TODO to test leaves with brackets...
                            'right__endBracketType':ding['left__startBracketPos'], #TODO to test leaves with brackets...
                            'right__argStart':ding['left__startBracketPos'] + lenOrZero(ding['left__startBracketType']), #without the bracket
                            'right__argEnd':ding['left__endBracketPos'] - lenOrZero(ding['left__endBracketType']), #without the bracket

                            'child':{1:None, 2:None},
                            'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                        }
                        self.infixList.append(implicitMultiplyInfoDict)
                        newDings.append(implicitMultiplyInfoDict)
                        ###################
                        if self.showError():
                            print('(infix|enclosing)(infix|leftRight)adding implicit-multiply between')
                            print((prevDing['name'], prevDing['startPos'], prevDing['endPos']))
                            print('vs')
                            print((ding['name'], ding['startPos'], ding['endPos']))
                            print('*******************************adding implicit-multiply')
                        ###################
                    #elif prevDing['right__endBracketType'] is not None and ding['left__startBracketType'] is not None: 
                    elif prevDing['right__type'] == 'enclosing' and ding['left__type'] == 'enclosing': #(???+...)*(...+???)
                        # implicitMultiplyNode = ('*', (self.addedSymbolId, -1))
                        self.addedSymbolId += 1
                        implicitMultiplyInfoDict = { # ganz * ganz
                            'name':'*',
                            'position':prevDing['right__endBracketPos']+lenOrZero(prevDing['right__endBracketType']),
                            'type':'implicit',
                            'startPos':prevDing['ganzStartPos'],
                            'endPos':ding['ganzEndPos'],
                            'ganzStartPos':prevDing['ganzStartPos'],
                            'ganzEndPos':ding['ganzEndPos'],
                            #ganz
                            'left__startBracketPos':prevDing['ganzStartPos'], #TODO to test leaves with brackets..
                            'left__startBracketType':prevDing['left__startBracketType'], #TODO to test leaves with brackets..
                            'left__endBracketPos':prevDing['ganzEndPos'], #TODO to test leaves with brackets..
                            'left__endBracketType':prevDing['right__endBracketType'], #TODO to test leaves with brackets..
                            'left__argStart':prevDing['ganzStartPos'] + lenOrZero(prevDing['left__startBracketType']), # without the bracket
                            'left__argEnd':prevDing['ganzEndPos'] - lenOrZero(prevDing['right__endBracketType']), # without the bracket
                            #ganz
                            'right__startBracketPos':ding['ganzStartPos'], #TODO to test leaves with brackets..
                            'right__startBracketType':ding['left__startBracketType'], #TODO to test leaves with brackets..
                            'right__endBracketPos':ding['ganzEndPos'], #TODO to test leaves with brackets...
                            'right__endBracketType':ding['right__endBracketType'], #TODO to test leaves with brackets...
                            'right__argStart':ding['ganzStartPos'] + lenOrZero(ding['left__startBracketType']), # without the bracket
                            'right__argEnd':ding['ganzEndPos'] - lenOrZero(ding['right__endBracketType']), # without the bracket

                            'child':{1:None, 2:None},
                            'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                        }
                        self.infixList.append(implicitMultiplyInfoDict)
                        newDings.append(implicitMultiplyInfoDict)
                        ###################
                        if self.showError():
                            print('(infix|enclosing)(infix|enclosing)adding implicit-multiply between')
                            print((prevDing['name'], prevDing['startPos'], prevDing['endPos']))
                            print('vs')
                            print((ding['name'], ding['startPos'], ding['endPos']))
                            print('*******************************adding implicit-multiply')
                        ###################


                # elif (prevDing['type'] == 'number' and prevDing['type'] == 'number') or (prevDing['type'] == 'variable' and ding['type'] == 'number'):#there are no other possible infix types..., heran haben wir nur (number/variable/backslash_variable/backslash_function)
                #     raise Exception('Should not have number|number; variable|number, something wrong with leftOver-finding-method')
                elif prevDing['type'] == 'infix': # ding['type'] != 'infix'
                    #if prevDing['right__startBracketType'] is not None and prevDing['right__endBracketType'] is not None: 
                    if prevDing['right__type'] == 'leftRight': #???+(...)*Ding, ???+(Ding)
                        if not(prevDing['right__argStart'] <= ding['position'] and ding['position']+len(ding['name']) <= prevDing['right__argEnd']):
                            #nearest infix with leftBracket, right of Ding
                            # infixRightOfDing = findRightestInfixFrom(ding) # that has leftCloseBracket
                            #infixRightOfDing might not be infix, since there might not have infix right of Ding
                            # implicitMultiplyNode = ('*', (self.addedSymbolId, -1))
                            self.addedSymbolId += 1
                            import pdb;pdb.set_trace()
                            implicitMultiplyInfoDict = {# rightarg * ganz
                                'name':'*',
                                'position':prevDing['right__endBracketPos']+lenOrZero(prevDing['right__endBracketType']),
                                'type':'implicit',
                                'startPos':prevDing['right__startBracketPos'],
                                'endPos':ding.get('endPos'),
                                'ganzStartPos':prevDing['right__startBracketPos'],
                                'ganzEndPos':ding.get('ganzEndPos'),
                                #rightarg
                                'left__startBracketPos':prevDing['right__startBracketPos'], #TODO to test leaves with brackets..
                                'left__startBracketType':prevDing['right__startBracketType'], #TODO to test leaves with brackets..
                                'left__endBracketPos':prevDing['right__endBracketPos'], #TODO to test leaves with brackets..
                                'left__endBracketType':prevDing['right__endBracketType'], #TODO to test leaves with brackets..
                                'left__argStart':prevDing['right__startBracketPos'] + lenOrZero(prevDing['right__startBracketType']), # without the bracket
                                'left__argEnd':prevDing['right__endBracketPos'] - lenOrZero(prevDing['right__endBracketType']), # without the bracket
                                #Ding, infixRightOfDing might not be infix
                                'right__startBracketPos':ding.get('right__startBracketPos'), #TODO to test leaves with brackets..
                                'right__startBracketType':ding.get('right__startBracketType'), #TODO to test leaves with brackets..
                                'right__endBracketPos':ding.get('right__endBracketPos'), #TODO to test leaves with brackets...
                                'right__endBracketType':ding.get('right__endBracketType'), #TODO to test leaves with brackets...
                                'right__argStart':ding.get('right__argStart'),
                                'right__argEnd':ding.get('right__argEnd'),

                                'child':{1:None, 2:None},
                                'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                            }
                            self.tempBracketFinderList = [implicitMultiplyInfoDict]
                            self.__updateInfixNearestBracketInfix(self.tempBracketFinderList, self.infixList)
                            self.infixList.append(implicitMultiplyInfoDict)
                            newDings.append(implicitMultiplyInfoDict)
                            ###################
                            if self.showError():
                                print('(infix|leftRight)(ding)adding implicit-multiply between')
                                print((prevDing['name'], prevDing['startPos'], prevDing['endPos']))
                                print('vs')
                                print((ding['name'], ding['startPos'], ding['endPos']))
                                print('*******************************adding implicit-multiply')
                            ###################
                    #elif prevDing['right__endBracketType'] is not None:
                    elif prevDing['right__type'] == 'enclosing': #(???+...)*Ding, (???+Ding)
                        # TODO need to check for this case: (???+Ding)
                        if not(prevDing['left__startBracketPos'] <= ding['position'] and ding['position'] + len(ding['name']) <= prevDing['right__endBracketPos']):
                            #for the case test__BODMAS__enclosingBracketInBackslashArg
                            # infixRightOfDing = findRightestInfixFrom(ding) # that has leftCloseBracket
                            # implicitMultiplyNode = ('*', (self.addedSymbolId, -1))
                            self.addedSymbolId += 1
                            # import pdb;pdb.set_trace()
                            implicitMultiplyInfoDict = {# ganz * leftarg
                                'name':'*',
                                'position':prevDing['right__endBracketPos']+lenOrZero(prevDing['right__endBracketType']),
                                'type':'implicit',
                                'startPos':prevDing['ganzStartPos'],
                                'endPos':ding.get('endPos'),
                                'ganzStartPos':prevDing['ganzStartPos'],
                                'ganzEndPos':ding.get('ganzEndPos'),
                                #ganz
                                'left__startBracketPos':prevDing['ganzStartPos'], #TODO to test leaves with brackets..
                                'left__startBracketType':prevDing['left__startBracketType'], #TODO to test leaves with brackets..
                                'left__endBracketPos':prevDing['ganzEndPos'], #TODO to test leaves with brackets..
                                'left__endBracketType':prevDing['right__endBracketType'], #TODO to test leaves with brackets..
                                'left__argStart':prevDing['ganzStartPos'] + lenOrZero(prevDing['left__startBracketType']), # without the bracket
                                'left__argEnd':prevDing['ganzEndPos'] - lenOrZero(prevDing['right__endBracketType']), # without the bracket
                                #Ding
                                'right__startBracketPos':ding.get('right__startBracketPos'), #TODO to test leaves with brackets..
                                'right__startBracketType':ding.get('right__startBracketType'), #TODO to test leaves with brackets..
                                'right__endBracketPos':ding.get('right__endBracketPos'), #TODO to test leaves with brackets...
                                'right__endBracketType':ding.get('right__endBracketType'), #TODO to test leaves with brackets...
                                'right__argStart':ding.get('right__argStart'),
                                'right__argEnd':ding.get('right__argEnd'),

                                'child':{1:None, 2:None},
                                'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                            }
                            self.tempBracketFinderList = [implicitMultiplyInfoDict]
                            self.__updateInfixNearestBracketInfix(self.tempBracketFinderList, self.infixList)
                            self.infixList.append(implicitMultiplyInfoDict)
                            newDings.append(implicitMultiplyInfoDict)
                            ###################
                            if self.showError():
                                print('(prevDing)(infix|enclosing)adding implicit-multiply between')
                                print((prevDing['name'], prevDing['startPos'], prevDing['endPos']))
                                print('vs')
                                print((ding['name'], ding['startPos'], ding['endPos']))
                                print('*******************************adding implicit-multiply')
                            ###################
                elif ding['type'] == 'infix': # prevDing['type'] != 'infix'
                    #if ding['left__startBracketType'] is not None and ding['left__endBracketType'] is not None:
                    if ding['left__type'] == 'leftRight': #prevDing*(...)+???, (prevDing)+???
                        if not(ding['left__argStart'] <= prevDing['position'] and prevDing['position']+len(prevDing['name']) <= ding['left__argEnd']):
                            # infixLeftOfDing = findLeftestInfixFrom(prevDing) # that has rightCloseBracket
                            # implicitMultiplyNode = ('*', (self.addedSymbolId, -1))
                            self.addedSymbolId += 1
                            implicitMultiplyInfoDict = {# ganz * leftarg
                                'name':'*',
                                'position':ding['left__startBracketPos'],#-len('*')
                                'type':'implicit',
                                'startPos':prevDing.get('startPos'),
                                'endPos':ding['left__endBracketPos'],
                                'ganzStartPos':prevDing.get('ganzStartPos'),
                                'ganzEndPos':ding['left__endBracketPos'],
                                #Ding
                                'left__startBracketPos':prevDing.get('left__startBracketPos'), #TODO to test leaves with brackets..
                                'left__startBracketType':prevDing.get('left__startBracketType'), #TODO to test leaves with brackets..
                                'left__endBracketPos':prevDing.get('left__endBracketPos'), #TODO to test leaves with brackets..
                                'left__endBracketType':prevDing.get('left__endBracketType'), #TODO to test leaves with brackets..
                                'left__argStart':prevDing.get('left__argStart'), # without the bracket
                                'left__argEnd':prevDing.get('left__argEnd'), # without the bracket
                                #leftarg
                                'right__startBracketPos':ding['left__startBracketPos'], #TODO to test leaves with brackets..
                                'right__startBracketType':ding['left__startBracketType'], #TODO to test leaves with brackets..
                                'right__endBracketPos':ding['left__endBracketPos'], #TODO to test leaves with brackets...
                                'right__endBracketType':ding['left__startBracketPos'], #TODO to test leaves with brackets...
                                'right__argStart':ding['left__startBracketPos'] + lenOrZero(ding['left__startBracketType']), #without the bracket
                                'right__argEnd':ding['left__endBracketPos'] - lenOrZero(ding['left__endBracketType']), #without the bracket

                                'child':{1:None, 2:None},
                                'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                            }
                            self.tempBracketFinderList = [implicitMultiplyInfoDict]
                            self.__updateInfixNearestBracketInfix(self.tempBracketFinderList, self.infixList)
                            self.infixList.append(implicitMultiplyInfoDict)
                            newDings.append(implicitMultiplyInfoDict)
                            ###################
                            if self.showError():
                                print('(prevDing)(infix|leftRight)adding implicit-multiply between')
                                print((prevDing['name'], prevDing['startPos'], prevDing['endPos']))
                                print('vs')
                                print((ding['name'], ding['startPos'], ding['endPos']))
                                print('*******************************adding implicit-multiply')
                            ###################
                    #elif ding['left__startBracketType'] is not None:
                    elif ding['left__type'] == 'enclosing': #Ding*(...+???), (Ding+???)
                        if not(ding['left__startBracketPos'] <= prevDing['position'] and prevDing['position'] + len(prevDing['name']) <= ding['right__endBracketPos']):
                            #for the case test__BODMAS__enclosingBracketInBackslashArg
                            # infixLeftOfDing = findLeftestInfixFrom(prevDing) # that has rightCloseBracket
                            # import pdb;pdb.set_trace()
                            # implicitMultiplyNode = ('*', (self.addedSymbolId, -1))
                            self.addedSymbolId += 1
                            implicitMultiplyInfoDict = {# rightarg * ganz
                                'name':'*',
                                'position':ding['left__startBracketPos'],#-len('*')
                                'type':'implicit',
                                'startPos':prevDing.get('startPos'),
                                'endPos':ding['ganzEndPos'],
                                'ganzStartPos':prevDing.get('ganzStartPos'),
                                'ganzEndPos':ding['ganzEndPos'],
                                #Ding
                                'left__startBracketPos':prevDing.get('left__startBracketPos'), #somehow... infixLeftOfDing = {'name': 'x', 'startPos': 8, 'endPos': 9, 'parent': None, 'type': 'variable', 'ganzStartPos': 8, 'ganzEndPos': 9, 'position': 8}
                                'left__startBracketType':prevDing.get('left__startBracketType'), #TODO to test leaves with brackets..
                                'left__endBracketPos':prevDing.get('left__endBracketPos'), #TODO to test leaves with brackets..
                                'left__endBracketType':prevDing.get('left__endBracketType'), #TODO to test leaves with brackets..
                                'left__argStart':prevDing.get('left__argStart'), # without the bracket
                                'left__argEnd':prevDing.get('left__argEnd'), # without the bracket
                                #ganz
                                'right__startBracketPos':ding['ganzStartPos'], #TODO to test leaves with brackets..
                                'right__startBracketType':ding['left__startBracketType'], #TODO to test leaves with brackets..
                                'right__endBracketPos':ding['ganzEndPos'], #TODO to test leaves with brackets...
                                'right__endBracketType':ding['right__endBracketType'], #TODO to test leaves with brackets...
                                'right__argStart':ding['ganzStartPos'] + lenOrZero(ding['left__startBracketType']), # without the bracket
                                'right__argEnd':ding['ganzEndPos'] - lenOrZero(ding['right__endBracketType']), # without the bracket

                                'child':{1:None, 2:None},
                                'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                            }
                            self.tempBracketFinderList = [implicitMultiplyInfoDict]
                            self.__updateInfixNearestBracketInfix(self.tempBracketFinderList, self.infixList)
                            self.infixList.append(implicitMultiplyInfoDict)
                            newDings.append(implicitMultiplyInfoDict)
                            ###################
                            if self.showError():
                                print('(prevDing)(infix|enclosing)adding implicit-multiply between')
                                print((prevDing['name'], prevDing['startPos'], prevDing['endPos']))
                                print('vs')
                                print((ding['name'], ding['startPos'], ding['endPos']))
                                print('*******************************adding implicit-multiply')
                            ###################
                else: #both prevDing & ding are not infixes.... 
                    #add implicit multiply to (prevDing and ding)
                    #prevDing/ding can be number/variable/backslash_variable/backslash_function
                    #-need to provide parent of () for update child [name, startPos, endPos, ganzStartPos, ganzEndPos]
                    # implicitMultiplyNode = ('*', (self.addedSymbolId, -1))
                    self.addedSymbolId += 1
                    implicitMultiplyInfoDict = {
                        'name':'*',
                        'position':prevDing['ganzEndPos'],
                        'type':'implicit',
                        'startPos':prevDing['startPos'],
                        'endPos':ding['endPos'],
                        'ganzStartPos':prevDing['ganzStartPos'],
                        'ganzEndPos':ding['ganzEndPos'],
                        'left__startBracketPos':None, #TODO to test leaves with brackets..
                        'left__startBracketType':None, #TODO to test leaves with brackets..
                        'left__endBracketPos':None, #TODO to test leaves with brackets..
                        'left__endBracketType':None, #TODO to test leaves with brackets..
                        'left__argStart':prevDing['startPos'],
                        'left__argEnd':prevDing['endPos'],

                        'right__startBracketPos':None, #TODO to test leaves with brackets..
                        'right__startBracketType':None, #TODO to test leaves with brackets..
                        'right__endBracketPos':None, #TODO to test leaves with brackets...
                        'right__endBracketType':None, #TODO to test leaves with brackets...
                        'right__argStart':ding['startPos'],
                        'right__argEnd':ding['endPos'],

                        'child':{1:None, 2:None},
                        'parent':None
                    }
                    self.tempBracketFinderList = [implicitMultiplyInfoDict]
                    self.__updateInfixNearestBracketInfix(self.tempBracketFinderList, self.infixList)
                    self.infixList.append(implicitMultiplyInfoDict)
                    newDings.append(implicitMultiplyInfoDict)
                    ###################
                    if self.showError():
                        print('(prevDing)(ding)adding implicit-multiply between')
                        print((prevDing['name'], prevDing['startPos'], prevDing['endPos']))
                        print('vs')
                        print((ding['name'], ding['startPos'], ding['endPos']))
                        print('*******************************adding implicit-multiply')
                    ###################
                newDings.append(ding) # add old ding back
        if self.showError():
            print('~~~~~~~~~~~~~~~~~~~~implicitMultiply~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            print('oldDings:')
            print(list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings)))
            print('newDings:')
            print(list(map(lambda d: (d['name'], d['startPos'], d['endPos']), newDings)))
            print('~~~~~~~~~~~~~~~~~~~~implicitMultiply~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

        return newDings


    def __intraGrenzeSubtreeUe(self, newDings):
        def getMostLeftStartPos(ting, currentGanzStartPos):
            if ting['type'] == 'infix':
                # ##########
                # print('tingleft', (ting['name'], ting['startPos'], ting['endPos']))
                # print(ting)
                # print(ting['type'], '&&&leftcontre: ', ting['left__argStart'], currentGanzStartPos)
                # import pdb;pdb.set_trace()
                # ##########
                return min(ting['left__argStart'], currentGanzStartPos)
            else:
                # ##########
                # print('tingleft', (ting['name'], ting['startPos'], ting['endPos']))
                # print(ting)
                # print(ting['type'], '&&&leftcontre: ', ting['ganzStartPos'], currentGanzStartPos)
                # import pdb;pdb.set_trace()
                # ##########
                return min(ting['ganzStartPos'], currentGanzStartPos)
            # return min(ting['ganzStartPos'], currentGanzStartPos)
        def getMostRightEndPos(ting, currentGanzEndPos):
            if ting['type'] == 'infix':
                return max(ting['right__argEnd'], currentGanzEndPos)
            else:
                return max(ting['ganzEndPos'], currentGanzEndPos)
            # ##########
            # print('tingright', (ting['name'], ting['startPos'], ting['endPos']))
            # print(ting)
            # print('&&&rightcontre: ', ting['ganzEndPos'], currentGanzEndPos)
            # ##########
            # return max(ting['ganzEndPos'], currentGanzEndPos)
        treeifiedDingsGanzStartPos = len(self._eqs) + 1
        treeifiedDingsGanzEndPos = -1
        ding = newDings[0]
        ############
        if self.showError():
            print('checking treeifiedDingsGanzStartPos/treeifiedDingsGanzEndPos')
            print('dings', list(map(lambda d: (d['name'], d['startPos'], d['endPos']), newDings)))
            print('ding', ((ding['name'], ding['startPos'], ding['endPos'])))
            print('treeifiedDingsGanzStartPos', treeifiedDingsGanzStartPos)
            print('treeifiedDingsGanzEndPos', treeifiedDingsGanzEndPos)
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            # import pdb;pdb.set_trace()
        ############
        treeifiedDingsGanzStartPos = getMostLeftStartPos(ding, treeifiedDingsGanzStartPos)
        treeifiedDingsGanzEndPos = getMostRightEndPos(ding, treeifiedDingsGanzEndPos)
        ############
        if self.showError():
            print('checking treeifiedDingsGanzStartPos/treeifiedDingsGanzEndPos')
            print('dings', list(map(lambda d: (d['name'], d['startPos'], d['endPos']), newDings)))
            print('ding', ((ding['name'], ding['startPos'], ding['endPos'])))
            print('treeifiedDingsGanzStartPos', treeifiedDingsGanzStartPos)
            print('treeifiedDingsGanzEndPos', treeifiedDingsGanzEndPos)
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!2!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            # import pdb;pdb.set_trace()
        ############
        if len(newDings) > 0:
            #add child/parent relationship to infixes of newDings
            #should have at least 2 things in newDings, else cannot form relationship
            #need to sort according to ^/*-+, then we go from left to right
            if self.showError():
                print('grouping new dings by priority****************************************')
                # import pdb;pdb.set_trace()
            processed = set() # this should include all the dingPos of the infixes, and then later the arguments that are linked to the infixes
            prioritiesToDingsPos = {}
            dingPosToPriorities = {}
            for dingPos, ding in enumerate(newDings):
                ############
                # if self.showError():
                #     print('checking treeifiedDingsGanzStartPos/treeifiedDingsGanzEndPos')
                #     print('dings', list(map(lambda d: (d['name'], d['startPos'], d['endPos']), newDings)))
                #     print('ding', ((ding['name'], ding['startPos'], ding['endPos'])))
                #     print('treeifiedDingsGanzStartPos', treeifiedDingsGanzStartPos)
                #     print('treeifiedDingsGanzEndPos', treeifiedDingsGanzEndPos)
                #     print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!3!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    # import pdb;pdb.set_trace()
                ############
                treeifiedDingsGanzStartPos = getMostLeftStartPos(ding, treeifiedDingsGanzStartPos) # but this does not contain the information of implicit multiply
                treeifiedDingsGanzEndPos = getMostRightEndPos(ding, treeifiedDingsGanzEndPos)
                ############
                # if self.showError():
                #     print('checking treeifiedDingsGanzStartPos/treeifiedDingsGanzEndPos')
                #     print('dings', list(map(lambda d: (d['name'], d['startPos'], d['endPos']), newDings)))
                #     print('ding', ((ding['name'], ding['startPos'], ding['endPos'])))
                #     print('treeifiedDingsGanzStartPos', treeifiedDingsGanzStartPos)
                #     print('treeifiedDingsGanzEndPos', treeifiedDingsGanzEndPos)
                #     print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!4!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    # import pdb;pdb.set_trace()
                ############
                if self.showError():
                    print('BODMAS****************************************************************************')
                    print('dings: ', list(map(lambda d: (d['name'], d['startPos'], d['endPos']), newDings)))
                try: # BODMAS
                    priority = self.PRIOIRITIZED_INFIX.index(ding['name']) # the smaller the number the higher the priority. Non-infix has the highest prioirity of -1
                    #if priority != -1: # one way to check if ding is an infix
                    if ding['type'] == 'infix': # which way is better?
                        if ding['tight__leftType'] == 'enclosing': #equivalently, ding['right__type'] == 'enclosing' ??
                            priority = -3 # smaller number higher priority
                        if ding['tight__leftType'] == 'leftRight':
                            priority = -2 # smaller number higher priority
                    processed.add(dingPos) # this is an infix
                except:
                    # dingPosToPriorities[dingPos] = -1
                    continue # we are only working on infix here. so ignore everything else

                existingDingsPos = prioritiesToDingsPos.get(priority, [])
                existingDingsPos.append(dingPos)
                prioritiesToDingsPos[priority] = existingDingsPos
                # dingPosToPriorities[dingPos] = priority
            prioritiesDingsPosItemList = sorted(prioritiesToDingsPos.items(), key=lambda item: item[0])

            if self.showError():
                import pprint
                pp = pprint.PrettyPrinter(indent=4)
                print('build subtrees by INFIX PRIORITY')
                print('infixBy Priorities*********************************START')
                priorityToItem = {}
                for priority, dingPoss in prioritiesDingsPosItemList: # for level -1, we should keep the child as is....
                    tits = []
                    for dingPos in dingPoss:
                        ding = newDings[dingPos]
                        tits.append((ding['name'], ding['startPos'], ding['endPos'], ding['left__type'], ding['right__type'], ding['tight__leftType'], ding['tight__rightType']))
                    priorityToItem[priority] = tits
                pp.pprint(priorityToItem)
                print('infixBy Priorities*********************************END')

                # import pdb;pdb.set_trace()
            #should include all the prioritiesDingsPosItemList that are infixes
            for priority, dingPoss in prioritiesDingsPosItemList: # for level -1, we should keep the child as is....
                for dingPos in dingPoss:
                    ding = newDings[dingPos]
                    #find ding-to-the-right, thats not processed.
                    for idx in range(dingPos, len(newDings)): #newDings are all consecutive
                        if idx in processed:
                            continue
                        dingToRightIdx = idx
                        break
                    #find ding-to-the-left, thats not processed.
                    for idx in range(dingPos, -1, -1):
                        if idx in processed:
                            continue
                        dingToLeftIdx = idx
                        break


                    #############
                    # import pdb;pdb.set_trace()
                    #############



                    #ding is parent, dingToLeftIdx is left, dingToRightIdx is right
                    leftDing = newDings[dingToLeftIdx]
                    rightDing = newDings[dingToRightIdx]


                    if self.showError():
                        """
                        dingsPoss = [0]
                        there is exactly one idx
                        and there is nothing to the left of dingPos in newDings.
                        and there is nothing to the right of dingPos in newDings
                        """
                        print('******BEFORE SETTING PC relationship subtrees, leftDingPos:', dingToLeftIdx, ', dingPos', dingPos, ' dingToRightIdx, ', dingToRightIdx)
                        print('leftDing ************')
                        print((leftDing['name'], leftDing['startPos'], leftDing['endPos']), '|', )
                        if 'parent' in leftDing and leftDing['parent'] is not None:
                            print('parent:', (leftDing['parent']['name'], leftDing['parent']['startPos'], leftDing['parent']['endPos']))
                        else:
                            print('leftDing no parent')
                        if 'child' in leftDing and leftDing['child'][1] is not None:
                            print('child1:', (leftDing['child'][1]['name'], leftDing['child'][1]['startPos'], leftDing['child'][1]['endPos']))
                        else:
                            print('leftDing no child1')
                        if 'child' in leftDing and 2 in leftDing['child'] and leftDing['child'][2] is not None:
                            print('child2:', (leftDing['child'][2]['name'], leftDing['child'][2]['startPos'], leftDing['child'][2]['endPos']))
                        else:
                            print('leftDing no child2')
                        print('ding *****************')
                        print((ding['name'], ding['startPos'], ding['endPos']), '|', )
                        if 'parent' in ding and ding['parent'] is not None:
                            print('parent:', (ding['parent']['name'], ding['parent']['startPos'], ding['parent']['endPos']))
                        else:
                            print('ding no parent')
                        if 'child' in ding and ding['child'][1] is not None:
                            print('child1:', (ding['child'][1]['name'], ding['child'][1]['startPos'], ding['child'][1]['endPos']))
                        else:
                            print('ding no child1')
                        if 'child' in ding and 2 in ding['child'] and  ding['child'][2] is not None:
                            print('child2:', (ding['child'][2]['name'], ding['child'][2]['startPos'], ding['child'][2]['endPos']))
                        else:
                            print('ding no child2')
                        print('rightDing ***********')
                        print((rightDing['name'], rightDing['startPos'], rightDing['endPos']), '|', )
                        if 'parent' in rightDing and rightDing['parent'] is not None:
                            print('parent:', (rightDing['parent']['name'], rightDing['parent']['startPos'], rightDing['parent']['endPos']))
                        else:
                            print('rightDing no parent')
                        if 'child' in rightDing and rightDing['child'][1] is not None:
                            print('child1:', (rightDing['child'][1]['name'], rightDing['child'][1]['startPos'], rightDing['child'][1]['endPos']))
                        else:
                            print('rightDing no child1')
                        if 'child' in rightDing and 2 in rightDing['child'] and  rightDing['child'][2] is not None:
                            print('child2:', (rightDing['child'][2]['name'], rightDing['child'][2]['startPos'], rightDing['child'][2]['endPos']))
                        else:
                            print('rightDing no child2')
                        print('**********************')
                        # import pdb;pdb.set_trace()


                    leftChild = {
                        'name':leftDing['name'],
                        'startPos':leftDing['startPos'],
                        'endPos':leftDing['endPos'],
                        'type':leftDing['type'],
                        'ganzStartPos':leftDing['ganzStartPos'],
                        'ganzEndPos':leftDing['ganzEndPos']
                    }
                    rightChild = {
                        'name':rightDing['name'],
                        'startPos':rightDing['startPos'],
                        'endPos':rightDing['endPos'],
                        'type':rightDing['type'],
                        'ganzStartPos':rightDing['ganzStartPos'],
                        'ganzEndPos':rightDing['ganzEndPos']
                    }
                    ding['child'][1] = leftChild
                    ding['child'][2] = rightChild
                    leftDing['parent'] = {
                        'name':ding['name'],
                        'startPos':ding['startPos'],
                        'endPos':ding['endPos'],
                        'type':ding['type'],
                        'childIdx':1,
                        'ganzStartPos':ding['ganzStartPos'],
                        'ganzEndPos':ding['ganzEndPos']
                    }
                    rightDing['parent'] = {
                        'name':ding['name'],
                        'startPos':ding['startPos'],
                        'endPos':ding['endPos'],
                        'type':ding['type'],
                        'childIdx':2,
                        'ganzStartPos':ding['ganzStartPos'],
                        'ganzEndPos':ding['ganzEndPos']
                    }


                    if self.showError():
                        """
                        dingsPoss = [0]
                        there is exactly one idx
                        and there is nothing to the left of dingPos in newDings.
                        and there is nothing to the right of dingPos in newDings
                        """
                        print('******building subtrees END for, leftDingPos:', dingToLeftIdx, ', dingPos', dingPos, ' dingToRightIdx, ', dingToRightIdx)
                        print('leftDing ************')
                        print((leftDing['name'], leftDing['startPos'], leftDing['endPos']), '|', )
                        if 'parent' in leftDing and leftDing['parent'] is not None:
                            print('parent:', (leftDing['parent']['name'], leftDing['parent']['startPos'], leftDing['parent']['endPos']))
                        else:
                            print('leftDing no parent')
                        if 'child' in leftDing and leftDing['child'][1] is not None:
                            print('child1:', (leftDing['child'][1]['name'], leftDing['child'][1]['startPos'], leftDing['child'][1]['endPos']))
                        else:
                            print('leftDing no child1')
                        if 'child' in leftDing and 2 in leftDing['child'] and leftDing['child'][2] is not None:
                            print('child2:', (leftDing['child'][2]['name'], leftDing['child'][2]['startPos'], leftDing['child'][2]['endPos']))
                        else:
                            print('leftDing no child2')
                        print('ding *****************')
                        print((ding['name'], ding['startPos'], ding['endPos']), '|', )
                        if 'parent' in ding and ding['parent'] is not None:
                            print('parent:', (ding['parent']['name'], ding['parent']['startPos'], ding['parent']['endPos']))
                        else:
                            print('ding no parent')
                        if 'child' in ding and ding['child'][1] is not None:
                            print('child1:', (ding['child'][1]['name'], ding['child'][1]['startPos'], ding['child'][1]['endPos']))
                        else:
                            print('ding no child1')
                        if 'child' in ding and 2 in ding['child'] and  ding['child'][2] is not None:
                            print('child2:', (ding['child'][2]['name'], ding['child'][2]['startPos'], ding['child'][2]['endPos']))
                        else:
                            print('ding no child2')
                        print('rightDing ***********')
                        print((rightDing['name'], rightDing['startPos'], rightDing['endPos']), '|', )
                        if 'parent' in rightDing and rightDing['parent'] is not None:
                            print('parent:', (rightDing['parent']['name'], rightDing['parent']['startPos'], rightDing['parent']['endPos']))
                        else:
                            print('rightDing no parent')
                        if 'child' in rightDing and rightDing['child'][1] is not None:
                            print('child1:', (rightDing['child'][1]['name'], rightDing['child'][1]['startPos'], rightDing['child'][1]['endPos']))
                        else:
                            print('rightDing no child1')
                        if 'child' in rightDing and 2 in rightDing['child'] and  rightDing['child'][2] is not None:
                            print('child2:', (rightDing['child'][2]['name'], rightDing['child'][2]['startPos'], rightDing['child'][2]['endPos']))
                        else:
                            print('rightDing no child2')
                        print('**********************')
                        # import pdb;pdb.set_trace()

                    #TODO set parents, so that we can figure out equals children later.....
                    processed.remove(dingPos) # the infix needs to be available again, to be a child
                    processed.add(dingToLeftIdx) # args used may not be reused again
                    processed.add(dingToRightIdx) # args used may not be reused again
        #the last ding from the last-for-loop is the root of dings
        # self.rootsAndGanzeWidth.append({'root':ding, 'ganzStartPos':treeifiedDingsGanzStartPos, 'ganzEndPos':treeifiedDingsGanzEndPos})
        #clear the treeifiedDingsGanzStartPos, treeifiedDingsGanzEndPos
        # treeifiedDingsGanzStartPos = len(self._eqs) + 1 # we only have 1 dings, do not need to clear tdgsp tdgep
        # treeifiedDingsGanzEndPos = -1
        # self.newConsecutiveGroups[grenzeRange] = newDings
        ############
        if self.showError():
            print('checking treeifiedDingsGanzStartPos/treeifiedDingsGanzEndPos')
            print('dings', list(map(lambda d: (d['name'], d['startPos'], d['endPos']), newDings)))
            print('ding', ((ding['name'], ding['startPos'], ding['endPos'])))
            print('treeifiedDingsGanzStartPos', treeifiedDingsGanzStartPos)
            print('treeifiedDingsGanzEndPos', treeifiedDingsGanzEndPos)
            print('we are returning (as root of subtree):')
            print({'root':ding, 'ganzStartPos':treeifiedDingsGanzStartPos, 'ganzEndPos':treeifiedDingsGanzEndPos})
            print('parent/child relationships:')

            print('*********parentChildR Status after __intraGrenzeSubtreeUe(2ndpart intralevel parentChildR building)********************************')
            sadchild = {}
            for d in newDings:
                idd = (d['name'], d['startPos'], d['endPos'])
                c0 = None if 'child' not in d or d['child'][1] is None else (d['child'][1]['name'], d['child'][1]['startPos'], d['child'][1]['endPos'])
                c1 = None if 'child' not in d or 2 not in d['child'] or d['child'][2] is None else (d['child'][2]['name'], d['child'][2]['startPos'], d['child'][2]['endPos'])
                pard = None if d['parent'] is None else (d['parent']['name'], d['parent']['startPos'], d['parent']['endPos'])
                sadchild[idd] = {'c1':c0, 'c2':c1, 'parent':pard}
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(sadchild)
            print('*********parentChildR Status after __intraGrenzeSubtreeUe(2ndpart intralevel parentChildR building)********************************')
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!AT THE END!!!!!!!!!!!!!!!!!!!!!!!!!')
            # import pdb;pdb.set_trace()
        ############
        return {'root':ding, 'ganzStartPos':treeifiedDingsGanzStartPos, 'ganzEndPos':treeifiedDingsGanzEndPos}


    def __interLevelSubtreeGrafting(self, rootSubTree, parentDings):
        """
        each key in newConsecutiveGroups is a level,
        and during the 2nd part of _addImplicitMultiply
        we build parent-child-relationship within each level

        Here, we build parent-child-relationship across levels.
        So, after this step, we should only have 2-subtrees with no parents
        Those 2 are the direct children of '='
        """
        containedArgument = False#have we already found the parent for rootSubTree
        for ding in parentDings: # ding is with socket (empty child)

            if self.showError():
                print('*********parentChildR Status after __interLevelSubtreeGrafting(2ndpart intralevel parentChildR building)********************************')
                sadchild = {}
                for d in parentDings:
                    idd = (d['name'], d['startPos'], d['endPos'])
                    c0 = None if 'child' not in d or d['child'][1] is None else (d['child'][1]['name'], d['child'][1]['startPos'], d['child'][1]['endPos'])
                    c1 = None if 'child' not in d or d['child'][2] is None else (d['child'][2]['name'], d['child'][2]['startPos'], d['child'][2]['endPos'])
                    pard = None if d['parent'] is None else (d['parent']['name'], d['parent']['startPos'], d['parent']['endPos'])
                    sadchild[idd] = {'c1':c0, 'c2':c1, 'parent':pard}
                import pprint
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(sadchild)
                print('*********parentChildR Status after __interLevelSubtreeGrafting(2ndpart intralevel parentChildR building)********************************')
            if containedArgument: # we have found the parent for rootSubTree

                return parentDings
            #####################################PARENT FINDING ROUTINE  ::: START <<<<<<<<<<<<<<<TODO refactor, damn confusing
            if (ding['type'] == 'backslash_function' and (ding['child'][1] is None or ding['child'][2] is None)) or \
            (ding['type'] == 'backslash_variable' and ding['child'][1] is None): #only come here if there is some None child
                #find the root of dings
                if ding['type'] == 'backslash_function':
                    if ding['child'][1] is None and ding['child'][2] is None:
                        if self.showError():
                            print('dingSocketBF using check for both children 1&2')
                        def rootIsContained(tGSPos, tGEPos):#need to include bracketType since tGSPos include brackets
                            if ding['argument1StartPosition'] - lenOrZero(ding['argument1BracketType']) <= tGSPos and  tGEPos <= ding['argument1EndPosition'] + lenOrZero(ding['argument1BracketType']):
                                return 1
                            if ding['argument2StartPosition'] - lenOrZero(ding['argument2BracketType']) <= tGSPos and tGEPos <= ding['argument2EndPosition'] + lenOrZero(ding['argument2BracketType']):
                                return 2
                            return False
                    elif ding['child'][1] is None:
                        if self.showError():
                            print('dingSocketBF using check for child 1 ONLY')
                        def rootIsContained(tGSPos, tGEPos):
                            # import pdb;pdb.set_trace()
                            if ding['argument1StartPosition'] - lenOrZero(ding['argument1BracketType']) <= tGSPos and  tGEPos <= ding['argument1EndPosition'] + lenOrZero(ding['argument1BracketType']):
                                return 1
                            return False
                    elif ding['child'][2] is None:
                        if self.showError():
                            print('dingSocketBF using check for child 2 ONLY')
                        def rootIsContained(tGSPos, tGEPos):
                            if ding['argument2StartPosition'] - lenOrZero(ding['argument2BracketType']) <= tGSPos and tGEPos <= ding['argument2EndPosition'] + lenOrZero(ding['argument2BracketType']):
                                return 2
                            return False
                elif ding['type'] == 'backslash_variable':
                    if ding['child'][1] is None:
                        if self.showError():
                            print('dingSocketBV using check for child 1 ONLY')
                        def rootIsContained(tGSPos, tGEPos):
                            if ding['argument1StartPosition'] - lenOrZero(ding['argument1BracketType']) <= tGSPos and  tGEPos <= ding['argument1EndPosition'] + lenOrZero(ding['argument1BracketType']):
                                return 1
                            return False
                #we need to find the widest ganzeWidth, but still contained
                theRoot1 = None
                theGanzStartPos1 = len(self._eqs) + 1#largest num
                theGanzEndPos1 = -1#smallest num
                theRoot2 = None
                theGanzStartPos2 = len(self._eqs) + 1#largest num
                theGanzEndPos2 = -1#smallest num
                #no need to find rootInfoDict, since rootInfoDict=rootSubTree
                # for rootInfoDict in self.rootsAndGanzeWidth:#rootInfoDict(with the pin)

                containedArgument = rootIsContained(rootSubTree['ganzStartPos'], rootSubTree['ganzEndPos'])
                ##############
                if self.showError():
                    print('finding a parent for rootSubTree, also find if rootSubTree is child1 or child2+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                    print('parent rangeArg1: ', ding['argument1StartPosition'], ' , ', ding['argument1EndPosition'], ' |rangeArg2: ', ding['argument2StartPosition'], ' , ', ding['argument2EndPosition'], '<<<<<<<<<<<<<SOCKETS')
                    print('child: ', rootSubTree['ganzStartPos'], rootSubTree['ganzEndPos'],'<<<<<<<<<<<<<<<<<<<<<<<<<<<<<PRICK')
                    print('is ding: ', (ding['name'], ding['startPos'], ding['endPos']), ' parent of rootSubTree?: ', (rootSubTree['ganzStartPos'], rootSubTree['ganzEndPos'], (rootSubTree['root']['name'], rootSubTree['root']['startPos'], rootSubTree['root']['endPos'])), containedArgument != False)
                ##############
                ####
                if self.showError():
                    print('checking ding(socket)', ding['name'], ' contains  ', (rootSubTree['root']['name'], rootSubTree['ganzStartPos'], rootSubTree['ganzEndPos']), 'containment Argument: ', containedArgument)
                    # import pdb;pdb.set_trace()
                ####
                if containedArgument:
                    ####
                    if self.showError():
                        print('ding', ding['name'], ' contains  rootSubTree of self.rootsAndGanzeWidth ', rootSubTree['root']['name'], ' containedment child:', containedArgument)
                        # import pdb;pdb.set_trace()
                    ####
                    if containedArgument == 1 and ( rootSubTree['ganzStartPos'] <= theGanzStartPos1 and theGanzEndPos1 <= rootSubTree['ganzEndPos'] ): # and wider than recorded
                        theRoot1 = rootSubTree['root']
                        theGanzStartPos1 = rootSubTree['ganzStartPos']
                        theGanzEndPos1 = rootSubTree['ganzEndPos']
                    if containedArgument == 2 and ( rootSubTree['ganzStartPos'] <= theGanzStartPos2 and theGanzEndPos2 <= rootSubTree['ganzEndPos'] ): # and wider than recorded
                        #+ and sqrt should have popped up here...
                        theRoot2 = rootSubTree['root']
                        theGanzStartPos2 = rootSubTree['ganzStartPos']
                        theGanzEndPos2 = rootSubTree['ganzEndPos']
                #There are trigo function with no power(arg1), if there is nothing fitting here for trigo function in arg1, then we take from argument1
                #Put the child into the right place
                ################
                if self.showError():
                    print('**************************check what theRoot1 or theRoot2 we found... parent of rootSubTree:')
                    if containedArgument == 1:
                        print('we found rootSubTree', (rootSubTree['ganzStartPos'], rootSubTree['ganzEndPos'], (rootSubTree['root']['name'], rootSubTree['root']['startPos'], rootSubTree['root']['endPos'])),' as child1 of parent: ', (ding['name'], ding['startPos'], ding['endPos']))
                        print('parent Details:')
                        print('theRoot1', theRoot1)
                        print('theGanzStartPos1', theGanzStartPos1)
                        print('theGanzEndPos1', theGanzEndPos1)
                    if containedArgument == 2:
                        print('we found rootSubTree', (rootSubTree['ganzStartPos'], rootSubTree['ganzEndPos'], (rootSubTree['root']['name'], rootSubTree['root']['startPos'], rootSubTree['root']['endPos'])),'as child2 of parent: ', (ding['name'], ding['startPos'], ding['endPos']))
                        print('parent Details:')
                        print('theRoot2', theRoot2)
                        print('theGanzStartPos2', theGanzStartPos2)
                        print('theGanzEndPos2', theGanzEndPos2)
                    if containedArgument is False:
                        print('we found rootSubTree', (rootSubTree['ganzStartPos'], rootSubTree['ganzEndPos'], (rootSubTree['root']['name'], rootSubTree['root']['startPos'], rootSubTree['root']['endPos'])),' have no parent... SOSOSOSOSO')
                    # import pdb;pdb.set_trace()
                ################
                if ding['type'] == 'backslash_variable':
                    if self.showError():
                        print("checking for tightest, ding['child'][1] is None=", ding['child'][1] is None)
                        if ding['child'][1] is not None:
                            print("theRoot1 is wider than ding['child'][1]: ", theRoot1['ganzStartPos'] <= ding['child'][1]['ganzStartPos'] and ding['child'][1]['ganzEndPos'] <= theRoot1['ganzEndPos'])
                    #check if current child/parent relationship is the tightest, noChild, or theRoot1 is tighter than ding['child'][1]
                    if ding['child'][1] is None or (theRoot1['ganzStartPos'] <= ding['child'][1]['ganzStartPos'] and ding['child'][1]['ganzEndPos'] <= theRoot1['ganzEndPos']):
                        ding['child'][1] = {
                            'name':theRoot1['name'],
                            'startPos':theRoot1['startPos'],
                            'endPos':theRoot1['endPos'],
                            'type':theRoot1['type'],
                            'ganzStartPos':theRoot1['ganzStartPos'],#theRoot1['startPos'],
                            'ganzEndPos':theRoot1['ganzEndPos']#theRoot1['endPos']
                        }
                        theRoot1['parent'] = {
                            'name':ding['name'],
                            'startPos':ding['startPos'],
                            'endPos':ding['endPos'],
                            'type':ding['type'],
                            'childIdx':1,
                            'ganzStartPos':ding['ganzStartPos'],
                            'ganzEndPos':ding['ganzEndPos']
                        }
                        if self.showError():
                            print('updating backslash_variable ding', (ding['name'], ding['startPos'], ding['endPos']), ' child1 = ', (theRoot1['name'], theRoot1['startPos'], theRoot1['endPos']), '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                # if ding['type'] == 'backslash_function' and ding['child'][1] is None and ding['argument1StartPosition'] <= theGanzStartPos1 and  theGanzEndPos1 <= ding['argument1EndPosition']:
                elif ding['type'] == 'backslash_function':
                    if theRoot1:
                        if self.showError():
                            print("checking for tightest, ding['child'][1] is None=", ding['child'][1] is None)
                            if ding['child'][1] is not None:
                                print("theRoot1 is wider than ding['child'][1]: ", theRoot1['ganzStartPos'] <= ding['child'][1]['ganzStartPos'] and ding['child'][1]['ganzEndPos'] <= theRoot1['ganzEndPos'])
                        #check if current child/parent relationship is the tightest, noChild, or theRoot1 is tighter than ding['child'][1]
                        if ding['child'][1] is None or (theRoot1['ganzStartPos'] <= ding['child'][1]['ganzStartPos'] and ding['child'][1]['ganzEndPos'] <= theRoot1['ganzEndPos']):
                            #TODO check if current child/parent relationship is the tightest
                            ding['child'][1] = {
                                'name':theRoot1['name'],
                                'startPos':theRoot1['startPos'],
                                'endPos':theRoot1['endPos'],
                                'type':theRoot1['type'],
                                'ganzStartPos':theRoot1['ganzStartPos'],
                                'ganzEndPos':theRoot1['ganzEndPos']
                            }
                            theRoot1['parent'] = {
                                'name':ding['name'],
                                'startPos':ding['startPos'],
                                'endPos':ding['endPos'],
                                'type':ding['type'],
                                'childIdx':1,
                                'ganzStartPos':ding['ganzStartPos'],
                                'ganzEndPos':ding['ganzEndPos']
                            }
                            if self.showError():
                                print('updating backslash_function ding', (ding['name'], ding['startPos'], ding['endPos']), ' child1 = ', (theRoot1['name'], theRoot1['startPos'], theRoot1['endPos']), '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

                    if theRoot2:
                        if self.showError():
                            print("checking for tightest, ding['child'][2] is None=", ding['child'][2] is None)
                            if ding['child'][2] is not None:
                                print("theRoot2 is wider than ding['child'][2]: ", theRoot2['ganzStartPos'] <= ding['child'][2]['ganzStartPos'] and ding['child'][2]['ganzEndPos'] <= theRoot2['ganzEndPos'])
                        #check if current child/parent relationship is the tightest, noChild, or theRoot2 is tighter than ding['child'][2]
                        if ding['child'][2] is None or (theRoot2['ganzStartPos'] <= ding['child'][2]['ganzStartPos'] and ding['child'][2]['ganzEndPos'] <= theRoot2['ganzEndPos']):
                            ding['child'][2] = {
                                'name':theRoot2['name'],
                                'startPos':theRoot2['startPos'],
                                'endPos':theRoot2['endPos'],
                                'type':theRoot2['type'],
                                'ganzStartPos':theRoot2['ganzStartPos'],
                                'ganzEndPos':theRoot2['ganzEndPos']
                            }
                            theRoot2['parent'] = {
                                'name':ding['name'],
                                'startPos':ding['startPos'],
                                'endPos':ding['endPos'],
                                'type':ding['type'],
                                'childIdx':2,
                                'ganzStartPos':ding['ganzStartPos'],
                                'ganzEndPos':ding['ganzEndPos']
                            }
                            if self.showError():
                                print('updating backslash_function ding', (ding['name'], ding['startPos'], ding['endPos']), ' child1 = ', (theRoot2['name'], theRoot2['startPos'], theRoot2['endPos']), '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                    #we have to do this no matter if children of trig is None or not. but, after we got children of trig (if trig was None in the first place)
                    if self.showError():
                        print('checked ding: ', (ding['name'], ding['startPos'], ding['endPos']), 'parentchildrBuildAcrossLevel***************************')
                        if theRoot1: # ding has theRoot1 as child1
                            print('ding child1 is: ', (theRoot1['name'], theRoot1['startPos'], theRoot1['endPos']))
                        elif theRoot2: # ding has theRoot2 as child2
                            print('ding child2 is: ', (theRoot2['name'], theRoot2['startPos'], theRoot2['endPos']))
                        else:
                            print('ding has no child!!!!!!!!')
                        print('parentchildrBuildAcrossLevel**************************************************************************************')
                    # import pdb;pdb.set_trace()
            #####################################PARENT FINDING ROUTINE  ::: END
        return parentDings


    def _reformatToAST(self):
        if self.parallelise:
            self.event__subTreeGraftingUntilTwoTrees.wait()
        #add the = (with children) in alleDing, YAY!
        #first find ding with no parent
        dingsNoParents = []
        for ding in self.alleDing:
            if ding['parent'] is None: # 'parent' not in ding (this is not acceptable, if this happens, fix the code apriori)
                dingsNoParents.append(ding)
        if len(dingsNoParents) != 2:
            print('BAD number of parents: ', len(dingsNoParents))
            print('parent/child relationship:')
            sadchild = {}
            for d in self.alleDing:
                idd = (d['name'], d['startPos'], d['endPos'])
                c0 = None if 'child' not in d or d['child'][1] is None else (d['child'][1]['name'], d['child'][1]['startPos'], d['child'][1]['endPos'])
                c1 = None if 'child' not in d or d['child'][2] is None else (d['child'][2]['name'], d['child'][2]['startPos'], d['child'][2]['endPos'])
                pard = None if d['parent'] is None else (d['parent']['name'], d['parent']['startPos'], d['parent']['endPos'])
                sadchild[idd] = {'c1':c0, 'c2':c1, 'parent':pard}
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(sadchild)
            print("dingsNoParents:")
            print(list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dingsNoParents)))
            import pdb;pdb.set_trace()
            raise Exception('Equals only have 2 sides')
        #build the AST here...
        nameStartEndToNodeId = {}
        self.nodeId = 1
        for s in self.alleDing:
            nameStartEndToNodeId[(s['name'], s['startPos'], s['endPos'])] = self.nodeId
            self.nodeId += 1
        self.latexAST = {}
        child0Id = nameStartEndToNodeId[(dingsNoParents[0]['name'], dingsNoParents[0]['startPos'], dingsNoParents[0]['endPos'])]
        child1Id = nameStartEndToNodeId[(dingsNoParents[1]['name'], dingsNoParents[1]['startPos'], dingsNoParents[1]['endPos'])]
        # import pdb;pdb.set_trace()
        self.equalTuple = ('=', 0)
        if dingsNoParents[0]['position'] < dingsNoParents[1]['position']:
            self.latexAST[self.equalTuple] = [(dingsNoParents[0]['name'], child0Id), (dingsNoParents[1]['name'], child1Id)]
        else:
            self.latexAST[self.equalTuple] = [(dingsNoParents[1]['name'], child1Id), (dingsNoParents[0]['name'], child0Id)]

        self.nodeIdToInfixArgsBrackets = {} # this is for unparse function, bracket information
        #############
        if self.showError():
            print('parent/child relationship:')
            sadchild = {}
            for d in self.alleDing:
                idd = (d['name'], d['startPos'], d['endPos'])
                c0 = None if 'child' not in d or d['child'][1] is None else (d['child'][1]['name'], d['child'][1]['startPos'], d['child'][1]['endPos'])
                c1 = None if 'child' not in d or d['child'][2] is None else (d['child'][2]['name'], d['child'][2]['startPos'], d['child'][2]['endPos'])
                pard = None if d['parent'] is None else (d['parent']['name'], d['parent']['startPos'], d['parent']['endPos'])
                sadchild[idd] = {'c1':c0, 'c2':c1, 'parent':pard}
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(sadchild)
            print("dingsNoParents:")
            print(list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dingsNoParents)))

        #############
        for parent in self.alleDing:
            parentId = nameStartEndToNodeId[(parent['name'], parent['startPos'], parent['endPos'])]
            ############ for unparse function
            if parent['type'] == 'infix':
                leftOpenBracket = ''
                leftCloseBracket = ''
                rightOpenBracket = ''
                rightCloseBracket = ''
                # import pdb;pdb.set_trace()
                if 'left__type' in parent and parent['left__type'] != 'infix' and parent['left__type'] != 'arg':
                    if parent['left__startBracketType'] is not None:
                        leftOpenBracket = parent['left__startBracketType']
                    if parent['left__endBracketType'] is not None:
                        leftCloseBracket = parent['left__endBracketType']
                if 'right__type'in parent and parent['right__type'] != 'infix' and parent['right__type'] != 'arg':
                    if parent['right__startBracketType'] is not None:
                        rightOpenBracket = parent['right__startBracketType']
                    if parent['right__endBracketType'] is not None:
                        rightCloseBracket = parent['right__endBracketType']
                self.nodeIdToInfixArgsBrackets[parentId] = {
                    'leftOpenBracket':leftOpenBracket,
                    'leftCloseBracket':leftCloseBracket,
                    'rightOpenBracket':rightOpenBracket,
                    'rightCloseBracket':rightCloseBracket,
                }
            ############
            if 'child' in parent:
                if len(parent['child']) == 1:
                    childKey = nameStartEndToNodeId[(parent['child'][1]['name'], parent['child'][1]['startPos'], parent['child'][1]['endPos'])]
                    self.latexAST[(parent['name'], parentId)] = [(parent['child'][1]['name'], childKey)]
                elif len(parent['child']) == 2: #current this is the only other possibility
                    if parent['child'][1] is not None:
                        child1Name = parent['child'][1]['name']
                        child1Key = nameStartEndToNodeId[(child1Name, parent['child'][1]['startPos'], parent['child'][1]['endPos'])]
                        self.latexAST[(parent['name'], parentId)] = [(child1Name, child1Key)]

                    if parent['child'][2] is not None:
                        child2Name = parent['child'][2]['name']
                        child2Key = nameStartEndToNodeId[(child2Name, parent['child'][2]['startPos'], parent['child'][2]['endPos'])]
                        existingChildren = self.latexAST.get((parent['name'], parentId), [])
                        existingChildren.append((child2Name, child2Key))
                        self.latexAST[(parent['name'], parentId)] = existingChildren
        if self.parallelise:
            self.event__reformatToAST.set()


    def _latexSpecialCases(self):
        import copy
        latexASTCopy = copy.deepcopy(self.latexAST)
        self.ast = {}
        stack = [self.equalTuple]
        while len(stack) > 0:
            currentNode = stack.pop()
            nodeName = currentNode[0]
            nodeId = currentNode[1]
            if nodeName == 'sqrt': # change to nroot
                nodeName = 'nroot'
                newNode = (nodeName, nodeId)
                children = latexASTCopy[currentNode]
                if len(children) == 1: # is root 2, and we only have the rootant
                    children.insert(0, (2, self.nodeId))
                    self.nodeId += 1
                self.ast[newNode] = children
                #replace parent's child too
                parentNode = None
                parentChildIndex = None
                for parent, children in latexASTCopy.items():
                    for childIdx, child in enumerate(children):
                        if child == currentNode:
                            parentNode = parent
                            parentChildIndex = childIdx
                            break
                    if parentNode is not None:
                        break
                if parentNode is not None and parentChildIndex is not None:
                    children[parentChildIndex] = newNode
                    latexASTCopy[parentNode] = children
                #
                stack += latexASTCopy[currentNode]
            elif nodeName == 'ln':
                nodeName = 'log'
                newNode = (nodeName, nodeId)
                children = latexASTCopy[currentNode]
                children.insert(0, ('e', self.nodeId))
                self.nodeId += 1
                self.ast[newNode] = children
                #replace parent's child too
                parentNode = None
                parentChildIndex = None
                for parent, children in latexASTCopy.items():
                    for childIdx, child in enumerate(children):
                        if child == currentNode:
                            parentNode = parent
                            parentChildIndex = childIdx
                            break
                    if parentNode is not None:
                        break
                if parentNode is not None and parentChildIndex is not None:
                    children[parentChildIndex] = newNode
                    latexASTCopy[parentNode] = children
                #
                stack += latexASTCopy[currentNode]
            elif nodeName == 'log' and len(latexASTCopy[currentNode]) == 1: # add the default 10 as argument 1
                children = latexASTCopy[currentNode]
                children = latexASTCopy[currentNode]
                children.insert(0, (10, self.nodeId))
                self.nodeId += 1
                self.ast[currentNode] = children
                stack += latexASTCopy[currentNode]
            elif nodeName == 'frac':
                nodeName = '/'
                newNode = (nodeName, nodeId)
                #replace parent's child too
                parentNode = None
                parentChildIndex = None
                for parent, children in latexASTCopy.items():
                    for childIdx, child in enumerate(children):
                        if child == currentNode:
                            parentNode = parent
                            parentChildIndex = childIdx
                            break
                    if parentNode is not None:
                        break
                if parentNode is not None and parentChildIndex is not None:
                    children[parentChildIndex] = newNode
                    latexASTCopy[parentNode] = children
                #
                self.ast[(nodeName, nodeId)] = latexASTCopy[currentNode]
                stack += latexASTCopy[currentNode]
            elif nodeName in self.TRIGOFUNCTION and len(latexASTCopy[currentNode]) == 2: # trig with power
                powerNode, argNode = latexASTCopy[currentNode]
                exponentialNode = ('^', self.nodeId)
                #SOorrry currentNodee! you got replaceed with exponentialNode!
                parentNode = None
                parentChildIndex = None
                for parent, children in latexASTCopy.items():
                    for childIdx, child in enumerate(children):
                        if child == currentNode:
                            parentNode = parent
                            parentChildIndex = childIdx
                            break
                    if parentNode is not None:
                        break
                if parentNode is not None and parentChildIndex is not None:
                    children = latexASTCopy[parentNode]
                    children[parentChildIndex] = exponentialNode
                #finis replacement de currentNode avec exponentialNode
                self.nodeId += 1
                self.ast[exponentialNode] = [(currentNode, powerNode)]
                self.ast[currentNode] = [argNode]
                stack += latexASTCopy[currentNode]
            elif currentNode in latexASTCopy: # latexAST do not contain leaves
                self.ast[currentNode] = latexASTCopy[currentNode]
                stack += latexASTCopy[currentNode]
        

    def _parse(self):
        """
        1. Find backslash and their argEnclosure, ganzEnclosure
        2. Find infix and their argEnclosure, ganzEnclosure, ignore '='
        3. Find leftovers, Collate leftovers into variables/numbers
        4. Add implicit-0 for (multiplicative-minus)
        5. Collate backslash, infix, variables/numbers into contiguous (bubble merging)
        6. Add implicit-multiply for (things like: 2x), should be actually 2*x
        7. Combine subtrees by argEnclosure, handle sqrt, trigpower specialcases
        8. Find 2 with subtreenoparent, attach them to =
        9. Run through all backslash/infix to form AST...


        
        VARIABLE DEPENDENCIES... 
        $$$$
        -> export
        <- import
        <> import&export(but modified.)
        $$$$
event__findBackSlashPositions
->self.variablesPos
->self.functionPos
->self.noBraBackslashPos

event__findInfixAndEnclosingBrackets
->self.matchingBracketsLocation
->self.infixList

event__updateInfixNearestBracketInfix
<-self.variablesPos
<-self.functionPos
<-self.matchingBracketsLocation
<>self.infixList
->self.allowedInfix
->self.listOfInfixInfoDict

event__removeCaretThatIsNotExponent
<-self.functionPos
<-self.allowedInfix
<>self.infixList

event__findLeftOverPosition
<-self.noBraBackslashPos
<-self.variablesPos
<-self.functionPos
<-self.infixList
->self.unoccupiedPoss

event__contiguousLeftOvers
<-self.unoccupiedPoss
->self.contiguousInfoList

event__addImplicitZero
<-self.infixList
->self.contiguousInfoList

event__collateBackslashInfixLeftOversToContiguous
<-self.contiguousInfoList
<-self.noBraBackslashPos
<-self.variablesPos
<-self.functionPos
<-self.infixList
->self.consecutiveGroups

event__addImplicitMultipy
<-self.consecutiveGroups
->self.newConsecutiveGroups
->self.infixList

event__subTreeGraftingUntilTwoTrees
<-self.newConsecutiveGroups
->self.alleDing

event__reformatToAST
<-self.alleDing
->self.ast




$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$incomplete code to check variable_dependency_between_methods (da ich schriebe 'cycle detection' nicht. )
dependenciesGraphStr = '''event__findBackSlashPositions
->self.variablesPos
->self.functionPos
->self.noBraBackslashPos

event__findInfixAndEnclosingBrackets
->self.matchingBracketsLocation
->self.infixList

event__updateInfixNearestBracketInfix
<-self.variablesPos
<-self.functionPos
<-self.matchingBracketsLocation
<>self.infixList
->self.allowedInfix
->self.listOfInfixInfoDict

event__removeCaretThatIsNotExponent
<-self.functionPos
<-self.allowedInfix
<>self.infixList

event__findLeftOverPosition
<-self.noBraBackslashPos
<-self.variablesPos
<-self.functionPos
<-self.infixList
->self.unoccupiedPoss

event__contiguousLeftOvers
<-self.unoccupiedPoss
->self.contiguousInfoList

event__addImplicitZero
<-self.infixList
->self.contiguousInfoList

event__collateBackslashInfixLeftOversToContiguous
<-self.contiguousInfoList
<-self.noBraBackslashPos
<-self.variablesPos
<-self.functionPos
<-self.infixList
->self.consecutiveGroups

event__addImplicitMultipy
<-self.consecutiveGroups
->self.newConsecutiveGroups
->self.infixList

event__subTreeGraftingUntilTwoTrees
<-self.newConsecutiveGroups
->self.alleDing

event__reformatToAST
<-self.alleDing
->self.ast'''

import os
resultGraphType = 'import' # could either be 'export' or 'import'
codify = True # if true, will change all the node name to numbers, then possibly easier to see


numberify = {}
numberId = 0
currentMethodNodeName = None
dependenciesGraph = {}
for line in dependenciesGraphStr.split('\n'):
    if len(line.strip()) == 0:
        continue
    print(line)
    #import pdb;pdb.set_trace()
    if line.startswith('event__'): #its a methodNode
        currentMethodNodeName = line # should remove the prefix event__
        numberify[currentMethodNodeName] = numberId
        numberId += 1
    elif line.startswith('->') or line.startswith('<>'):
        if currentMethodNodeName is None:
            raise Exception('Import currentMethodNodeName is None')
        exImDict = dependenciesGraph.get(currentMethodNodeName, {'export':[], 'import':[]})
        exImDict['export'].append(line[2:]) # take out -> or <>
        dependenciesGraph[currentMethodNodeName] = exImDict
    elif line.startswith('<-') or line.startswith('<>'):
        if currentMethodNodeName is None:
            raise Exception('Export currentMethodNodeName is None')
        exImDict = dependenciesGraph.get(currentMethodNodeName, {'export':[], 'import':[]})
        exImDict['import'].append(line[2:]) # take out <- or <>
        dependenciesGraph[currentMethodNodeName] = exImDict
    else:
        raise Exception('UnHandled')

newDependenciesGraph = {}
if codify:
    for nodeName, dings in dependenciesGraph.items():
        newDependenciesGraph[numberify[nodeName]] = dings
    dependenciesGraph = newDependenciesGraph

#find import/export Sources and put them in a queue
queue = []
for methodNodeName, exImDict in dependenciesGraph.items():
    if len(exImDict[resultGraphType]) == 0:
        queue.append(methodNodeName)


if resultGraphType == 'export':
    oppoType = 'import'
else:
    oppoType = 'export'



AST = {}
while len(queue) > 0: # there is dependency loop, need to detect cycles
    cNode = queue.pop()
    cEdges = dependenciesGraph[cNode][oppoType]
    ###look for children, they have edges on oppoType
    children = set()
    for aNode, exImDict in dependenciesGraph.items():
        if aNode == cNode:
            continue
        aEdges = exImDict[resultGraphType]
        #import pdb;pdb.set_trace()
        for aEdge in aEdges:
            if aEdge in cEdges:
                children.add(aNode)
    children = list(children)
    ###
    #import pdb;pdb.set_trace()
    AST[cNode] = children
    for child in children:
        queue.append(child)



import pprint
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(AST)

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$incomplete code to check variable_dependency_between_methods




        UNIMPLEMENTED:
        10. convert backslash variables to internal variables mapping
        11. convert backslash function name to standard function name IN automat.arithmetic.function.py
        """
        self._findInfixAndEnclosingBrackets()
        self._findBackSlashPositions()
        self._updateInfixNearestBracketInfix()
        self._removeCaretThatIsNotExponent()
        self._findLeftOverPosition()
        self._contiguousLeftOvers()
        self._collateBackslashInfixLeftOversToContiguous()
        self._graftGrenzeRangesIntoContainmentTree()
        self._reformatToAST()
        self._latexSpecialCases()
        #TODO Pool multiprocessing with method priorities (Chodai!) -- dependency ha chain desu yo, sou shitara, motto hayakunarimasu ka?





    def _unparse(self): # TODO from AST to LaTeX string... 
        """
        #~ DRAFT ~#
        TODO
        1. remove implicit 0-
        2. remove implicit-multiply
        """
        #find the implicit 0- in AST and remove (would subtree equivalence be easier?)
        #find the implicit-multiply in AST and remove
        return self._recursiveUnparse(self.equalTuple)


    def _recursiveUnparse(self, keyTuple):
        #~DRAFT~#
        name = keyTuple[0]
        #does not include backslash_variable although they are the real leaves. TODO have a consolidated AST, and a LatexAST...
        if name in self.leaves: # TODO, rename self.leaves to something ChildClass specific (confusing later)
            return name # return the namestr
        nid = keyTuple[1]
        arguments = self.ast[keyTuple]
        if name in self.backslashes:
            aux = self.backslashes[name]
            """
            aux = {
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
             # what about \sqrt, \log, \ln....
            if aux['hasArgument1'] and aux['hasArgument2']:
                return f"\\{name}{aux['argument1SubSuper']}{aux['argument1OpenBracket']}{self._recursiveUnparse(arguments[0])}{aux['argument1CloseBracket']}{aux['argument2SubSuper']}{aux['argument2OpenBracket']}{self._recursiveUnparse(arguments[1])}{aux['argument2CloseBracket']}"
            elif aux['hasArgument1']:
                return f"\\{name}{aux['argument1SubSuper']}{aux['argument1OpenBracket']}{self._recursiveUnparse(arguments[0])}{aux['argument1CloseBracket']}"
            elif aux['hasArgument2']:
                return f"\\{name}{aux['argument2SubSuper']}{aux['argument2OpenBracket']}{self._recursiveUnparse(arguments[1])}{aux['argument2CloseBracket']}"
            else:
                return f"\\{name}"

        if name in Latexparser.PRIOIRITIZED_INFIX:
            aux = self.nodeIdToInfixArgsBrackets[nid]
            """
            aux = {
                'leftOpenBracket':leftOpenBracket,
                'leftCloseBracket':leftCloseBracket,
                'rightOpenBracket':rightOpenBracket,
                'rightCloseBracket':rightCloseBracket,
            }
            """
            return f"\\{aux['leftOpenBracket']}{self._recursiveUnparse(arguments[0])}{aux['leftCloseBracket']}{name}{aux['rightOpenBracket']}{self._recursiveUnparse(arguments[1])}{aux['rightCloseBracket']}"#need to get the brackets....
        raise Exception(f'Unhandled {keyTuple}')

    def latexToScheme(self):
        """
        #~ DRAFT ~#
        backslash_variable to 1 node!
        """
        raise Exception('unImplemented')