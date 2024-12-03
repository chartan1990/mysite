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
            '_tagBracketsToBackslash':False,
            '_updateInfixNearestBracketInfix':False,
            '__updateInfixNearestBracketInfix':False,#
            '_removeCaretThatIsNotExponent':False,
            '_findLeftOverPosition':False,
            '_contiguousLeftOvers':False,
            '_collateBackslashInfixLeftOversToContiguous':False,
            '__updateBackslashLeftOversBracketInfo':False,
            '_updateBackslashLeftOversBracketInfo':False,
            '_graftGrenzeRangesIntoContainmentTree':False,#
            '__addImplicitZero':False,
            '__addImplicitMultiply':False,
            '__intraGrenzeSubtreeUe':True,#
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


        #################DEBUGGING TOOL FOR PARENT/CHILD RELATIONSHIP:
        def printConsecutiveGroup(consecutiveGroups):
            grenzeRangeToShortDings = {}
            for grenzeRange, dings in consecutiveGroups.items():
                # dings = consecutiveGroups[grenzeRange]
                # import pdb;pdb.set_trace()

                shortDings = {}
                for d in dings:
                    idd = (d['name'], d['startPos'], d['endPos'])
                    c0 = None if 'child' not in d or d['child'][1] is None else (d['child'][1]['name'], d['child'][1]['startPos'], d['child'][1]['endPos'])
                    c1 = None if 'child' not in d or 2 not in d['child'] or d['child'][2] is None else (d['child'][2]['name'], d['child'][2]['startPos'], d['child'][2]['endPos'])
                    pard = None if d['parent'] is None else (d['parent']['name'], d['parent']['startPos'], d['parent']['endPos'])
                    shortDings[idd] = {'c1':c0, 'c2':c1, 'parent':pard}
                    # import pdb;pdb.set_trace()
                grenzeRangeToShortDings[grenzeRange] = shortDings
            # print('level: ', level, 'grenzeRanges: ', grenzeRanges, 'grenzeRangeToShortDings', )
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(grenzeRangeToShortDings)

        self.printConsecutiveGroup = printConsecutiveGroup
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
            print('infixList:')
            pp.pprint(self.infixList)
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
                        'position':positionTuple[0],
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


    def _tagBracketsToBackslash(self):
        for bracketInfoDict in self.matchingBracketsLocation: 
            bracketInfoDict['belongToBackslash'] = False
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
                if vInfoDict['argument1StartPosition'] is not None and (vInfoDict['argument1StartPosition'] - lenOrZero(vInfoDict['argument1BracketType'])) == bracketInfoDict['openBracketPos']:# and (vInfoDict['argument1StartPosition'] - lenOrZero(vInfoDict['argument1BracketType'])) <= startBracketPos and endBracketPos <= (vInfoDict['argument1EndPosition'] + lenOrZero(vInfoDict['argument1BracketType'])):

                    # if self.showError():
                    #     print('bracketPos: ', (startBracketPos, endBracketPos), ' is arg Of backslashVariable: ', (vInfoDict['name'], vInfoDict['startPos']))
                    bracketInfoDict['belongToBackslash'] = True
                    continue
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
                if fInfoDict['argument1BracketType'] is not None and (fInfoDict['argument1StartPosition'] - lenOrZero(fInfoDict['argument1BracketType'])) == bracketInfoDict['openBracketPos'] :# and (fInfoDict['argument1StartPosition'] - lenOrZero(fInfoDict['argument1BracketType'])) <= startBracketPos and endBracketPos <= (fInfoDict['argument1EndPosition'] + lenOrZero(fInfoDict['argument1BracketType'])):

                    # if self.showError():
                    #     print('bracketPos: ', (startBracketPos, endBracketPos), ' is arg1 Of backslashFunction: ', (fInfoDict['name'], fInfoDict['startPos']))
                    bracketInfoDict['belongToBackslash'] = True
                    continue
                ##########################
                # print("f2looking at: ", (fInfoDict['name'], fInfoDict['startPos'], fInfoDict['endPos']), "(arg2)'s ", fInfoDict['argument2StartPosition'] - lenOrZero(fInfoDict['argument2BracketType']), ' == ', startBracketPos)
                # import pdb;pdb.set_trace()
                ##########################
                if fInfoDict['argument2BracketType'] is not None and (fInfoDict['argument2StartPosition'] - lenOrZero(fInfoDict['argument2BracketType'])) == bracketInfoDict['openBracketPos']:# and (fInfoDict['argument2StartPosition'] - lenOrZero(fInfoDict['argument2BracketType'])) <= startBracketPos and endBracketPos <= (fInfoDict['argument2EndPosition'] + lenOrZero(fInfoDict['argument2BracketType'])):

                    # if self.showError():
                    #     print('bracketPos: ', (startBracketPos, endBracketPos), ' is arg2 Of backslashFunction: ', (fInfoDict['name'], fInfoDict['startPos']))
                    bracketInfoDict['belongToBackslash'] = True
                    continue



    def __updateInfixNearestBracketInfix(self, tempInfixList0, tempInfixList1):
        sortedMainInfixList = sorted(tempInfixList0, key=lambda tup: Latexparser.PRIOIRITIZED_INFIX.index(tup['name']))
        sortedAgainstInfixList = sorted(tempInfixList1, key=lambda tup: Latexparser.PRIOIRITIZED_INFIX.index(tup['name']))
        ###########helpers
        def priorityOfOtherInfixEnHaltBrack(startBracketPos, endBracketPos, startBracketLength, endBracketLength, selfName, selfStartPos):#This is for case : test__collateBackslashInfixLeftOversToContiguous__exponentialOverMultiply
            """
            test__collateBackslashInfixLeftOversToContiguous__exponentialOverMultiply
            3x^{9} = 3x^{2}x^{7}
            3x^{2}x^{7}
            ==>
            3 x ^ 2 * x ^ 7
            """
            if self.showError():
                print('isArgOfOtherInfix???~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            # import pdb;pdb.set_trace()
            for infixInfoDict2 in sortedAgainstInfixList:
                #skip infixInfoDict2 that we are checking now
                if infixInfoDict2['name'] == selfName and infixInfoDict2['startPos'] == selfStartPos:
                    continue
                if self.showError():
                    print('checking brack', (startBracketPos, endBracketPos),' against infix:', (infixInfoDict2['name'], infixInfoDict2['startPos'], infixInfoDict2['endPos']))
                    # import pdb;pdb.set_trace()
                #if 'tight__leftEndPos' in infixInfoDict2 and infixInfoDict2['tight__leftEndPos'] is not None and infixInfoDict2['tight__leftEndPos'] == endBracketPos:
                if infixInfoDict2['startPos'] == (endBracketPos - endBracketLength): # - because endBracketPos includes the endBracketLength
                    #this bracket is actually infixInfoDict2 leftArg
                    if self.showError():
                        print('bracketPos: ', (startBracketPos, endBracketPos), ' is leftArg Of infix: ', (infixInfoDict2['name'], infixInfoDict2['startPos']))
                    return Latexparser.PRIOIRITIZED_INFIX.index(infixInfoDict2['name'])#True
                #if 'tight__rightStartPos' in infixInfoDict2 and infixInfoDict2['tight__rightStartPos'] is not None and infixInfoDict2['tight__rightStartPos'] == startBracketPos:
                if infixInfoDict2['startPos'] + len(infixInfoDict2['name']) == startBracketPos - startBracketLength:
                    #this bracket is actually infixInfoDict2 rightArg
                    if self.showError():
                        print('bracketPos: ', (startBracketPos, endBracketPos), ' is rightArg Of infix: ', (infixInfoDict2['name'], infixInfoDict2['startPos']))
                    return Latexparser.PRIOIRITIZED_INFIX.index(infixInfoDict2['name'])#True

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
        # def ali(a, b):
        #     return True
        # self.allowedInfix = ali
        for infixInfoDict0 in sortedMainInfixList:
            infixInfoDict0.update({
                'enclosingBracketsNonBackslashArg':[]
            })#leftRightBrackets are unique...., there is no tightest nor widest leftRightBrackets
            ############
            if self.showError():
                print('infixBracMatch: ', (infixInfoDict0['name'], infixInfoDict0['startPos'], infixInfoDict0['endPos']), '^^^<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
            ############
            #find nearest infix, might be the case that there is no brackets at all, then we rely on infix for ganzRange
            nearestLeftInfix = {
                'name':None, 
                'position':0 if infixInfoDict0['position'] < self.equalPos else self.equalPos, 
                'startPos':0 if infixInfoDict0['position'] < self.equalPos else self.equalPos, 
                'endPos': 0 if infixInfoDict0['position'] < self.equalPos else self.equalPos
            }
            nearestRightInfix = {
                'name':None, 
                'position':self.equalPos+1 if infixInfoDict0['position'] < self.equalPos else len(self._eqs), 
                'startPos': self.equalPos+1 if infixInfoDict0['position'] < self.equalPos else len(self._eqs), 
                'endPos':self.equalPos+1 if infixInfoDict0['position'] < self.equalPos else len(self._eqs)
            }
            for infixInfoDict1 in sortedAgainstInfixList:
                if infixInfoDict0['name'] == infixInfoDict1['name'] and infixInfoDict0['position'] == infixInfoDict1['position']: 
                    #avoid using the same infix as infixInfoDict0
                    continue
                if sameSideAsInfoDictOfEqual(infixInfoDict0, infixInfoDict1):
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
            leftBracket = {
                'openBracketType':None,
                'closeBracketType':None,
                'openBracketPos':None,
                'closeBracketPos':None
            }
            rightBracket = {
                'openBracketType':None,
                'closeBracketType':None,
                'openBracketPos':None,
                'closeBracketPos':None
            }


            for bracketInfoDict in self.matchingBracketsLocation: 

                #check if enclosing
                if bracketInfoDict['openBracketPos'] + len(bracketInfoDict['openBracketType']) <= infixInfoDict0['startPos'] and infixInfoDict0['endPos'] <= bracketInfoDict['closeBracketPos'] + len(bracketInfoDict['closeBracketType']):
                    # if not bracketInfoDict['belongToBackslash']:
                    infixInfoDict0['enclosingBracketsNonBackslashArg'].append({
                        'enclosingStartPos':bracketInfoDict['openBracketPos'],
                        'enclosingEndPos':bracketInfoDict['closeBracketPos'],
                        'enclosingStartType':bracketInfoDict['openBracketType'],
                        'enclosingEndType':bracketInfoDict['closeBracketType'],
                        'belongToBackslash':bracketInfoDict['belongToBackslash']
                    })#HHHHHHHHHHHHHHHHHHHHHH filter for BackslashArgs? 

                #direct left-side (of infixInfoDict0)
                elif bracketInfoDict['closeBracketPos'] + len(bracketInfoDict['closeBracketType']) == infixInfoDict0['startPos']:
                    # isBackSlashBrackets = collideWithNonEnclosingBackslashBrackets(bracketInfoDict['openBracketPos'], bracketInfoDict['closeBracketPos'], infixInfoDict0['name'], infixInfoDict0['startPos'])
                    leftBracket = bracketInfoDict
                    # leftBracket['belongToBackslash'] = bracketInfoDict['belongToBackslash']
                #direct right-side (of infixInfoDict0)
                elif infixInfoDict0['endPos'] == bracketInfoDict['openBracketPos'] - len(bracketInfoDict['openBracketType']):
                    # isBackSlashBrackets = collideWithNonEnclosingBackslashBrackets(bracketInfoDict['openBracketPos'], bracketInfoDict['closeBracketPos'], infixInfoDict0['name'], infixInfoDict0['startPos'])
                    rightBracket = bracketInfoDict
                    # rightBracket['belongToBackslash'] = isBackSlashBrackets['belongToBackslash']


            #but, first, update common information, needed later but too early to add, at discovery.... is this better though?
            infixInfoDict0.update({
                'type':'infix',
                'child':{1:None, 2:None}, #sockets for intralevel, interlevel subtree
                'parent':None, #sockets for intralevel, interlevel subtree
                #fill up with None
                'ganzStartPos':0 if infixInfoDict0['position'] < self.equalPos else self.equalPos, #later will limit this position
                'ganzEndPos': self.equalPos + 1 if infixInfoDict0['position'] < self.equalPos else len(self._eqs), #later will limit this position

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
                'left__type':'arg',

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
            if leftBracket['openBracketType'] is not None and not leftBracket['belongToBackslash']: # tightest
                infixInfoDict0.update({
                    'startPos':infixInfoDict0['startPos'], # only the infix character/s
                    'endPos':infixInfoDict0['endPos'], # only the infix character/s
                    'ganzStartPos':leftBracket['openBracketPos'], # infix with args and brackets
                    # 'ganzEndPos':, # infix with args and brackets, only checking left, cannot get the rightEnding

                    'left__startBracketPos':leftBracket['openBracketPos'],
                    'left__startBracketType':leftBracket['openBracketType'],
                    'left__endBracketPos':leftBracket['closeBracketPos'],
                    'left__endBracketType':leftBracket['closeBracketType'],
                    'left__argStart':leftBracket['openBracketPos']+lenOrZero(leftBracket['openBracketType']),
                    'left__argEnd':leftBracket['closeBracketPos']+lenOrZero(leftBracket['closeBracketType']),
                    'left__type':'leftRight'#'backslashArg' if leftBracket['belongToBackslash'] else 'leftRight'
                    # 'left__type':'leftRight' if wideRightBracket['closeBracketType'] is not None else 'halfLeftRight'
                })
            elif nearestLeftInfix['name'] is not None:
                infixInfoDict0.update({
                    'startPos':infixInfoDict0['startPos'], # only the infix character/s
                    'endPos':infixInfoDict0['endPos'], # only the infix character/s
                    'ganzStartPos':nearestLeftInfix['endPos'], # infix with args and brackets
                    # 'ganzEndPos':, # infix with args and brackets, only checking left, cannot get the rightEnding

                    'left__startBracketPos':None,
                    'left__startBracketType':None,
                    'left__endBracketPos':None,
                    'left__endBracketType':None,
                    'left__argStart':nearestLeftInfix['endPos'],
                    'left__argEnd':infixInfoDict0['position'],
                    'left__type':'infix'#'backslashArg' if leftBracket['belongToBackslash'] else 'leftRight'
                    # 'left__type':'leftRight' if wideRightBracket['closeBracketType'] is not None else 'halfLeftRight'
                })



            if rightBracket['openBracketType'] is not None and not rightBracket['belongToBackslash']: # tightest
                infixInfoDict0.update({
                    'startPos':infixInfoDict0['startPos'], # only the infix character/s
                    'endPos':infixInfoDict0['endPos'], # only the infix character/s
                    # 'ganzStartPos':, # infix with args and brackets, only checking right, cannot get the leftEnding
                    'ganzEndPos':rightBracket['closeBracketPos'], # infix with args and brackets

                    'right__startBracketPos':rightBracket['openBracketPos'],
                    'right__startBracketType':rightBracket['openBracketType'],
                    'right__endBracketPos':rightBracket['closeBracketPos'],
                    'right__endBracketType':rightBracket['closeBracketType'],
                    'right__argStart':rightBracket['openBracketPos']+lenOrZero(rightBracket['openBracketType']),
                    'right__argEnd':rightBracket['closeBracketPos']+lenOrZero(rightBracket['closeBracketType']),
                    'right__type':'leftRight'#'backslashArg' if rightBracket['belongToBackslash'] else 'leftRight'
                    # 'right__type':'leftRight' if wideLeftBracket['openBracketType'] is not None else 'halfLeftRight'
                })
            elif nearestRightInfix['name'] is not None:
                infixInfoDict0.update({
                    'startPos':infixInfoDict0['startPos'], # only the infix character/s
                    'endPos':infixInfoDict0['endPos'], # only the infix character/s
                    # 'ganzStartPos':, # infix with args and brackets, only checking right, cannot get the leftEnding
                    'ganzEndPos':nearestRightInfix['startPos'], # infix with args and brackets

                    'right__startBracketPos':None,
                    'right__startBracketType':None,
                    'right__endBracketPos':None,
                    'right__endBracketType':None,
                    'right__argStart':infixInfoDict0['position'] + len(infixInfoDict0['name']),
                    'right__argEnd':nearestRightInfix['startPos'],
                    'right__type':'infix'#'backslashArg' if rightBracket['belongToBackslash'] else 'leftRight'
                    # 'right__type':'leftRight' if wideLeftBracket['openBracketType'] is not None else 'halfLeftRight'
                })


            if (leftBracket['openBracketType'] is None or leftBracket['belongToBackslash']) and \
            (rightBracket['openBracketType'] is None or rightBracket['belongToBackslash']) and \
            len(infixInfoDict0['enclosingBracketsNonBackslashArg']) > 0: # most prefered type of ending, will replace above chosen brackets
                #use enclosing to get the ganzEndPos and ganzStartPos (and all the bracket information)
                #find tightest enclosing bracket
                # import pdb;pdb.set_trace()
                tightestOpenBracketPos = infixInfoDict0['enclosingBracketsNonBackslashArg'][0]['enclosingStartPos']
                tightestOpenBracketType = infixInfoDict0['enclosingBracketsNonBackslashArg'][0]['enclosingStartType']
                tightestCloseBracketPos = infixInfoDict0['enclosingBracketsNonBackslashArg'][0]['enclosingEndPos']
                tightestCloseBracketType = infixInfoDict0['enclosingBracketsNonBackslashArg'][0]['enclosingEndType']
                for bracketInfoDict in infixInfoDict0['enclosingBracketsNonBackslashArg']:
                    if tightestOpenBracketPos < bracketInfoDict['enclosingStartPos'] and bracketInfoDict['enclosingEndPos'] < tightestCloseBracketPos:
                        tightestOpenBracketPos = bracketInfoDict['enclosingStartPos']
                        tightestOpenBracketType = bracketInfoDict['enclosingStartType']
                        tightestCloseBracketPos = bracketInfoDict['enclosingEndPos']
                        tightestCloseBracketType = bracketInfoDict['enclosingEndType']
                infixInfoDict0.update({
                    'ganzStartPos':tightestOpenBracketPos + len(tightestOpenBracketType),
                    'ganzEndPos':tightestCloseBracketPos,

                    'left__startBracketPos':tightestOpenBracketPos,
                    'left__startBracketType':tightestOpenBracketType,
                    'left__endBracketPos':None,
                    'left__endBracketType':None,
                    'left__argStart':tightestOpenBracketPos + len(tightestOpenBracketType),
                    'left__argEnd':infixInfoDict0['position'],
                    'left__type':'enclosing',#'backslashArg' if leftBracket['belongToBackslash'] else 'leftRight'

                    'right__startBracketPos':None,
                    'right__startBracketType':None,
                    'right__endBracketPos':tightestCloseBracketPos,
                    'right__endBracketType':tightestCloseBracketType,
                    'right__argStart':infixInfoDict0['position'] + len(infixInfoDict0['name']),
                    'right__argEnd':tightestCloseBracketPos,
                    'right__type':'enclosing'#'backslashArg' if rightBracket['belongToBackslash'] else 'leftRight'
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

        self.occupiedBrackets = set()#[]# for bubble merge later, these entreSpaces are connected
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
            #add all the brackets that do not belong to backSlash 
            for bracketInfoDict in self.matchingBracketsLocation:
                if not bracketInfoDict['belongToBackslash']:
                    for pos in range(bracketInfoDict['openBracketPos'], bracketInfoDict['closeBracketPos']+len(bracketInfoDict['closeBracketType'])):
                        self.occupiedBrackets.add(pos)
        self.occupiedBrackets = sorted(list(self.occupiedBrackets))

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
            isNume = isNum(leftOverC) or leftOverC == '.'
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

        def rangesConsecutiveInEqsIgnoringSpace(grenzeRange0, grenzeRange1):#and unoccupiedBrackets found in _findLeftOverPosition
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


    def __updateBackslashLeftOversBracketInfo(self, infoDictsToUpdate):
        """
        backslash_function/backslash_variable/variable/numbers should only have enclosing...

        This necessity was verdeckt because of errors from addImplicitMultiply, so this is a fix dedicated to addImplicitMultiply


        if brackets belong to backslash, then cannot be used for implicit-multiply

        (1+(1+(1+1)))(((1+1)+1)+1)
                    ^
        implicit-multiply needed here, and we need position of the widest-enclosing-bracket

        (1+(1+1)(1+1)+1)+1
               ^
        implicit-multiply needed here, and we need position of the tightest-enclosing-bracket

        ((1+(1+(1+1)))(((1+1)+1)+1)+1)+1
                     ^
        implicit-multiply needed here, and its not the tightest-enclosing-bracket, nor widest-enclosing-bracket

        so if under the same widest brackets, then look to tightest brackets?
        can it be under the same tightest bracket?
        (x+y+z)


        Keep all the enclosingbracket-notbackslashargument-information in the backslash_function/backslash_variable/variable/number
        """
        def bracketsBelongToBackSlash(startBracketPos):
            if self.showError():
                print('collideWithNonEnclosingBackslashBrackets~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~', startBracketPos, endBracketPos)
            #######
            # print('collideWithNonEnclosingBackslashBrackets self.variablesPos: ', self.variablesPos)
            # import pdb;pdb.set_trace()
            #######
            for vInfoDict in self.variablesPos:
                if vInfoDict['argument1StartPosition'] is not None and (vInfoDict['argument1StartPosition'] - lenOrZero(vInfoDict['argument1BracketType'])) == startBracketPos:
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
                if fInfoDict['argument1BracketType'] is not None and (fInfoDict['argument1StartPosition'] - lenOrZero(fInfoDict['argument1BracketType'])) == startBracketPos :
                    return True
                ##########################
                # print("f2looking at: ", (fInfoDict['name'], fInfoDict['startPos'], fInfoDict['endPos']), "(arg2)'s ", fInfoDict['argument2StartPosition'] - lenOrZero(fInfoDict['argument2BracketType']), ' == ', startBracketPos)
                # import pdb;pdb.set_trace()
                ##########################
                if fInfoDict['argument2BracketType'] is not None and (fInfoDict['argument2StartPosition'] - lenOrZero(fInfoDict['argument2BracketType'])) == startBracketPos:
                    return True
            return False


        for infoDict in infoDictsToUpdate:
            infoDict.update({
                'enclosingBracketsNonBackslashArg':[]
            })
            # import pdb;pdb.set_trace()
            for bracketInfoDict in self.matchingBracketsLocation: 
                if bracketsBelongToBackSlash(bracketInfoDict['openBracketPos']):
                    continue # skip because it cannot be used in implicit-multiply
                #is bracketInfoDict enclosing infoDict?
                if bracketInfoDict['openBracketPos'] <= infoDict['ganzStartPos'] and infoDict['ganzEndPos'] <= bracketInfoDict['closeBracketPos']:
                    infoDict['enclosingBracketsNonBackslashArg'].append({
                        'enclosingStartPos':bracketInfoDict['openBracketPos'],
                        'enclosingEndPos':bracketInfoDict['closeBracketPos'],
                        'enclosingStartType':bracketInfoDict['openBracketType'],
                        'enclosingEndType':bracketInfoDict['closeBracketType'],
                        'belongToBackslash':bracketInfoDict['belongToBackslash']
                    })
            #sort enclosingBracketsNonBackslashArg, peutetre sort according to enclosingStartPos and enclosingEndPos, and keep 2 list


    def _updateBackslashLeftOversBracketInfo(self):
        self.__updateBackslashLeftOversBracketInfo(self.functionPos+self.variablesPos+self.noBraBackslashPos+self.contiguousInfoList)


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
        Here we 
        1. build self.consecutiveGroups into EnclosureTree
        2. By the levels of EnclosureTree
            a. __addImplicitZero
            b. __addImplicitMultipy
        3. By the levels of EnclosureTree
            a. __intraGrenzeSubtreeUe
        4. By the levels of EnclosureTree
            a. __interLevelSubtreeGrafting
            b. dump all nodes into self.alleDing for the next process to use
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
                    # shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                    # print('level: ', level, 'grenzeRange: ', grenzeRange, 'shortDings: ', shortDings)
                    # print('BEGINT dings: ', list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), dings)))
                    print('************************************_graftGrenzeRangesIntoContainmentTree (NOTHING)**********************************************')
                    self.printConsecutiveGroup(self.consecutiveGroups)
                    print('***************************************_graftGrenzeRangesIntoContainmentTree (NOTHING)*******************************************')
                    print('**************************')
                ################
                #here, we need to 
                #__addImplicitZero
                dings = self.__addImplicitZero(dings)
                ################
                if self.showError():
                    print('**************************')
                    # shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                    # print('level: ', level, 'grenzeRange: ', grenzeRange, 'shortDings: ', shortDings)
                    # print('After implicitzero dings: ', list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), dings)))
                    print('**************************')
                    print('************************************_graftGrenzeRangesIntoContainmentTree (__addImplicitZero)**********************************************')
                    self.printConsecutiveGroup(self.consecutiveGroups)
                    print('***************************************_graftGrenzeRangesIntoContainmentTree (__addImplicitZero)*******************************************')
                ################
                #__addImplicitMultiply
                dings = self.__addImplicitMultiply(dings) 
                ################
                ################
                self.consecutiveGroups[grenzeRange] = dings # replace with the new dings
                if self.showError():
                    print('**************************')
                    # shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                    # print('level: ', level, 'grenzeRange: ', grenzeRange, 'shortDings: ', shortDings)
                    # print('After implicitmultiply dings: ', list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), dings)))
                    # print('**************************')
                    print('************************************_graftGrenzeRangesIntoContainmentTree (__addImplicitMultiply)**********************************************')
                    self.printConsecutiveGroup(self.consecutiveGroups)
                    print('***************************************_graftGrenzeRangesIntoContainmentTree (__addImplicitMultiply)*******************************************')
            levelTo_grenzeRangeToRoot[level] = grenzeRangeToRoot
            ################
            if self.showError():
                print('*************self.consecutiveGroups*************')
                self.printConsecutiveGroup(self.consecutiveGroups)
                print('************self.consecutiveGroups**************')
            ################
        # print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@DOING INTRALEVEL')
        for level, grenzeRanges in sorted(list(levelToIDs.items()), key=lambda t: t[0]): # t[0] is the level
            grenzeRangeToRoot = levelTo_grenzeRangeToRoot[level]
            for grenzeRange in grenzeRanges:
                dings = self.consecutiveGroups[grenzeRange]
                #__intraGrenzeSubtreeUe
                rootOfDingsWithGanzRange, dings = self.__intraGrenzeSubtreeUe(dings) #{'root':ding, 'ganzStartPos':[of the whole tree], 'ganzEndPos':[of the whole tree]}
                grenzeRangeToRoot[grenzeRange] = rootOfDingsWithGanzRange
                ################
                if self.showError():
                    # shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                    # print('level: ', level, 'grenzeRange: ', grenzeRange, 'shortDings: ', shortDings)
                    # print('After __intraGrenzeSubtreeUe dings: ', list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), dings)))
                    # print('root: ', (rootOfDingsWithGanzRange['root']['name'], rootOfDingsWithGanzRange['root']['startPos'], rootOfDingsWithGanzRange['root']['endPos']), ' ganzrange: ', (rootOfDingsWithGanzRange['ganzStartPos'], rootOfDingsWithGanzRange['ganzEndPos']))
                    # print('**************************')

                    # print('**********************')
                    print('*********_graftGrenzeRangesIntoContainmentTree (just after intralevel)********************************')
                    self.printConsecutiveGroup(self.consecutiveGroups)
                    print('*********_graftGrenzeRangesIntoContainmentTree********************************')
                ################
                self.consecutiveGroups[grenzeRange] = dings
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
                    # shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                    # print('level: ', level, 'grenzeRange: ', grenzeRange, 'shortDings: ', shortDings)
                    # print('After __interLevelSubtreeGrafting dings: ', list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), dings)))
                    # print('grenzeRangeParent: ', grenzeRangeParent, ' PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPParent')

                    print('*********_graftGrenzeRangesIntoContainmentTree (before interLevel)********************************')
                    self.printConsecutiveGroup(self.consecutiveGroups)
                    print('*********_graftGrenzeRangesIntoContainmentTree********************************')
                    print('*************__interLevelSubtreeGraftingVOR*************')
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
                        # shortDings = list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings))
                        # print('level: ', level, 'grenzeRange: ', grenzeRange, 'shortDings: ', shortDings)
                        # print('After __interLevelSubtreeGrafting dings: ', list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), dings)))
                        # print('parentDings: ', list(map(lambda ding:(ding['name'], ding['startPos'], ding['endPos']), parentDings)))

                        print('*********_graftGrenzeRangesIntoContainmentTree (after interlevel)********************************')
                        self.printConsecutiveGroup(self.consecutiveGroups)
                        print('*********_graftGrenzeRangesIntoContainmentTree********************************')
                        print('**************************')
                    ################
                self.alleDing += dings # TODO something wrong with alleDing, its repeating dings that should not be

                #####################
                if self.showError():
                    print('**********************alleDing: <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    print(list(map(lambda ding: (ding['name'], ding['startPos'], ding['endPos']), self.alleDing)))
                    print('*********_graftGrenzeRangesIntoContainmentTree (check alleDing)********************************')
                    self.printConsecutiveGroup({(0, 0):self.alleDing})
                    print('*********_graftGrenzeRangesIntoContainmentTree********************************')
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
            # import pdb;pdb.set_trace()
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
                'enclosingBracketsNonBackslashArg':[], # FILL IT UP
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
            self.__updateBackslashLeftOversBracketInfo([implicitZero])
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
        Ob es gibt 'touchingBrackets', dann es gibt implicit-multiply, sonst Man kannt nicht implicit-multiply haben

        Falls gibt es implicit-multiply, dann:
            Das right__type und left__type ist immer 'leftRight' oder 'arg'.
            Ob es gibt 'enclosing' oder 'leftRight' auf der links, dann left__type='leftRight', sonst es ist 'arg'
            ebenso
            Ob es gibt 'enclosing' oder 'leftRight' auf der rechts, dann right__type='leftRight', sonst es ist 'arg'
        """
        #~~~~~~~~~~~~~~~~~~~~~HELPER FUNCTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        def findCommonBrackets(leftArgBracketList, rightArgBracketList):
            """
            Since leftArgBracketList and rightArgBracketList contains all the brackets-enclosing-bothargs-without-backslash
            the implicit-multiply would be contained in the intersection of leftArgBracketList and rightArgBracketList.
            """
            # import pdb;pdb.set_trace()
            matchedIndexInRightBracketList = [] # those that were matched in rightArgBracketList, will not need to be checked again.
            commonBrackets = []
            for leftBracketInfoDict in leftArgBracketList:
                for index, rightBracketInfoDict in enumerate(rightArgBracketList):
                    if index in matchedIndexInRightBracketList:
                        continue # matched already not need to check again.
                    #check if brackets are equals, need to match on all the common keys.
                    commonKeys = set(leftBracketInfoDict.keys()).intersection(set(rightBracketInfoDict.keys()))
                    matchedIndex = index
                    for commonKey in commonKeys:
                        if leftBracketInfoDict[commonKey] != rightBracketInfoDict[commonKey]:
                            matchedIndex = None
                            break
                    #we found a match for leftBracketInfoDict
                    # import pdb;pdb.set_trace()
                    if matchedIndex is not None:
                        matchedIndexInRightBracketList.append(matchedIndex)
                        commonBrackets.append(leftBracketInfoDict) # rightBracketInfoDict is equals
            return commonBrackets


        #touching brackets TODO refactor
        def touchingBrackets(leftArgBracketList, rightArgBracketList):
            """
            ((()))  ((()))
                  ^
        This position will be returned. Notice that we allow whitespace


        (TODO refactor) test case:~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

eqs = '(1+(1+(1+1)))      (((1+1)+1)+1)'


def touchingBrackets(leftArgBracketList, rightArgBracketList):
  for leftBracketInfoDict in leftArgBracketList:
    for rightBracketInfoDict in rightArgBracketList: 
      touchingPos = leftBracketInfoDict['enclosingEndPos']+len(leftBracketInfoDict['enclosingEndType'])
      chasZweischen = eqs[touchingPos:rightBracketInfoDict['enclosingStartPos']]
      if len(chasZweischen.strip()) == 0: #only whitespace between leftBracket and rightBracket, then they are touching
          return touchingPos





leftArgBracketList = [
    {
        'enclosingStartPos':0,
        'enclosingEndPos':12,
        'enclosingStartType':'(',
        'enclosingEndType':')'
    },
    {
        'enclosingStartPos':3,
        'enclosingEndPos':11,
        'enclosingStartType':'(',
        'enclosingEndType':')'
    },
    {
        'enclosingStartPos':6,
        'enclosingEndPos':10,
        'enclosingStartType':'(',
        'enclosingEndType':')'
    },
]
rightArgBracketList = [
    {
        'enclosingStartPos':19,
        'enclosingEndPos':31,
        'enclosingStartType':'(',
        'enclosingEndType':')'
    },
    {
        'enclosingStartPos':20,
        'enclosingEndPos':28,
        'enclosingStartType':'(',
        'enclosingEndType':')'
    },
    {
        'enclosingStartPos':21,
        'enclosingEndPos':25,
        'enclosingStartType':'(',
        'enclosingEndType':')'
    },
]


if __name__=='__main__':
    touchingBracketsPos = touchingBrackets(leftArgBracketList, rightArgBracketList)
    expected = 13
    print(' PASSED? ', touchingBracketsPos == expected)
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            :param leftArgBracketList: list of dictionary with the following keys
                enclosingStartPos
                enclosingEndPos
                enclosingStartType
                enclosingEndType
            :type leftArgBracketList: list[dict[str, Any]]
            :param rightArgBracketList: same format as leftArgBracketList.
            list of dictionary with the following keys
                enclosingStartPos
                enclosingEndPos
                enclosingStartType
                enclosingEndType
            :type rightArgBracketList: list[dict[str, Any]]
            :return: leftest position when there are brackets that touch. 
                     None if there are no touching brackets
            :rtype: Any
            """
            for leftBracketInfoDict in leftArgBracketList:
                # TODO can be made more efficient by selecting rightBracketInfoDict[enclosingStartPos] > leftBracketInfoDict[enclosingEndPos],(in the second loop) 
                # and ALSO sorting both list before hand and then use binary search.... (for larger list next time)
                for rightBracketInfoDict in rightArgBracketList: 
                    # import pdb;pdb.set_trace()
                    touchingPos = leftBracketInfoDict['enclosingEndPos']+lenOrZero(leftBracketInfoDict['enclosingEndType'])
                    if touchingPos > rightBracketInfoDict['enclosingStartPos']: # overshoot
                        continue
                    chasZweischen = self._eqs[touchingPos:rightBracketInfoDict['enclosingStartPos']]
                    # import pdb;pdb.set_trace()
                    if len(chasZweischen.strip()) == 0: #only whitespace between leftBracket and rightBracket, then they are touching
                        return touchingPos, leftBracketInfoDict, rightBracketInfoDict

        newDings = [dings[0]]
        # self.nodeId
        if len(dings) > 1: # must have at least 2 items in dings, sonst kann nicht implicitMultiply zwischenstellen
            import copy
            for idx in range(1, len(dings)):
                hinDing = dings[idx-1]
                vorDing = dings[idx]
                # import pdb;pdb.set_trace()
                hinTouchingBrackets = copy.deepcopy(hinDing['enclosingBracketsNonBackslashArg'])
                #add type
                for hinTouchingBracket in hinTouchingBrackets:
                    hinTouchingBracket['type'] = 'leftEnclosing'
                #add on the fake brackets
                # import pdb;pdb.set_trace()
                if hinDing['type']=='infix' and hinDing['right__type'] == 'leftRight':
                    hinTouchingBrackets.append({ # FAKE-ENCLOSING to get touching position
                        'enclosingStartPos':hinDing['right__startBracketPos'],
                        'enclosingEndPos':hinDing['right__endBracketPos'],
                        'enclosingStartType':hinDing['right__startBracketType'],
                        'enclosingEndType':hinDing['right__endBracketType'],
                        'type':'left',
                        'belongToBackslash':False
                    })
                if hinDing['type']!='infix' and len(hinDing['enclosingBracketsNonBackslashArg']) == 0: # non-infix with NO enclosingbrackets
                    hinTouchingBrackets.append({ # FAKE-ENCLOSING to get touching position
                        'enclosingStartPos':hinDing['ganzStartPos'],
                        'enclosingEndPos':hinDing['ganzEndPos'],
                        'enclosingStartType':None,
                        'enclosingEndType':None,
                        'type':'leftArg',
                        'belongToBackslash':False
                    })

                vorTouchingBrackets = copy.deepcopy(vorDing['enclosingBracketsNonBackslashArg'])
                #add type
                for vorTouchingBracket in vorTouchingBrackets:
                    vorTouchingBracket['type'] = 'rightEnclosing'
                # add on the fake brackets
                if vorDing['type']=='infix' and vorDing['left__type'] == 'leftRight':
                    vorTouchingBrackets.append({ # FAKE-ENCLOSING to get touching position
                        'enclosingStartPos':vorDing['left__startBracketPos'],
                        'enclosingEndPos':vorDing['left__endBracketPos'],
                        'enclosingStartType':vorDing['left__startBracketType'],
                        'enclosingEndType':vorDing['left__endBracketType'],
                        'type':'right',
                        'belongToBackslash':False
                    })
                if vorDing['type']!='infix' and len(vorDing['enclosingBracketsNonBackslashArg']) == 0: # non-infix with NO enclosingbrackets
                    vorTouchingBrackets.append({ # FAKE-ENCLOSING to get touching position
                        'enclosingStartPos':vorDing['ganzStartPos'],
                        'enclosingEndPos':vorDing['ganzEndPos'],
                        'enclosingStartType':None,
                        'enclosingEndType':None,
                        'type':'rightArg',
                        'belongToBackslash':False
                    })
                try:
                    resultTup = touchingBrackets(hinTouchingBrackets, vorTouchingBrackets)
                except:
                    import pdb;pdb.set_trace()

                if self.showError():
                    print('~~~~~~~~~~~~~~~~~~~~implicitMultiply TOUCHING BRACKETS~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                    print((hinDing['name'], hinDing['startPos']), ' || ', (vorDing['name'], vorDing['startPos']))
                    print('hinTouchingBrackets:')
                    print(hinTouchingBrackets)
                    print('vorTouchingBrackets:')
                    print(vorTouchingBrackets)
                    print('bracket Touching resultTup:')
                    print(resultTup)
                    print('~~~~~~~~~~~~~~~~~~~~implicitMultiply TOUCHING BRACKETS~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                if resultTup is not None: # used a signal to put the implicit-multiply in
                    bracketsTouchingStartPos, touchingLeftBracketInfoDict, touchingRightBracketInfoDict = resultTup
                    ganzStartPos = touchingLeftBracketInfoDict['enclosingStartPos']
                    ganzEndPos = touchingRightBracketInfoDict['enclosingEndPos']

                    #left Side
                    left__startBracketPos = None
                    left__startBracketType = None
                    left__endBracketPos = None
                    left__endBracketType = None
                    left__argStart = touchingLeftBracketInfoDict['enclosingStartPos']
                    left__argEnd = touchingLeftBracketInfoDict['enclosingEndPos']
                    if touchingLeftBracketInfoDict['type'] == 'leftArg':
                        left__type = 'arg'
                    else: # touchingLeftBracketInfoDict['type'] == 'left', no inner Bracket
                        left__type = 'leftRight'
                        left__startBracketPos = touchingLeftBracketInfoDict['enclosingStartPos']
                        left__startBracketType = touchingLeftBracketInfoDict['enclosingStartType']
                        left__argStart = touchingLeftBracketInfoDict['enclosingStartPos'] + len(touchingLeftBracketInfoDict['enclosingStartType'])
                        if touchingLeftBracketInfoDict['type'] == 'leftEnclosing': #has inner bracket
                            left__endBracketPos = touchingLeftBracketInfoDict['enclosingEndPos']
                            left__endBracketType = touchingLeftBracketInfoDict['enclosingEndType']
                            # left__argEnd = touchingLeftBracketInfoDict['enclosingEndPos']

                    #right Side
                    right__startBracketPos = None
                    right__startBracketType = None
                    right__endBracketPos = None
                    right__endBracketType = None
                    right__argStart = touchingRightBracketInfoDict['enclosingStartPos']
                    right__argEnd = touchingRightBracketInfoDict['enclosingEndPos']
                    if touchingRightBracketInfoDict['type'] == 'rightArg':
                        right__type = 'arg'
                    else: # touchingRightBracketInfoDict['type'] == 'right', no inner Bracket
                        right__type = 'leftRight'
                        right__endBracketPos = touchingRightBracketInfoDict['enclosingEndPos']
                        right__endBracketType = touchingRightBracketInfoDict['enclosingEndType']
                        # right__argEnd = touchingRightBracketInfoDict['enclosingEndPos']
                        if touchingRightBracketInfoDict['type'] == 'rightEnclosing': #has inner bracket
                            right__startBracketPos = touchingRightBracketInfoDict['enclosingStartPos']
                            right__startBracketType = touchingRightBracketInfoDict['enclosingStartType']
                            right__argStart = touchingRightBracketInfoDict['enclosingStartPos'] + len(touchingRightBracketInfoDict['enclosingStartType'])


                    # self.nodeId += 1
                    implicitMultiplyInfoDict = { # rightarg * leftarg
                        'name':'*',
                        'position':bracketsTouchingStartPos,
                        'type':'implicit',
                        'startPos':bracketsTouchingStartPos,
                        'endPos':bracketsTouchingStartPos, # implicitMultiply is slim :)
                        'ganzStartPos':ganzStartPos,
                        'ganzEndPos':ganzEndPos,
                        'enclosingBracketsNonBackslashArg':findCommonBrackets(hinDing['enclosingBracketsNonBackslashArg'], vorDing['enclosingBracketsNonBackslashArg']),
                        # rightarg
                        'left__startBracketPos':left__startBracketPos, #TODO to test leaves with brackets..
                        'left__startBracketType':left__startBracketType, #TODO to test leaves with brackets..
                        'left__endBracketPos':left__endBracketPos, #TODO to test leaves with brackets..
                        'left__endBracketType':left__endBracketType, #TODO to test leaves with brackets..
                        'left__argStart':left__argStart, # without the bracket
                        'left__argEnd':left__argEnd, # without the bracket
                        'left__type':left__type,
                        # leftarg
                        'right__startBracketPos':right__startBracketPos, #TODO to test leaves with brackets..
                        'right__startBracketType':right__startBracketType, #TODO to test leaves with brackets..
                        'right__endBracketPos':right__endBracketPos, #TODO to test leaves with brackets...
                        'right__endBracketType':right__endBracketType, #TODO to test leaves with brackets...
                        'right__argStart':right__argStart,
                        'right__argEnd':right__argEnd,
                        'right__type':right__type,

                        'child':{1:None, 2:None},
                        'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                    }
                    newDings.append(implicitMultiplyInfoDict)
                newDings.append(vorDing) # add old ding back

        if self.showError():
            print('~~~~~~~~~~~~~~~~~~~~implicitMultiply~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            print('oldDings:')
            print(list(map(lambda d: (d['name'], d['startPos'], d['endPos']), dings)))
            print('newDings:')
            print(list(map(lambda d: (d['name'], d['startPos'], d['endPos']), newDings)))
            print('~~~~~~~~~~~~~~~~~~~~implicitMultiply~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

        return newDings


    def __intraGrenzeSubtreeUe(self, newDings):
        """
        This method only deals with infixes
        """
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
        # ding = newDings[0]
        for ding in newDings:
            # import pdb;pdb.set_trace()
            treeifiedDingsGanzStartPos = getMostLeftStartPos(ding, treeifiedDingsGanzStartPos)
            treeifiedDingsGanzEndPos = getMostRightEndPos(ding, treeifiedDingsGanzEndPos)

        #TODO please refactor the above, damn confusing...
        ############
        # if self.showError():
        #     print('checking treeifiedDingsGanzStartPos/treeifiedDingsGanzEndPos')
        #     print('dings', list(map(lambda d: (d['name'], d['startPos'], d['endPos']), newDings)))
        #     print('ding', ((ding['name'], ding['startPos'], ding['endPos'])))
        #     print('treeifiedDingsGanzStartPos', treeifiedDingsGanzStartPos)
        #     print('treeifiedDingsGanzEndPos', treeifiedDingsGanzEndPos)
        #     print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            # import pdb;pdb.set_trace()
        ############
        # treeifiedDingsGanzStartPos = getMostLeftStartPos(ding, treeifiedDingsGanzStartPos)
        # treeifiedDingsGanzEndPos = getMostRightEndPos(ding, treeifiedDingsGanzEndPos)
        ############
        # if self.showError():
        #     print('checking treeifiedDingsGanzStartPos/treeifiedDingsGanzEndPos')
        #     print('dings', list(map(lambda d: (d['name'], d['startPos'], d['endPos']), newDings)))
        #     print('ding', ((ding['name'], ding['startPos'], ding['endPos'])))
        #     print('treeifiedDingsGanzStartPos', treeifiedDingsGanzStartPos)
        #     print('treeifiedDingsGanzEndPos', treeifiedDingsGanzEndPos)
        #     print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!2!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            # import pdb;pdb.set_trace()
        ############

        #here with deal with the tree growing.
        if len(newDings) > 1:
            #TODO refactor helper function
            def findTightestBracketEnclosingMostArgs(enclosingBracketInfoDicts, ganzRangeOfRemainingArgs):
                """
                But we can only have 1 tightest.... because each bracket is id by position,.....
                GO by TIGHTEST, then 
                Then by most number of args<<<<<<<<<<<<seems like this is rubbish
                """
                tightest = enclosingBracketInfoDicts[0]
                for bracketInfoDict in enclosingBracketInfoDicts:
                    if tightest['enclosingStartPos'] <= bracketInfoDict['enclosingStartPos'] and bracketInfoDict['enclosingEndPos'] <= tightest['enclosingEndPos']:
                        tightest = bracketInfoDict
                return tightest


                #this was most-number-of-args, then tightest
                # mostArgsCount = 0
                # mostArgsBracketList = []
                # for bracketInfoDict in enclosingBracketInfoDicts:
                #     """
                #     bracketInfoDict:
                #     {'enclosingStartPos': 7, 'enclosingEndPos': 15, 'enclosingStartType': '{', 'enclosingEndType': '}'}
                #     """
                #     numberOfArgsEnclosed = 0
                #     for ganzTuple in ganzRangeOfRemainingArgs:
                #         """
                #         ganzTuple:
                #         (8, 9)
                #         """
                #         if bracketInfoDict['enclosingStartPos'] <= ganzTuple[0] and ganzTuple[1] <= bracketInfoDict['enclosingEndPos']:
                #             numberOfArgsEnclosed += 1
                #     if mostArgsCount == numberOfArgsEnclosed:
                #         mostArgsBracketList.append(bracketInfoDict)
                #     elif numberOfArgsEnclosed > mostArgsCount:
                #         mostArgsCount = numberOfArgsEnclosed
                #         mostArgsBracketList = [bracketInfoDict]
                # tightest = mostArgsBracketList[0]
                # for bracketInfoDict in mostArgsBracketList:
                #     if tightest['enclosingStartPos'] <= bracketInfoDict['enclosingStartPos'] and bracketInfoDict['enclosingEndPos'] <= tightest['enclosingEndPos']:
                #         tightest = bracketInfoDict
                # return tightest




            import copy
            #find all the infixesPos, we only need to deal with infixes here...
            parentChildInformation = [] # collect all the information here first. fill out the form later
            infixPoss = []
            leftRightPossToSkip = []
            enclosingPossForFirst = []
            possToGanzRange = {} # for checking which enclosingInfix contains the least number of args
            for idx, ding in enumerate(newDings):
                possToGanzRange[idx] = (ding['ganzStartPos'], ding['ganzEndPos'])
                #if ding['type'] == 'infix':# implicit-multiply type is 'implicit' and not 'infix'
                if ding['name'] in Latexparser.PRIOIRITIZED_INFIX:
                    infixPoss.append(idx)
                    if len(list(filter(lambda bracketInfoDict: not bracketInfoDict['belongToBackslash'], ding['enclosingBracketsNonBackslashArg']))) > 0:# remove all the enclosing, that belongs to backSLash TODO BAD NAMING enclosingBrackets, not enclosingBRacketsNonBackslashArg
                        enclosingPossForFirst.append(idx)
                    elif ding['left__type'] == 'leftRight' or ding['right__type'] == 'leftRight':
                        leftRightPossToSkip.append(idx)
                        


            if self.showError():
                print('__intraGrenzeSubtreeUe')
                print('newDings', list(map(lambda d: (d['name'], d['startPos'], d['endPos']), newDings)))


            processed = set() # more for args

            if self.showError():
                #######################################
                print('BEFORE relationship building~~~~~~~~~~~~~~~~~~~~')
                print('infixPoss: ')
                print(list(map(lambda infixPos: (newDings[infixPos]['name'], newDings[infixPos]['startPos'], newDings[infixPos]['endPos']), infixPoss)))
                print('enclosingPossForFirst: ')
                print(list(map(lambda infixPos: (newDings[infixPos]['name'], newDings[infixPos]['startPos'], newDings[infixPos]['endPos']), enclosingPossForFirst)))
                print('leftRightPossToSkip: ')
                print(list(map(lambda infixPos: (newDings[infixPos]['name'], newDings[infixPos]['startPos'], newDings[infixPos]['endPos']), leftRightPossToSkip)))
                #######################################

            #begin processing the infixes with enclosing brackets
            remainingEnclosingPoss = copy.deepcopy(enclosingPossForFirst)
            while len(remainingEnclosingPoss) > 0:
                bracketToPos = {}
                #deal with enclosingInfixPoss first
                for infixPos in remainingEnclosingPoss:# you are going to popout the infixes.... so
                    #figure out which infix to build parent/child relationship first.
                    #need to take out the one
                    # 1. containing least args  - needs to be done on the fly, the args available will keep changing
                    # 2. by BODMAS
                    # then put in to infixPos
                    remainingArgPoss = set(possToGanzRange.keys()) - set([infixPos]) - set(processed)
                    ganzRangeOfRemainingArgs = []
                    for remainingArgPos in remainingArgPoss:
                        ding = newDings[remainingArgPos]
                        ganzRangeOfRemainingArgs.append((ding['ganzStartPos'], ding['ganzEndPos']))
                    tightestBracketEnclosingMostArgs = findTightestBracketEnclosingMostArgs(newDings[infixPos]['enclosingBracketsNonBackslashArg'], ganzRangeOfRemainingArgs)
                    bracketPosTuple = (tightestBracketEnclosingMostArgs['enclosingStartPos'], tightestBracketEnclosingMostArgs['enclosingEndPos']) # cannot be used as key, because some infix share the same tightest brackets
                    existing = bracketToPos.get(bracketPosTuple, [])
                    existing.append(infixPos)
                    bracketToPos[bracketPosTuple] = existing

                listOfPoss = list(bracketToPos.keys())
                def firstContainsSecond(arg1, arg2):
                    return arg1[0] <= arg2[0] and arg2[1] <= arg1[1]
                def getId(bracket): # Id has to be hashable
                    return tuple(bracketToPos[bracket])
                # import pdb;pdb.set_trace()
                roots, leaves, enclosureTree, levelToIDs, idToLevel = EnclosureTree.makeEnclosureTreeWithLevelRootLeaves(listOfPoss, firstContainsSecond, getId)

                #################
                if self.showError():
                    import pprint
                    pp = pprint.PrettyPrinter(indent=4)
                    print('*******************************')
                    print('input: listOfPoss to infixKeys')
                    print(list(map(lambda bracket: getId(bracket), listOfPoss)))
                    print('enclosureTree:::')
                    pp.pprint(enclosureTree)
                    print('levelToIDs')
                    pp.pprint(levelToIDs)
                    print('mapped levelToIDs:')
                    mappedLevels = {}
                    for level, infixPussLists in sorted(list(levelToIDs.items()), key=lambda t: t[0]):
                        ddl = []
                        for infixPussList in infixPussLists:
                            for infixPuss in infixPussList:
                                dd = newDings[infixPuss]
                                ddl.append((dd['name'], dd['startPos']))
                        mappedLevels[level] = ddl
                    pp.pprint(mappedLevels)
                    print('idToLevel')
                    pp.pprint(idToLevel)
                    print('*******************************')
                #################
                #flatten each 
                mappedLevels = {}
                for level, infixPussLists in sorted(list(levelToIDs.items()), key=lambda t: t[0]):
                    ddl = []
                    for infixPussList in infixPussLists:
                        for infixPuss in infixPussList:
                            # dd = newDings[infixPuss]
                            # ddl.append((dd['name'], dd['startPos']))
                            ddl.append(infixPuss)
                    mappedLevels[level] = ddl
                level, IDs = sorted(mappedLevels.items(), key=lambda kvtup: kvtup[0], reverse=True)[0] # lowest level has the biggest number

                # for level, IDs in sorted(levelToIDs.items(), key=lambda kvtup: kvtup[0]): # go by the lowest level
                infixesWithPos = list(map(lambda ID: (ID, newDings[ID]), IDs))
                # for infixPos, infix in sorted(infixesWithPos, key=lambda infixWithPos: Latexparser.PRIOIRITIZED_INFIX[infixWithPos[1]['name']]): # then go by BODMAS
                # import pdb;pdb.set_trace()
                infixPos, infix = sorted(infixesWithPos, key=lambda infixWithPos: Latexparser.PRIOIRITIZED_INFIX.index(infixWithPos[1]['name']))[0]# then go by BODMAS
                #and only process 1 infix, then we re-calculate the whole thing, (TODO is it ok to do the whole level?)

                # infix = newDings[infixPos]
                #get left and right args of infix
                #find ding-to-the-right-of-infix, thats not processed.
                for idx in range(infixPos+1, len(newDings)): #infixPos+1 is to skip infixPos itself
                    if idx in processed:
                        continue
                    dingToRightIdx = idx
                    break
                #find ding-to-the-left-infix, thats not processed.
                for idx in range(infixPos-1, -1, -1):
                    if idx in processed:
                        continue
                    dingToLeftIdx = idx
                    break

                # if self.showError():
                #     import pdb;pdb.set_trace()
                parentChildInformation.append((dingToLeftIdx, infixPos, dingToRightIdx))
                processed.add(dingToLeftIdx)
                processed.add(dingToRightIdx)

                remainingEnclosingPoss = list(set(remainingEnclosingPoss) - set([infixPos])) # take out the infixPos that was processed
                #remove dingToLeftIdx and dingToRightIdx from possToGanzRange
                if dingToLeftIdx in possToGanzRange:
                    del possToGanzRange[dingToLeftIdx]
                if dingToRightIdx in possToGanzRange:
                    del possToGanzRange[dingToRightIdx]
                if self.showError():
                    #######################################
                    print('IN ENCLOSING~~~~~~~~~~~~~~~~~~~~, just processed: ', infixPos)
                    print('remainingEnclosingPoss:')
                    print(remainingEnclosingPoss)
                    print('processed: ')
                    print(processed)
                    print('parentChildInformation: ')
                    print(parentChildInformation)
                    print('just processed: ***')
                    leftDing = newDings[dingToLeftIdx]
                    rightDing = newDings[dingToRightIdx]
                    print((leftDing['name'], leftDing['startPos'], leftDing['endPos']))
                    print((infix['name'], infix['startPos'], infix['endPos']))
                    print((rightDing['name'], rightDing['startPos'], rightDing['endPos']))
                    #######################################

            if self.showError():
                #######################################
                print('lists CHECKS~~~~~~~~~~~~~~~~~~~~')
                print('infixPoss: ')
                print(list(map(lambda infixPos: (newDings[infixPos]['name'], newDings[infixPos]['startPos'], newDings[infixPos]['endPos']), infixPoss)))
                print('enclosingPossForFirst: ')
                print(list(map(lambda infixPos: (newDings[infixPos]['name'], newDings[infixPos]['startPos'], newDings[infixPos]['endPos']), enclosingPossForFirst)))
                print('leftRightPossToSkip: ')
                print(list(map(lambda infixPos: (newDings[infixPos]['name'], newDings[infixPos]['startPos'], newDings[infixPos]['endPos']), leftRightPossToSkip)))
                #######################################

            #process NonEnclosing NonleftRight Infix
            otherNonEnclosingNonLeftRightPoss = list((set(infixPoss) - set(enclosingPossForFirst)) - set(leftRightPossToSkip))
            # import pdb;pdb.set_trace()
            otherNonEnclosingNonLeftRightPoss = sorted(otherNonEnclosingNonLeftRightPoss, key=lambda infixPos: Latexparser.PRIOIRITIZED_INFIX.index(newDings[infixPos]['name'])) # shuold not throw, if throw, developer please update Latexparser.PRIOIRITIZED_INFIX
            for infixPos in otherNonEnclosingNonLeftRightPoss:
                infix = newDings[infixPos]
                #get left and right args of infix
                #find ding-to-the-right-of-infix, thats not processed.
                for idx in range(infixPos+1, len(newDings)): #infixPos+1 is to skip infixPos itself
                    if idx in processed:
                        continue
                    dingToRightIdx = idx
                    break
                #find ding-to-the-left-infix, thats not processed.
                for idx in range(infixPos-1, -1, -1):
                    if idx in processed:
                        continue
                    dingToLeftIdx = idx
                    break

                parentChildInformation.append((dingToLeftIdx, infixPos, dingToRightIdx))
                processed.add(dingToLeftIdx)
                processed.add(dingToRightIdx)
                    
                if self.showError():
                    #######################################
                    print('IN NONENCLOSING NONLEFTRIGHT~~~~~~~~~~~~~~~~~~~~')
                    print('processed: ')
                    print(processed)
                    print('parentChildInformation: ')
                    print(parentChildInformation)
                    print('just processed: ***')
                    leftDing = newDings[dingToLeftIdx]
                    rightDing = newDings[dingToRightIdx]
                    print((leftDing['name'], leftDing['startPos'], leftDing['endPos']))
                    print((infix['name'], infix['startPos'], infix['endPos']))
                    print((rightDing['name'], rightDing['startPos'], rightDing['endPos']))
                    #######################################
                    # import pdb;pdb.set_trace()


            #Lastly process the LeftRight infixes
            leftRightInfixPoss = sorted(leftRightPossToSkip, key=lambda infixPos: Latexparser.PRIOIRITIZED_INFIX.index(newDings[infixPos]['name']))
            for infixPos in leftRightInfixPoss:
                infix = newDings[infixPos]
                #get left and right args of infix
                #find ding-to-the-right-of-infix, thats not processed.
                for idx in range(infixPos+1, len(newDings)): #infixPos+1 is to skip infixPos itself
                    if idx in processed:
                        continue
                    dingToRightIdx = idx
                    break
                #find ding-to-the-left-infix, thats not processed.
                for idx in range(infixPos-1, -1, -1):
                    if idx in processed:
                        continue
                    dingToLeftIdx = idx
                    break
                if self.showError():
                    #######################################
                    print('IN LEFTRIGHT~~~~~~~~~~~~~~~~~~~~')
                    print('processed: ')
                    print(processed)
                    print('parentChildInformation: ')
                    print(parentChildInformation)
                    print('just processed: ***')
                    leftDing = newDings[dingToLeftIdx]
                    rightDing = newDings[dingToRightIdx]
                    print((leftDing['name'], leftDing['startPos'], leftDing['endPos']))
                    print((infix['name'], infix['startPos'], infix['endPos']))
                    print((rightDing['name'], rightDing['startPos'], rightDing['endPos']))
                    #######################################
                    # import pdb;pdb.set_trace()

                parentChildInformation.append((dingToLeftIdx, infixPos, dingToRightIdx))
                processed.add(dingToLeftIdx)
                processed.add(dingToRightIdx)


            #fill out the parentChildInformation
            for leftDingPos, dingPos, rightDingPos in parentChildInformation:
                leftDing = newDings[leftDingPos]
                ding = newDings[dingPos]
                rightDing = newDings[rightDingPos]
                #form filling
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
            print('checking treeifiedDingsGanzStartPos/treeifiedDingsGanzEndPos')
            print('dings', list(map(lambda d: (d['name'], d['startPos'], d['endPos']), newDings)))
            print('ding', ((ding['name'], ding['startPos'], ding['endPos'])))
            # print('treeifiedDingsGanzStartPos', treeifiedDingsGanzStartPos)
            # print('treeifiedDingsGanzEndPos', treeifiedDingsGanzEndPos)
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
        return {'root':ding, 'ganzStartPos':treeifiedDingsGanzStartPos, 'ganzEndPos':treeifiedDingsGanzEndPos}, newDings


    def __interLevelSubtreeGrafting(self, rootSubTree, parentDings):
        """
        each key in newConsecutiveGroups is a level,
        and during the 2nd part of _addImplicitMultiply
        we build parent-child-relationship within each level

        Here, we build parent-child-relationship across levels.
        So, after this step, we should only have 2-subtrees with no parents
        Those 2 are the direct children of '='


        parentDings are all the potential parents
        rootSubTree is the child look for a potential parent
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
                print('parentDings:::: potentialParents')
                pp.pprint(sadchild)
                print('rootSubTree:::child looking for a potentialParent')
                print(rootSubTree)
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
        # self.nodeId = 1
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
        self.nodeId = 1 # 0 is for =, for _parse, TODO
        self._findInfixAndEnclosingBrackets()
        self._findBackSlashPositions()
        self._tagBracketsToBackslash()
        self._updateInfixNearestBracketInfix()
        self._removeCaretThatIsNotExponent()
        self._findLeftOverPosition()
        self._contiguousLeftOvers()
        self._collateBackslashInfixLeftOversToContiguous()
        self._updateBackslashLeftOversBracketInfo()
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