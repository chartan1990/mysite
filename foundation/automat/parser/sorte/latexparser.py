import multiprocessing as mp # TODO for Django, we might need to re-int  Django

from foundation.automat.common import findAllMatches, isNum, lenOrZero
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
    PRIOIRITIZED_INFIX = ['^', '/', '*', '-', '+'] # the smaller the number the higher the priority
    INFIX = PRIOIRITIZED_INFIX+['=']
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
        self.equalPos = self._eqs.index('=') # will explode if no equals :)
        #maybe set all EVENT to false(clear()) before parsing, then
        #dump each "method" as processes into Pool
        #each method will have a .wait() for the oMethod/s, its waiting for
        #oMethod/s that complete will call set(), signalling method (waiting for oMethod) to start. :)
        self.event__findVariablesFunctionsPositions = mp.Event()
        self.event__findInfixAndEnclosingBrackets = mp.Event()
        self.event__removeCaretThatIsNotExponent = mp.Event()
        self.event__varFindVarChildren = mp.Event()
        self.event__funcFindFuncChildren = mp.Event()
        self.event__infixFindInfixChildren = mp.Event()
        self.event__infixFuncVarLeftoversCrossFindChildren = mp.Event()
        self.event__findLeftOverPosition = mp.Event()
        self.event__contiguousLeftOvers = mp.Event()
        self.event__addChildOnMinusInfixWithNoLeftArg = mp.Event()
        self.event__addImplicitMultipy = mp.Event()


    def _findVariablesFunctionsPositions(self):
        """
        THE BACKSLASH FINDER! TODO rename this method, damn-confusing.

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
        if self.verbose:
            print('lock__findVariablesFunctionsPositions IS AQCUIRED')
        self.variablesPos = [] # name, startPos, endPos, | argument1, argument1StartPosition, argument1EndPosition, argumentBracketType
        self.functionPos = [] # functionName, startPos, endPos, _, ^, arguments, TODO rename to functionsPos
        self.noBraBackslashPos = [] # are variables, but no brackets

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
                        closingSquareBracketPos = self._eqs.index(']', argument1StartPosition)
                        argument1 = self._eqs[argument1StartPosition:closingSquareBracketPos] # argument1 == rootpower
                        argument1EndPosition = closingSquareBracketPos
                        argument1BracketType = '['
                        nextPos = argument1EndPosition + 1 #because of the ]
                    else:
                        argument1StartPosition = positionTuple[1]#None
                        argument1 = 2 # default rootpower is square root
                        argument1EndPosition = positionTuple[1]#None
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
                        argument1SubSuperType = '^'
                        argument1SubSuperPos = positionTuple[1]
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
                    else: # will lead to ugly AST, TODO need to simplify AST later to get rid of (^ sin 1)
                        argument1SubSuperType = None
                        argument1SubSuperPos = None
                        argument1StartPosition = -1
                        argument1EndPosition = -1
                        argument1 = "1"
                        argument1BracketType = None
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
                    argument1StartPosition = -1
                    argument1 = 'e' # defintion of natural log
                    argument1EndPosition = -1
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
                        argument1SubSuperType = '_'
                        argument1SubSuperPos = positionTuple[1]
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
                        argument1StartPosition = -1
                        argument1EndPosition = -1
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
                    'startPos':positionTuple[0], # of the label not the whole ding
                    'endPos':positionTuple[1], # of the label not the whole ding
                    'position':positionTuple[0],###TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
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
                    'ganzEndPos':max((argument1EndPosition if argument1EndPosition is not None else -1) + (len(argument1BracketType) if argument1BracketType is not None else 0), 
                (argument2EndPosition if argument2EndPosition is not None else -1) + (len(argument2BracketType) if argument2BracketType is not None else 0),
                positionTuple[1]),
                    'type':'backslash_function',
                    'child':{1:None, 2:None},
                    'parent':None
                })
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

        if self.verbose:
            print('lock__findVariablesFunctionsPositions IS RELEASED')
        self.event__findVariablesFunctionsPositions.set() # Trigger the event to notify the waiting process


    def _findInfixAndEnclosingBrackets(self):
        #find all the positions of the infixes, and if there are round/square/curly brackets beside them...
        self.openBracketsLocation = dict(map(lambda openBracket: (openBracket, []), Latexparser.OPEN_BRACKETS))
        self.matchingBracketsLocation = []
        self.infixOperatorPositions = {}#dict(map(lambda infixOp: (infixOp, []), Latexparser.INFIX))
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
                existingList = self.infixOperatorPositions.get(c, [])
                existingList.append({
                    'position':idx,
                    #'leftCloseBracket':self._eqs[idx-1] if idx>0 and (self._eqs[idx-1] in Latexparser.CLOSE_BRACKETS) else None,
                    #'rightOpenBracket':self._eqs[idx+1] if idx<len(self._eqs)-2 and (self._eqs[idx+1] in Latexparser.OPEN_BRACKETS) else None
                })
                self.infixOperatorPositions[c] = existingList
        #check for error, if there are any left-over brackets in any of the stacks, then there is unbalanced brackets
        mismatchedOpenBrackets = []
        for openBracket, bracketPosStack in self.openBracketsLocation.items():
            if len(bracketPosStack) > 0:
                mismatchedOpenBrackets.append(openBracket)
        if len(mismatchedOpenBrackets) > 0:
            raise Exception(f'Mismatched brackets: {mismatchedOpenBrackets}')
        ###########
        #check if the bracket belongs to fBackslash/vBackslash
        def collideWithBackslashBrackets(startBracketPos):
            for vInfoDict in self.variablesPos:
                if vInfoDict['argument1StartPosition'] is not None and startBracketPos == vInfoDict['argument1StartPosition'] - lenOrZero(vInfoDict['argument1BracketType']):
                    return True
            for fInfoDict in self.functionPos:
                if fInfoDict['argument1StartPosition'] is not None and startBracketPos == fInfoDict['argument1StartPosition'] - lenOrZero(fInfoDict['argument1BracketType']):
                    return True
                if fInfoDict['argument2StartPosition'] is not None and startBracketPos == fInfoDict['argument2StartPosition'] - lenOrZero(fInfoDict['argument2BracketType']):
                    return True
            return False
        ###########
        self.listOfInfixInfoDict = []
        for infixOp, infoDictList in self.infixOperatorPositions.items():
            if infixOp == '=':
                continue # '=' does not belong here
            if self.verbose:
                print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<looking at infix: ', infixOp)
                # import pdb;pdb.set_trace()
            for infoDict in infoDictList:
                #find left_bracket_positions (if any), find right_bracket_positions (if any), find tightest enclosing brackets, if any
                newInfoDict = {
                    'name': infixOp, 'position':infoDict['position'], 'type':'infix', 'child':{1:None, 2:None},'parent':None,

                    'left__startBracketPos':-1 if infoDict['position'] < self.equalPos else self.equalPos + 1,  # for easy comparison, will be removed, if nothing is found
                    'left__startBracketType':None,
                    'left__endBracketPos':None,
                    'left__endBracketType':None,
                    'left__argStart':None,
                    'left__argEnd':None,
                    'left__type':None, # enclosing

                    'right__startBracketPos':len(self._eqs) if infoDict['position'] > self.equalPos else self.equalPos - 1, # for easy comparison, will be removed if nothing is found
                    'right__startBracketType':None,
                    'right__endBracketPos':None,
                    'right__endBracketType':None,
                    'right__argStart':None,
                    'right__argEnd':None,
                    'right__type':None, #enclosing
                }
                """
                # TODO binarySearch with sorted matchingBracketsLocations, may be faster with more brackets... EXPERIMENT: two different sets of code, find parametrised "Sweet Spot" to swap between code...
                https://en.wikipedia.org/wiki/Segment_tree
                #copy and paste:
                https://www.geeksforgeeks.org/segment-tree-efficient-implementation/
                """
                for infoDictMatchingBracketLoc in self.matchingBracketsLocation: 
                    #for finding tightest enclosing brackets, these might be brackets of backslash args and thats ok
                    if self.verbose:
                        print(infoDictMatchingBracketLoc, '>>>>>>>>>>>>>>>>')
                    if infoDictMatchingBracketLoc['startPos'] <= infoDict['position'] and infoDict['position'] <= infoDictMatchingBracketLoc['endPos']: # is enclosed by infoDictMatchingBracketLoc
                        if newInfoDict['left__startBracketPos'] <= infoDictMatchingBracketLoc['startPos'] and infoDictMatchingBracketLoc['endPos'] <= newInfoDict['right__startBracketPos']: #is a tighter bracket, then recorded on currentEnclosingBracketPos
                            
                            if self.verbose:
                                print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<found tight enclosing brackets')
                            newInfoDict['left__startBracketPos'] = infoDictMatchingBracketLoc['startPos']
                            newInfoDict['right__startBracketPos'] = infoDictMatchingBracketLoc['endPos']
                            newInfoDict['left__startBracketType'] = infoDictMatchingBracketLoc['openBracketType']
                            newInfoDict['right__startBracketType'] = self.open__close[infoDictMatchingBracketLoc['openBracketType']]
                            newInfoDict['left__argStart'] = infoDictMatchingBracketLoc['startPos'] + len(infoDictMatchingBracketLoc['openBracketType'])
                            newInfoDict['left__argEnd'] = infoDict['position'] - len(infixOp) # this is enclosing brackets, we assume no left/right brackets...
                            newInfoDict['right__argStart'] = infoDict['position'] + len(infixOp) # this is enclosing brackets, we assume, no left/right brackets...
                            newInfoDict['right__argEnd'] = infoDictMatchingBracketLoc['endPos'] - len(self.open__close[infoDictMatchingBracketLoc['openBracketType']])
                            newInfoDict['left__type'] = 'enclosing'
                            newInfoDict['right__type'] = 'enclosing'
                    #if there are no enclosing brackets.... have to take the nearest infixOpPos....
                #update newInfixOperatorPositions
                #TODO if no enclosing brackets, then right/left bracket
                #############
                if self.verbose:
                    print('JUST AFTER SEARCHING FOR ENCLOSING BRACKETS')
                #############
                if newInfoDict['left__startBracketType'] is None: #no enclosing bracket (startSymbol, endSymbol are set together)
                    if self.verbose:
                        print('NO ENCLOSING, looking for leftRight')
                    #find brackets to the left
                    newInfoDict.update({
                        'left__startBracketPos':-1, 
                        'left__startBracketType':None,
                        'left__endBracketPos':-1,
                        'left__endBracketType':None,
                        'left__argStart':None,
                        'left__argEnd':None,
                        'left__type':None, # enclosing
                    })
                    for infoDictMatchingBracketLoc in self.matchingBracketsLocation:
                        if not collideWithBackslashBrackets(infoDictMatchingBracketLoc['startPos']) and infoDictMatchingBracketLoc['endPos'] < infoDict['position']: # we got a left bracket thats not a backslash argument
                            if newInfoDict['left__endBracketPos'] < infoDictMatchingBracketLoc['endPos']: #find the closest left bracket
                                
                                if self.verbose:
                                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<found closest left bracket')
                                newInfoDict['left__startBracketPos'] = infoDictMatchingBracketLoc['startPos']
                                newInfoDict['left__endBracketPos'] = infoDictMatchingBracketLoc['endPos']
                                newInfoDict['left__startBracketType'] = infoDictMatchingBracketLoc['openBracketType']
                                newInfoDict['left__endBracketType'] = open__close[infoDictMatchingBracketLoc['openBracketType']]
                                newInfoDict['left__argStart'] = infoDictMatchingBracketLoc['startPos'] + len(infoDictMatchingBracketLoc['openBracketType'])
                                newInfoDict['left__argEnd'] = infoDictMatchingBracketLoc['endPos'] - len(open__close[infoDictMatchingBracketLoc['openBracketType']])
                                newInfoDict['left__type'] = 'leftRight'
                    if newInfoDict['left__startBracketType'] is None:#no left start bracket
                        #find nearest infix to the left
                        def sameSideAsInfoDict(newInfoDict):
                            if infoDict['position'] < self.equalPos:
                                return newInfoDict['position'] < self.equalPos
                            else:
                                return newInfoDict['position'] > self.equalPos
                        for infixOp0, infoDictList0 in self.infixOperatorPositions.items():
                            for infoDict0 in infoDictList0:
                                if sameSideAsInfoDict(infoDict0) and infoDict0['position'] < infoDict['position']:# must be on the same side of the '=' as infoDict, and left of infoDict
                                    #found a left infix
                                    if self.verbose:
                                        print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<found closest left infx')
                                        # import pdb;pdb.set_trace()
                                    #is infoDict0 nearer than newInfoDict?
                                    if newInfoDict['left__startBracketPos'] < infoDict0['position']:
                                        newInfoDict['left__startBracketPos'] = infoDict0['position']
                                        newInfoDict['left__startBracketType'] = infixOp0#infoDict0['name']
                                        newInfoDict['left__endBracketPos'] = infoDict0['position'] + len(infixOp0)
                                        newInfoDict['left__endBracketType'] = infixOp0#infoDict0['name']
                                        newInfoDict['left__argStart'] = infoDict0['position'] + len(infixOp0)
                                        newInfoDict['left__argEnd'] = infoDict['position'] - len(infixOp)
                                        newInfoDict['left__type'] = 'infix'
                        if newInfoDict['left__startBracketType'] is None:#no left neighbouring infix
                            #still must have left__argStart and left__argEnd, note that '-' has a special case, wie "-ab=-ba", where the len(leftArg) = 0 and leftArg=0...TODO
                            #...+...=  (position < equalPos)
                            #=...+...  (position > equalPos)
                            
                            if self.verbose:
                                print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<no left neighbouring infix')
                            newInfoDict['left__argStart'] = 0 if infoDict['position'] < self.equalPos else self.equalPos + 1 # everything to the left of infoDict
                            newInfoDict['left__argEnd'] = infoDict['position'] - 1 if infoDict['position'] < self.equalPos else self.equalPos
                            newInfoDict['left__type'] = 'arg'

                    #find brackets to the right
                    newInfoDict.update({
                        'right__startBracketPos':-1,
                        'right__startBracketType':None,
                        'right__endBracketPos':-1,
                        'right__endBracketType':None,
                        'right__argStart':None,
                        'right__argEnd':None,
                        'right__type':None, #enclosing
                    })
                    for infoDictMatchingBracketLoc in self.matchingBracketsLocation:
                        if not collideWithBackslashBrackets(infoDictMatchingBracketLoc['startPos']) and infoDictMatchingBracketLoc['startPos'] > infoDict['position']: # we got a right bracket
                            if newInfoDict['startPos'] > infoDictMatchingBracketLoc['endPos']:#find the closest right bracket
                                
                                if self.verbose:
                                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<found closest right bracket')
                                newInfoDict['right__startBracketPos'] = infoDictMatchingBracketLoc['startPos']
                                newInfoDict['right__endBracketPos'] = infoDictMatchingBracketLoc['endPos']
                                newInfoDict['right__startBracketType'] = infoDictMatchingBracketLoc['openBracketType']
                                newInfoDict['right__endBracketType'] = open__close[infoDictMatchingBracketLoc['openBracketType']]
                                newInfoDict['right__argStart'] = infoDictMatchingBracketLoc['startPos'] + len(infoDictMatchingBracketLoc['openBracketType'])
                                newInfoDict['right__argEnd'] = infoDictMatchingBracketLoc['endPos'] - len(open__close[infoDictMatchingBracketLoc['openBracketType']])
                                newInfoDict['right__type'] = 'leftRight'
                    if newInfoDict['right__startBracketType'] is None:#no right bracket
                        #find nearest infix to the left
                        def sameSideAsInfoDict(newInfoDict):
                            if infoDict['position'] < self.equalPos:
                                return newInfoDict['position'] < self.equalPos
                            else:
                                return newInfoDict['position'] > self.equalPos
                        for infixOp0, infoDictList0 in self.infixOperatorPositions.items():
                            for infoDict0 in infoDictList0:
                                if sameSideAsInfoDict(infoDict0) and infoDict0['position'] < infoDict['position']:# must be on the same side of the '=' as infoDict, and left of infoDict
                                    
                                    if self.verbose:
                                        print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<found closest right infix')
                                    if infoDict0['position'] < newInfoDict['right__startBracketPos']:
                                        newInfoDict['right__startBracketPos'] = infoDict0['position']
                                        newInfoDict['right__startBracketType'] = infixOp0
                                        newInfoDict['right__endBracketPos'] = infoDict0['position'] + len(infixOp0)
                                        newInfoDict['right__endBracketType'] = infixOp0
                                        newInfoDict['right__argStart'] = infoDict['position'] + len(infixOp)
                                        newInfoDict['right__argEnd'] = infoDict0['position'] - len(infixOp0)
                                        newInfoDict['right__type'] = 'infix'
                        if newInfoDict['right__startBracketType'] is None:#no right neighbouring infix
                            #still must have right__argStart and right__argEnd, note that '-' has a special case, wie "-ab=-ba", where the len(leftArg) = 0 and leftArg=0...TODO
                            #...+...=  (position < equalPos)
                            #=...+...  (position > equalPos)
                            
                            if self.verbose:
                                print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<no right neighbouring infix')
                            newInfoDict['right__argStart'] = infoDict['position'] + 1 
                            newInfoDict['right__argEnd'] = self.equalPos if infoDict['position'] < self.equalPos else len(self._eqs)
                            newInfoDict['right__type'] = 'arg'
                #
                #for '-', there is a special case, like '-ab=-ba'
                #also, we can have "a+b=b+a", no brackets, no neighbouring infixes, but still, there are arguments...
                if newInfoDict['left__startBracketType'] is None:
                    newInfoDict['left__startBracketPos'] = None
                if newInfoDict['right__startBracketType'] is None:
                    newInfoDict['right__startBracketPos'] = None
                if newInfoDict['right__type'] == 'enclosing':
                    newInfoDict['startPos'] = newInfoDict['left__startBracketPos']
                    newInfoDict['ganzStartPos'] = newInfoDict['left__startBracketPos']
                    newInfoDict['endPos'] = newInfoDict['right__endBracketPos']
                    newInfoDict['ganzEndPos'] = newInfoDict['right__endBracketPos']
                if newInfoDict['left__type'] == 'leftRight':
                    newInfoDict['startPos'] = newInfoDict['left__startBracketPos']
                    newInfoDict['ganzStartPos'] = newInfoDict['left__startBracketPos']

                if newInfoDict['right__type'] == 'leftRight':
                    newInfoDict['endPos'] = newInfoDict['right__endBracketPos']
                    newInfoDict['ganzEndPos'] = newInfoDict['right__endBracketPos']

                if newInfoDict['left__type'] == 'infix':
                    newInfoDict['startPos'] = newInfoDict['left__argStart']
                    newInfoDict['ganzStartPos'] = newInfoDict['left__argStart']

                if newInfoDict['right__type'] == 'infix':
                    newInfoDict['endPos'] = newInfoDict['right__argEnd']
                    newInfoDict['ganzEndPos'] = newInfoDict['right__argEnd']

                if newInfoDict['left__type'] == 'arg':
                    newInfoDict['startPos'] = newInfoDict['left__argStart']
                    newInfoDict['ganzStartPos'] = newInfoDict['left__argStart']
                if newInfoDict['right__type'] == 'arg':
                    newInfoDict['endPos'] = newInfoDict['right__argEnd']
                    newInfoDict['ganzEndPos'] = newInfoDict['right__argEnd']
                self.listOfInfixInfoDict.append(newInfoDict)
        self.event__findInfixAndEnclosingBrackets.set()


    def _removeCaretThatIsNotExponent(self):
        self.event__findVariablesFunctionsPositions.wait()
        self.event__findInfixAndEnclosingBrackets.wait()
        #^ would have been picked up by "findInfixAndEnclosingBrackets" as infix
        fakeExponents = []
        fakeExponentsQuickCheck = set()
        newListOfInfixInfoDict = []
        for infixInfoDict in self.listOfInfixInfoDict:
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
        if self.verbose:
            print('original newListOfInfixInfoDict<<<<<<<<<<<<<<<<<<<<<<<<<<')
            print(newListOfInfixInfoDict)
            print('<<<<<<<<<<<<<ORIGINAL newListOfInfixInfoDict<<<<<<<<<<<<<')
        ###############
        for infixInfoDict in newListOfInfixInfoDict:
            #match left args of infixInfoDict with fakeExponents
            #match right args of infixInfoDict with fakeExponents
            for fakeExponent in fakeExponents:###TTTTTTTTTTTTTTTTTTTTTTTTTT
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
                        if infixInfoDict0['position'] < infixInfoDict['position'] and (infixInfoDict0['position'], infixInfoDict0['position']+len(infixInfoDict0['name'])) not in fakeExponentsQuickCheck:
                            if nextInfix['left__startBracketPos'] < infoDict0['position']:
                                nextInfix['left__startBracketPos'] = infoDict0['position']
                                nextInfix['left__startBracketType'] = infixOp0#infoDict0['name']
                                nextInfix['left__endBracketPos'] = infoDict0['position'] + len(infixOp0)
                                nextInfix['left__endBracketType'] = infixOp0#infoDict0['name']
                                nextInfix['left__argStart'] = infoDict0['position'] + len(infixOp0)
                                nextInfix['left__argEnd'] = infoDict['position'] - len(infixOp)
                                nextInfix['left__type'] = 'infix'
                                nextInfix['ganzStartPos'] = infoDict0['position'] + len(infixOp0)

                    if nextInfix['left__startBracketType'] is None:#no left neighbouring infix
                        #still must have left__argStart and left__argEnd, note that '-' has a special case, wie "-ab=-ba", where the len(leftArg) = 0 and leftArg=0...TODO
                        #...+...=  (position < equalPos)
                        #=...+...  (position > equalPos)
                        
                        if self.verbose:
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
                        if infixInfoDict0['position'] > infixInfoDict['position'] and (infixInfoDict0['position'], infixInfoDict0['position']+len(infixInfoDict0['name'])) not in fakeExponentsQuickCheck:
                            if infoDict0['position'] < nextInfix['right__startBracketPos']:
                                nextInfix['right__startBracketPos'] = infoDict0['position']
                                nextInfix['right__startBracketType'] = infixOp0
                                nextInfix['right__endBracketPos'] = infoDict0['position'] + len(infixOp0)
                                nextInfix['right__endBracketType'] = infixOp0
                                nextInfix['right__argStart'] = infoDict['position'] + len(infixOp)
                                nextInfix['right__argEnd'] = infoDict0['position'] - len(infixOp0)
                                nextInfix['right__type'] = 'infix'
                                nextInfix['ganzEndPos'] = infoDict0['position'] - len(infixOp0)
                    if nextInfix['right__startBracketType'] is None:#no right neighbouring infix
                        #still must have right__argStart and right__argEnd, note that '-' has a special case, wie "-ab=-ba", where the len(leftArg) = 0 and leftArg=0...TODO
                        #...+...=  (position < equalPos)
                        #=...+...  (position > equalPos)
                        
                        if self.verbose:
                            print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<no right neighbouring infix')
                        nextInfix['right__argStart'] = infixInfoDict['position'] + 1 
                        nextInfix['right__argEnd'] = self.equalPos if infixInfoDict['position'] < self.equalPos else len(self._eqs)
                        nextInfix['ganzEndPos'] = nextInfix['right__argStart']
                        nextInfix['right__type'] = 'arg'
                    infixInfoDict.update(nextInfix)
            # import pdb;pdb.set_trace()
        self.listOfInfixInfoDict = newListOfInfixInfoDict
        if self.verbose:
            print('<<<<<<<<<<<<<<<<<<<REMOVED ALL ^ pretending to be exponent?')
            print(self.listOfInfixInfoDict)
            print('<<<<<<<<<<<<<<<<<<<')
        ###what about infixes, whose left and right are pretending to be exponents? TODO
        self.event__removeCaretThatIsNotExponent.set()


    def _findLeftOverPosition(self):
        self.event__varFindVarChildren.wait()
        self.event__funcFindFuncChildren.wait()
        self.event__infixFindInfixChildren.wait()
        listOfOccupiedRanges = [] # note that ranges should not overlapp
        for vInfoDict in self.noBraBackslashPos:
            listOfOccupiedRanges.append((vInfoDict['startPos'], vInfoDict['endPos']))

        for variableInfoDict in self.variablesPos:
            listOfOccupiedRanges.append((variableInfoDict['startPos'], variableInfoDict['endPos']))
            if variableInfoDict['argument1StartPosition'] is not None: # just take the bracket start and end Pos
                listOfOccupiedRanges.append((variableInfoDict['argument1StartPosition']-len(variableInfoDict['argument1BracketType']), variableInfoDict['argument1StartPosition']))
            if variableInfoDict['argument1EndPosition'] is not None: # just take the bracket start and end Pos
                listOfOccupiedRanges.append((variableInfoDict['argument1EndPosition'], variableInfoDict['argument1EndPosition']+len(variableInfoDict['argument1BracketType'])))
        for functionInfoDict in self.functionPos:
            listOfOccupiedRanges.append((functionInfoDict['startPos'], functionInfoDict['endPos']))
            if functionInfoDict['argument1BracketType'] is not None: # there is opening and closing brackets for argument1
                listOfOccupiedRanges.append((functionInfoDict['argument1StartPosition']-len(functionInfoDict['argument1BracketType']), functionInfoDict['argument1StartPosition']))
                listOfOccupiedRanges.append((functionInfoDict['argument1EndPosition'], functionInfoDict['argument1EndPosition']+len(functionInfoDict['argument1BracketType'])))
            if functionInfoDict['argument2BracketType'] is not None: # there is opening and closing brackets for argument2
                listOfOccupiedRanges.append((functionInfoDict['argument2StartPosition']-len(functionInfoDict['argument2BracketType']), functionInfoDict['argument2StartPosition']))
                listOfOccupiedRanges.append((functionInfoDict['argument2EndPosition'], functionInfoDict['argument2EndPosition']+len(functionInfoDict['argument2BracketType'])))
            if functionInfoDict['argument1SubSuperPos'] is not None: # there is a ^ or _ on argument1
                listOfOccupiedRanges.append((functionInfoDict['argument1SubSuperPos'], functionInfoDict['argument1SubSuperPos']+len(functionInfoDict['argument1SubSuperType'])))
            if functionInfoDict['argument2SubSuperPos'] is not None: # there is a ^ or _ on argument2
                listOfOccupiedRanges.append((functionInfoDict['argument2SubSuperPos'], functionInfoDict['argument2SubSuperPos']+len(functionInfoDict['argument2SubSuperType'])))
        # sortedListOfOccupiedRanges = sorted(listOfOccupiedRanges, key=lambda tup: tup[0]) # TODO sort for binary search

        #self.infixOperatorPositions
        for infixInfoDict in self.listOfInfixInfoDict:
            listOfOccupiedRanges.append((infixInfoDict['position'], infixInfoDict['position']+len(infixInfoDict['name']))) # might have repeats since some 'brackets' are infixes
            if infixInfoDict['left__startBracketType'] is not None:
                listOfOccupiedRanges.append((infixInfoDict['left__startBracketPos'], infixInfoDict['left__startBracketPos']+len(infixInfoDict['left__startBracketType'])))
            if infixInfoDict['left__endBracketType'] is not None: # left__startBracketType is not None =/=> left__endBracketType is not None, since we may have enclosing brackets
                listOfOccupiedRanges.append((infixInfoDict['left__endBracketPos'], infixInfoDict['left__endBracketPos']+len(infixInfoDict['left__endBracketType'])))
            if infixInfoDict['right__startBracketType'] is not None:
                listOfOccupiedRanges.append((infixInfoDict['right__startBracketPos'], infixInfoDict['right__startBracketPos']+len(infixInfoDict['right__startBracketType'])))
            if infixInfoDict['right__endBracketType'] is not None: # right__startBracketType is not None =/=> right__endBracketType is not None, since we may have enclosing brackets
                listOfOccupiedRanges.append((infixInfoDict['right__endBracketPos'], infixInfoDict['right__endBracketPos']+len(infixInfoDict['right__endBracketType'])))
        self.unoccupiedPoss = set()
        for pos in range(0, len(self._eqs)):
            # TODO binary search
            occupied = False 
            for occupiedRange in listOfOccupiedRanges:
                if occupiedRange[0] <= pos and pos < occupiedRange[1]:
                    occupied = True
            if not occupied:
                self.unoccupiedPoss.add(pos)
        self.event__findLeftOverPosition.set()


    def _contiguousLeftOvers(self): # left overs can be part of infix as well...., self.infixOperatorPositions, infix with no enclosing brackets are the top?
        """
        N=>number character
        V=>non-number character

        At the beginning, where we have no previous to compare type with, we just take it was word.
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
        self.event__findLeftOverPosition.wait()
        self.contiguousInfoList = []
        previousIsNume = None
        previousPos = -1
        word = ""
        wordPosRange = [None, None]
        ###############
        if self.verbose:
            print('*************** grouping _contiguousLeftOvers')
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(self.unoccupiedPoss)
            print('***************END grouping _contiguousLeftOvers')
            # import pdb;pdb.set_trace()
        ###############
        for unoccupiedPos in sorted(list(self.unoccupiedPoss)): # start with left-most leftover
            leftOverC = self._eqs[unoccupiedPos]
            isNume = isNum(leftOverC)
            #############
            if self.verbose:
                print('leftOverC: ', leftOverC)
                print("leftOverC not in ['=', ' '] ", " (unoccupiedPos == previousPos+1) ", " previousIsNume is None ", " isNume == previousIsNume ", " (not previousIsNume) and isNume ")
                print(f"""{leftOverC not in ['=', ' ']} and (({(unoccupiedPos == previousPos+1)}) and ({previousIsNume is None} or {isNume == previousIsNume} or {(not previousIsNume) and isNume}))""")
                # import pdb;pdb.set_trace()
            #############
            if leftOverC not in ['=', ' '] and ((unoccupiedPos == previousPos+1) and (previousIsNume is None or (isNume == previousIsNume) or ((not previousIsNume) and isNume))): #contiguous
                word += leftOverC # word coagulation
                if wordPosRange[0] is None:
                    wordPosRange[0] = unoccupiedPos
                else:
                    wordPosRange[1] = unoccupiedPos
            else: # not contiguous
                # we are going to put in, if wordPosRange[1] still None, then its a single char.
                if len(word) > 0:
                    if wordPosRange[1] is None:
                        print(leftOverC)
                        wordPosRange[1] = wordPosRange[0]+1 # for easy array index, python array indexing endPos always plus 1
                    self.contiguousInfoList.append({
                        'name':word, 
                        'startPos':wordPosRange[0],
                        'endPos':wordPosRange[1],
                        'parent':None,
                        'type':'number' if isNum(word) else 'variable',
                        'ganzStartPos':wordPosRange[0],
                        'ganzEndPos':wordPosRange[1],
                        'position':wordPosRange[0]#this is for building AST's convienence
                    })#, 'parentsInfo':self.wordLowestBackSlashArgumentParents}) # 
                if leftOverC not in ['=', ' ']:
                    word = leftOverC
                    wordPosRange = [unoccupiedPos, None]
                else:
                    word = ''
                    wordPosRange = [None, None]
            ############################
            if self.verbose:
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
            'startPos':wordPosRange[0],
            'endPos':wordPosRange[0]+len(word),
            'parent':None,
            'type':'number' if isNum(word) else 'variable',
            'ganzStartPos':wordPosRange[0],
            'ganzEndPos':wordPosRange[0]+len(word),
            'position':wordPosRange[0]#this is for building AST's convienence
        })#, 'parentsInfo':self.wordLowestBackSlashArgumentParents}) # 
        #debugging double check that we got the contiguous right....
        if self.verbose:#TTTTTTTTTTTTTTTTTTTTTTTTTTT
            print('&&&&&&&&&&&&&&&contiguousInfoList&&&&&&&&&&&&&&&&&')
            print(self.contiguousInfoList)
            print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
            # import pdb;pdb.set_trace()
        self.event__contiguousLeftOvers.set()


    def _varFindVarChildren(self): #also store parent for easier/faster processing
        self.event__findInfixAndEnclosingBrackets.wait()
        self.event__removeCaretThatIsNotExponent.wait()
        self.event__varFindVarChildren.set()



    def _funcFindFuncChildren(self): # make the children key explicit
        self.event__findInfixAndEnclosingBrackets.wait()
        self.event__removeCaretThatIsNotExponent.wait()
        self.event__funcFindFuncChildren.set()



    def _infixFindInfixChildren(self): # make the children key explicit
        self.event__findInfixAndEnclosingBrackets.wait()
        self.event__removeCaretThatIsNotExponent.wait()
        self.event__infixFindInfixChildren.set()




    def _infixFuncVarLeftoversCrossFindChildren(self):
        self.event__varFindVarChildren.wait()
        self.event__funcFindFuncChildren.wait()
        self.event__infixFindInfixChildren.wait()
        self.event__contiguousLeftOvers.wait()
        self.event__infixFuncVarLeftoversCrossFindChildren.set()


    def _addChildOnMinusInfixWithNoLeftArg(self):
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
        self.event__infixFuncVarLeftoversCrossFindChildren.wait()
        for infixInfoDict in self.listOfInfixInfoDict:
            if infixInfoDict['name']=='-' and infixInfoDict['child'][1] is None:
                infixInfoDict['child'][1] = {
                    'name':'0',
                    'startPos':infixInfoDict['position'], # it would be a problem we add more than one implicit 0 or * at the infixInfoDict['position']
                    'endPos':infixInfoDict['position'],
                    'type':'number',
                    'ganzStartPos':infixInfoDict['position'],
                    'ganzEndPos':infixInfoDict['position']
                }
                self.contiguousInfoList.append({
                'name':'0', 
                'startPos':infixInfoDict['position'],
                'endPos':infixInfoDict['position'],
                'type':'number',
                'ganzStartPos':infixInfoDict['position'],
                'ganzEndPos':infixInfoDict['position'],
                'parent':{
                        'name':infixInfoDict['name'],
                        'startPos':infixInfoDict['position'],
                        'endPos':infixInfoDict['position']+len(infixInfoDict['name']),
                        'type':'infix',
                        'childIdx':1,
                        'ganzStartPos':infixInfoDict['left__startBracketPos'],
                        'ganzEndPos':infixInfoDict['right__endBracketPos']
                    }
                })

        if self.verbose:
            for d in self.contiguousInfoList:
                print('>>>', d['name'], d['startPos'], d['endPos'], '<<<')
            # import pdb;pdb.set_trace()
        self.event__addChildOnMinusInfixWithNoLeftArg.set()


    def _addImplicitMultipy(self):
        """
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
        #B will not be groupped together with A and C, only with either B and C, unless we re-check those existing in consecutiveGroups...
        #SO PLEASE NARABEKAENASAI! (startPos nishitagatte ne)
        #have to do all-pairs consecutiveness checking.
        #TODO maybe this can be a general algorithm.... grouping by consecutiveness.... even in 3D space... like how bubbles come together to make bigger bubbles (or atoms => molecules :))
        
        self.event__addChildOnMinusInfixWithNoLeftArg.wait()
        allDings = sorted(self.contiguousInfoList+self.noBraBackslashPos+self.variablesPos+self.functionPos+self.listOfInfixInfoDict,key=lambda item: item['startPos'])
        consecutiveGroups = {} # (grenzeStartPos, grenzeEndPos) : [ding0, ding1, ...]


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



        #load each ding as keys first....
        for ding in allDings:
            if ding['type'] == 'infix':
                consecutiveGroups[(ding['position'], ding['position']+len(ding['name']))] = [ding]
            else:
                sKey = 'ganzStartPos'
                eKey = 'ganzEndPos'
                consecutiveGroups[(ding[sKey], ding[eKey])] = [ding]

        def rangesConsecutiveInEqsIgnoringSpace(grenzeRange0, grenzeRange1):
            start0 = grenzeRange0[0]
            end0 = grenzeRange0[1]
            start1 = grenzeRange1[0]#ding['ganzStartPos']
            end1 = grenzeRange1[1]#ding['ganzEndPos']
            ##############
            # print(start0, end0, start1, end1, '<<<<<<<<<')
            # import pdb;pdb.set_trace()

            ##############
            if end0<=start1 and len(self._eqs[end0:start1].strip()) == 0:
                # print('>>>>>>>>>>>>>>>>>>>>append')
                return 'append'
            if end1<=start0 and len(self._eqs[end1:start0].strip()) == 0:
                # print('>>>>>>>>>>>>>>>>>>>>prepend')
                return 'prepend'
            return None

        sortedConsecutiveGroupsItems = sorted(consecutiveGroups.items(), key=lambda item: item[0][0])
        ###################################
        if self.verbose:
            print('))))))))))))))))))))))))))))')
            ppprint(consecutiveGroups, sorted(consecutiveGroups.items(), key=lambda item: item[0][0]))
            print('SGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGISGGI')
            print('))))))))))))))))))))))))))))')
        ###################################
        changed = True
        while changed:
            #sortedConsecutiveGroupsItems = sorted(consecutiveGroups.items(), key=lambda item: item[0][0])
            changed = False
            ###################
            if self.verbose:
                print('@@@@@@@@@@@@@@@@@@@@@@@, reset sortedConsecutiveGroupsItems')
                ppprint(consecutiveGroups, sortedConsecutiveGroupsItems)
                print('@@@@@@@@@@@@@@@@@@@@@@@, reset sortedConsecutiveGroupsItems')
            ###################
            for grenzeRange0, existingDings0 in sortedConsecutiveGroupsItems: # TODO refactor to more dimensions

                if changed:
                    if self.verbose:
                        print('BREAKKKKKKKKKKKKKKKKKKKKKKKKKKKK2')
                    break
                for grenzeRange1, existingDings1 in sortedConsecutiveGroupsItems:
                    if grenzeRange0 == grenzeRange1:
                        continue
                    #########
                    if self.verbose:
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
                        if grenzeRange0 in consecutiveGroups:
                            del consecutiveGroups[grenzeRange0]
                        if grenzeRange1 in consecutiveGroups:
                            del consecutiveGroups[grenzeRange1]
                        consecutiveGroups[newGrenzeRange] = newExistingDings
                        sortedConsecutiveGroupsItems = sorted(consecutiveGroups.items(), key=lambda item: item[0][0])
                        changed = True
                        #############
                        if self.verbose:
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
                            ppprint(consecutiveGroups, sortedConsecutiveGroupsItems)
                            print('====================')
                        #############
                        if self.verbose:
                            print('BREAKKKKKKKKKKKKKKKKKKKKKKKKKKKK1')
                        break
                    if self.verbose:
                        print('AFTER BREAK1, changed: ', changed)

        #here we would have allDings in consecutive-groupings, then we add the implicit multiplications yay! Complete answer....

        ##############
        if self.verbose:
            print('consecutiveGroups<<<<<<<<<<<<<<')
            ppprint(consecutiveGroups, sorted(consecutiveGroups.items(), key=lambda item: item[0][0]))
            print('consecutiveGroups<<<<<<<<<<<<<<')
            # import pdb;pdb.set_trace()
        ##############

        def getMostLeftStartPos(ting, currentGanzStartPos):
            if ting['type'] == 'infix':
                return min(ting['left__argStart'], currentGanzStartPos)
            else:
                return min(ting['ganzStartPos'], currentGanzStartPos)
        def getMostRightEndPos(ting, currentGanzEndPos):
            if ting['type'] == 'infix':
                return max(ting['right__argEnd'], currentGanzEndPos)
            else:
                return max(ting['ganzEndPos'], currentGanzEndPos)

        rootsAndGanzeWidth = [] #these are treeified-dings, each item is {'root':, 'ganzStartPos':, 'ganzEndPos':}
        implicitMultiplyId = 0
        treeifiedDingsGanzStartPos = len(self._eqs) + 1
        treeifiedDingsGanzEndPos = -1
        newConsecutiveGroups = {}
        for grenzeRange, dings in consecutiveGroups.items():
            ding = dings[0] # this will be the root of treeified-dings (or be replaced)
            treeifiedDingsGanzStartPos = getMostLeftStartPos(ding, treeifiedDingsGanzStartPos)
            treeifiedDingsGanzEndPos = getMostRightEndPos(ding, treeifiedDingsGanzEndPos)
            newDings = [ding]

            #dings are in consecutive order ... by way it was constructed above.
            if len(dings) > 1: # must have at least 2 items in dings, sonst kann nicht implicitMultiply beibringen
                for idx in range(1, len(dings)): # assumes that dings are sorted by startPos

                    #all the types are number, variable (leftOvers&backslashNoBra); backslash_variable, backslash_function, infixes...
                    prevDing = dings[idx-1]
                    ding = dings[idx]
                    treeifiedDingsGanzStartPos = getMostLeftStartPos(ding, treeifiedDingsGanzStartPos) # but this does not contain the information of implicit multiply
                    treeifiedDingsGanzEndPos = getMostRightEndPos(ding, treeifiedDingsGanzEndPos)
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
                            if ding['name'] == dding['name'] and ding['startPos'] == dding['startPos']:
                                return leftest
                            if ding['type'] == 'infix' and (ding['right__type'] =='enclosing' or ding['right__type'] == 'leftRight'):
                                leftest = ding
                        return leftest
                    ################### find nearest infix with leftOpenBracket, right of dding, if no, then last Ding in dings
                    def findRightestInfixFrom(dding):
                        rightest = dings[-1]
                        for ding in reversed(dings): # assumes that dings are sorted by startPos
                            if ding['name'] == dding['name'] and ding['startPos'] == dding['startPos']:
                                return rightest
                            if ding['type'] == 'infix' and (ding['left__type'] =='enclosing' or ding['left__type'] == 'leftRight'):
                                rightest = ding
                        return rightest
                    ###################
                    if prevDing['type'] == 'infix' and ding['type'] == 'infix':
                        #if prevDing['right__startBracketType'] is not None and prevDing['right__endBracketType'] is not None and ding['left__startBracketType'] is not None and ding['left__endBracketType']: 
                        if prevDing['right__type'] == 'leftRight' and ding['left__type'] == 'leftRight':# ???+(...)*(...)+???
                            implicitMultiplyNode = ('*', (implicitMultiplyId, -1))
                            implicitMultiplyId += 1
                            implicitMultiplyInfoDict = { # rightarg * leftarg
                                'name':'*',
                                'position':-1, # no real position in equation
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
                                'left__argStart':prevDing['right__startBracketPos'] + len(prevDing['right__startBracketType']), # without the bracket
                                'left__argEnd':prevDing['right__endBracketPos'] - len(prevDing['right__endBracketType']), # without the bracket
                                # leftarg
                                'right__startBracketPos':ding['left__startBracketPos'], #TODO to test leaves with brackets..
                                'right__startBracketType':ding['left__startBracketType'], #TODO to test leaves with brackets..
                                'right__endBracketPos':ding['left__endBracketPos'], #TODO to test leaves with brackets...
                                'right__endBracketType':ding['left__startBracketPos'], #TODO to test leaves with brackets...
                                'right__argStart':ding['left__startBracketPos'] + len(ding['left__startBracketType']),
                                'right__argEnd':ding['left__endBracketPos'] - len(ding['left__endBracketType']),

                                'child':{1:None, 2:None},
                                'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                            }
                            self.listOfInfixInfoDict.append(implicitMultiplyInfoDict)
                            newDings.append(implicitMultiplyInfoDict)
                        #elif prevDing['right__startBracketType'] is not None and prevDing['right__endBracketType'] is not None and ding['left__startBracketType'] is not None: 
                        elif prevDing['right__type'] == 'leftRight' and ding['left__type'] == 'enclosing': #???+(...)*(...+???)
                            #could be ding['right__type'] == 'enclosing' too
                            implicitMultiplyNode = ('*', (implicitMultiplyId, -1))
                            implicitMultiplyId += 1
                            implicitMultiplyInfoDict = {# rightarg * ganz
                                'name':'*',
                                'position':-1, # no real position in equation
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
                                'left__argStart':prevDing['right__startBracketPos'] + len(prevDing['right__startBracketType']), # without the bracket
                                'left__argEnd':prevDing['right__endBracketPos'] - len(prevDing['right__endBracketType']), # without the bracket
                                #ganz
                                'right__startBracketPos':ding['ganzStartPos'], #TODO to test leaves with brackets..
                                'right__startBracketType':ding['left__startBracketType'], #TODO to test leaves with brackets..
                                'right__endBracketPos':ding['ganzEndPos'], #TODO to test leaves with brackets...
                                'right__endBracketType':ding['right__endBracketType'], #TODO to test leaves with brackets...
                                'right__argStart':ding['ganzStartPos'] + len(ding['left__startBracketType']), # without the bracket
                                'right__argEnd':ding['ganzEndPos'] - len(ding['right__endBracketType']), # without the bracket

                                'child':{1:None, 2:None},
                                'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                            }
                            self.listOfInfixInfoDict.append(implicitMultiplyInfoDict)
                            newDings.append(implicitMultiplyInfoDict)
                        #elif prevDing['right__endBracketType'] is not None and ding['left__startBracketType'] is not None and ding['left__endBracketType'] is not None: 
                        elif prevDing['right__type'] == 'enclosing' and ding['left__type'] == 'leftRight': #(???+...)*(...)+???
                            # could be prevDing['left__type'] == 'enclosing'
                            implicitMultiplyNode = ('*', (implicitMultiplyId, -1))
                            implicitMultiplyId += 1
                            implicitMultiplyInfoDict = {# ganz * leftarg
                                'name':'*',
                                'position':-1, # no real position in equation
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
                                'left__argStart':prevDing['ganzStartPos'] + len(prevDing['left__startBracketType']), # without the bracket
                                'left__argEnd':prevDing['ganzEndPos'] - len(prevDing['right__endBracketType']), # without the bracket
                                #leftarg
                                'right__startBracketPos':ding['left__startBracketPos'], #TODO to test leaves with brackets..
                                'right__startBracketType':ding['left__startBracketType'], #TODO to test leaves with brackets..
                                'right__endBracketPos':ding['left__endBracketPos'], #TODO to test leaves with brackets...
                                'right__endBracketType':ding['left__startBracketPos'], #TODO to test leaves with brackets...
                                'right__argStart':ding['left__startBracketPos'] + len(ding['left__startBracketType']), #without the bracket
                                'right__argEnd':ding['left__endBracketPos'] - len(ding['left__endBracketType']), #without the bracket

                                'child':{1:None, 2:None},
                                'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                            }
                            self.listOfInfixInfoDict.append(implicitMultiplyInfoDict)
                            newDings.append(implicitMultiplyInfoDict)
                        #elif prevDing['right__endBracketType'] is not None and ding['left__startBracketType'] is not None: 
                        elif prevDing['right__type'] == 'enclosing' and ding['left__type'] == 'enclosing': #(???+...)*(...+???)
                            implicitMultiplyNode = ('*', (implicitMultiplyId, -1))
                            implicitMultiplyId += 1
                            implicitMultiplyInfoDict = { # ganz * ganz
                                'name':'*',
                                'position':-1, # no real position in equation
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
                                'left__argStart':prevDing['ganzStartPos'] + len(prevDing['left__startBracketType']), # without the bracket
                                'left__argEnd':prevDing['ganzEndPos'] - len(prevDing['right__endBracketType']), # without the bracket
                                #ganz
                                'right__startBracketPos':ding['ganzStartPos'], #TODO to test leaves with brackets..
                                'right__startBracketType':ding['left__startBracketType'], #TODO to test leaves with brackets..
                                'right__endBracketPos':ding['ganzEndPos'], #TODO to test leaves with brackets...
                                'right__endBracketType':ding['right__endBracketType'], #TODO to test leaves with brackets...
                                'right__argStart':ding['ganzStartPos'] + len(ding['left__startBracketType']), # without the bracket
                                'right__argEnd':ding['ganzEndPos'] - len(ding['right__endBracketType']), # without the bracket

                                'child':{1:None, 2:None},
                                'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                            }
                            self.listOfInfixInfoDict.append(implicitMultiplyInfoDict)
                            newDings.append(implicitMultiplyInfoDict)


                    # elif (prevDing['type'] == 'number' and prevDing['type'] == 'number') or (prevDing['type'] == 'variable' and ding['type'] == 'number'):#there are no other possible infix types..., heran haben wir nur (number/variable/backslash_variable/backslash_function)
                    #     raise Exception('Should not have number|number; variable|number, something wrong with leftOver-finding-method')
                    elif prevDing['type'] == 'infix': # ding['type'] != 'infix'
                        #if prevDing['right__startBracketType'] is not None and prevDing['right__endBracketType'] is not None: 
                        if prevDing['right__type'] == 'leftRight': #???+(...)*Ding
                            #nearest infix with leftBracket, right of Ding
                            infixRightOfDing = findRightestInfixFrom(ding) # that has leftCloseBracket
                            implicitMultiplyNode = ('*', (implicitMultiplyId, -1))
                            implicitMultiplyId += 1
                            implicitMultiplyInfoDict = {# rightarg * ganz
                                'name':'*',
                                'position':-1, # no real position in equation
                                'type':'implicit',
                                'startPos':prevDing['right__startBracketPos'],
                                'endPos':infixRightOfDing['endPos'],
                                'ganzStartPos':prevDing['right__startBracketPos'],
                                'ganzEndPos':infixRightOfDing['ganzEndPos'],
                                #rightarg
                                'left__startBracketPos':prevDing['right__startBracketPos'], #TODO to test leaves with brackets..
                                'left__startBracketType':prevDing['right__startBracketType'], #TODO to test leaves with brackets..
                                'left__endBracketPos':prevDing['right__endBracketPos'], #TODO to test leaves with brackets..
                                'left__endBracketType':prevDing['right__endBracketType'], #TODO to test leaves with brackets..
                                'left__argStart':prevDing['right__startBracketPos'] + len(prevDing['right__startBracketType']), # without the bracket
                                'left__argEnd':prevDing['right__endBracketPos'] - len(prevDing['right__endBracketType']), # without the bracket
                                #Ding
                                'right__startBracketPos':infixRightOfDing['right__startBracketPos'], #TODO to test leaves with brackets..
                                'right__startBracketType':infixRightOfDing['right__startBracketType'], #TODO to test leaves with brackets..
                                'right__endBracketPos':infixRightOfDing['right__endBracketPos'], #TODO to test leaves with brackets...
                                'right__endBracketType':infixRightOfDing['right__endBracketType'], #TODO to test leaves with brackets...
                                'right__argStart':infixRightOfDing['right__argStart'],
                                'right__argEnd':infixRightOfDing['right__argEnd'],

                                'child':{1:None, 2:None},
                                'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                            }
                            self.listOfInfixInfoDict.append(implicitMultiplyInfoDict)
                            newDings.append(implicitMultiplyInfoDict)
                        #elif prevDing['right__endBracketType'] is not None:
                        elif prevDing['right__type'] == 'enclosing': #(???+...)*Ding
                            infixRightOfDing = findRightestInfixFrom(ding) # that has leftCloseBracket
                            implicitMultiplyNode = ('*', (implicitMultiplyId, -1))
                            implicitMultiplyId += 1
                            implicitMultiplyInfoDict = {# ganz * leftarg
                                'name':'*',
                                'position':-1, # no real position in equation
                                'type':'implicit',
                                'startPos':prevDing['ganzStartPos'],
                                'endPos':infixRightOfDing['endPos'],
                                'ganzStartPos':prevDing['ganzStartPos'],
                                'ganzEndPos':infixRightOfDing['ganzEndPos'],
                                #ganz
                                'left__startBracketPos':prevDing['ganzStartPos'], #TODO to test leaves with brackets..
                                'left__startBracketType':prevDing['left__startBracketType'], #TODO to test leaves with brackets..
                                'left__endBracketPos':prevDing['ganzEndPos'], #TODO to test leaves with brackets..
                                'left__endBracketType':prevDing['right__endBracketType'], #TODO to test leaves with brackets..
                                'left__argStart':prevDing['ganzStartPos'] + len(prevDing['left__startBracketType']), # without the bracket
                                'left__argEnd':prevDing['ganzEndPos'] - len(prevDing['right__endBracketType']), # without the bracket
                                #Ding
                                'right__startBracketPos':infixRightOfDing['right__startBracketPos'], #TODO to test leaves with brackets..
                                'right__startBracketType':infixRightOfDing['right__startBracketType'], #TODO to test leaves with brackets..
                                'right__endBracketPos':infixRightOfDing['right__endBracketPos'], #TODO to test leaves with brackets...
                                'right__endBracketType':infixRightOfDing['right__endBracketType'], #TODO to test leaves with brackets...
                                'right__argStart':infixRightOfDing['right__argStart'],
                                'right__argEnd':infixRightOfDing['right__argEnd'],

                                'child':{1:None, 2:None},
                                'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                            }
                            self.listOfInfixInfoDict.append(implicitMultiplyInfoDict)
                            newDings.append(implicitMultiplyInfoDict)
                    elif ding['type'] == 'infix': # prevDing['type'] != 'infix'
                        #if ding['left__startBracketType'] is not None and ding['left__endBracketType'] is not None:
                        if ding['left__type'] == 'leftRight': #Ding*(...)+???
                            infixLeftOfDing = findLeftestInfixFrom(prevDing) # that has rightCloseBracket
                            implicitMultiplyNode = ('*', (implicitMultiplyId, -1))
                            implicitMultiplyId += 1
                            implicitMultiplyInfoDict = {# ganz * leftarg
                                'name':'*',
                                'position':-1, # no real position in equation
                                'type':'implicit',
                                'startPos':infixLeftOfDing['startPos'],
                                'endPos':ding['left__endBracketPos'],
                                'ganzStartPos':infixLeftOfDing['ganzStart'],
                                'ganzEndPos':ding['left__endBracketPos'],
                                #Ding
                                'left__startBracketPos':infixLeftOfDing['left__startBracketPos'], #TODO to test leaves with brackets..
                                'left__startBracketType':infixLeftOfDing['left__startBracketType'], #TODO to test leaves with brackets..
                                'left__endBracketPos':infixLeftOfDing['left__endBracketPos'], #TODO to test leaves with brackets..
                                'left__endBracketType':infixLeftOfDing['left__endBracketType'], #TODO to test leaves with brackets..
                                'left__argStart':infixLeftOfDing['left__argStart'], # without the bracket
                                'left__argEnd':infixLeftOfDing['left__argEnd'], # without the bracket
                                #leftarg
                                'right__startBracketPos':ding['left__startBracketPos'], #TODO to test leaves with brackets..
                                'right__startBracketType':ding['left__startBracketType'], #TODO to test leaves with brackets..
                                'right__endBracketPos':ding['left__endBracketPos'], #TODO to test leaves with brackets...
                                'right__endBracketType':ding['left__startBracketPos'], #TODO to test leaves with brackets...
                                'right__argStart':ding['left__startBracketPos'] + len(ding['left__startBracketType']), #without the bracket
                                'right__argEnd':ding['left__endBracketPos'] - len(ding['left__endBracketType']), #without the bracket

                                'child':{1:None, 2:None},
                                'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                            }
                            self.listOfInfixInfoDict.append(implicitMultiplyInfoDict)
                            newDings.append(implicitMultiplyInfoDict)
                        #elif ding['left__startBracketType'] is not None:
                        elif ding['left__type'] == 'enclosing': #Ding*(...+???)
                            infixLeftOfDing = findLeftestInfixFrom(prevDing) # that has rightCloseBracket
                            import pdb;pdb.set_trace()
                            implicitMultiplyNode = ('*', (implicitMultiplyId, -1))
                            implicitMultiplyId += 1
                            implicitMultiplyInfoDict = {# rightarg * ganz
                                'name':'*',
                                'position':-1, # no real position in equation
                                'type':'implicit',
                                'startPos':infixLeftOfDing['startPos'],
                                'endPos':ding['ganzEndPos'],
                                'ganzStartPos':infixLeftOfDing['ganzStartPos'],
                                'ganzEndPos':ding['ganzEndPos'],
                                #Ding
                                'left__startBracketPos':infixLeftOfDing['left__startBracketPos'], #somehow... infixLeftOfDing = {'name': 'x', 'startPos': 8, 'endPos': 9, 'parent': None, 'type': 'variable', 'ganzStartPos': 8, 'ganzEndPos': 9, 'position': 8}
                                'left__startBracketType':infixLeftOfDing['left__startBracketType'], #TODO to test leaves with brackets..
                                'left__endBracketPos':infixLeftOfDing['left__endBracketPos'], #TODO to test leaves with brackets..
                                'left__endBracketType':infixLeftOfDing['left__endBracketType'], #TODO to test leaves with brackets..
                                'left__argStart':infixLeftOfDing['left__argStart'], # without the bracket
                                'left__argEnd':infixLeftOfDing['left__argEnd'], # without the bracket
                                #ganz
                                'right__startBracketPos':ding['ganzStartPos'], #TODO to test leaves with brackets..
                                'right__startBracketType':ding['left__startBracketType'], #TODO to test leaves with brackets..
                                'right__endBracketPos':ding['ganzEndPos'], #TODO to test leaves with brackets...
                                'right__endBracketType':ding['right__endBracketType'], #TODO to test leaves with brackets...
                                'right__argStart':ding['ganzStartPos'] + len(ding['left__startBracketType']), # without the bracket
                                'right__argEnd':ding['ganzEndPos'] - len(ding['right__endBracketType']), # without the bracket

                                'child':{1:None, 2:None},
                                'parent':None # no setting parents here, since we need to check for presence of infix in all Dings first.
                            }
                            self.listOfInfixInfoDict.append(implicitMultiplyInfoDict)
                            newDings.append(implicitMultiplyInfoDict)
                    else: #both prevDing & ding are not infixes.... 
                        #add implicit multiply to (prevDing and ding)
                        #-need to provide parent of () for update child [name, startPos, endPos, ganzStartPos, ganzEndPos]
                        implicitMultiplyNode = ('*', (implicitMultiplyId, -1))
                        implicitMultiplyId += 1
                        implicitMultiplyInfoDict = {
                            'name':'*',
                            'position':-1, # means its implicit multiply
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
                        self.listOfInfixInfoDict.append(implicitMultiplyInfoDict)
                        newDings.append(implicitMultiplyInfoDict)
                    newDings.append(ding) # add old ding back

                #add child/parent relationship to infixes of newDings
                #should have at least 2 things in newDings, else cannot form relationship
                #need to sort according to ^/*-+, then we go from left to right
                if self.verbose:
                    print('grouping new dings by priority****************************************')
                    # import pdb;pdb.set_trace()
                processed = set() # this should include all the dingPos of the infixes, and then later the arguments that are linked to the infixes
                prioritiesToDingsPos = {}
                dingPosToPriorities = {}
                for dingPos, ding in enumerate(newDings):
                    try:
                        priority = self.PRIOIRITIZED_INFIX.index(ding['name']) # the smaller the number the higher the priority. Non-infix has the highest prioirity of -1
                        processed.add(dingPos) # this is an infix
                    except:
                        # dingPosToPriorities[dingPos] = -1
                        continue # we are only working on infix here. so ignore everything else

                    existingDingsPos = prioritiesToDingsPos.get(priority, [])
                    existingDingsPos.append(dingPos)
                    prioritiesToDingsPos[priority] = existingDingsPos
                    # dingPosToPriorities[dingPos] = priority
                prioritiesDingsPosItemList = sorted(prioritiesToDingsPos.items(), key=lambda item: item[0])

                if self.verbose:
                    print('build subtrees by INFIX PRIORITY')
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


                        if self.verbose:
                            """
                            dingsPoss = [0]
                            there is exactly one idx
                            and there is nothing to the left of dingPos in newDings.
                            and there is nothing to the right of dingPos in newDings
                            """
                            print('******BEFORE SETTING PC relationship subtrees, leftDingPos:', dingToLeftIdx, ', dingPos', dingPos, ' dingToRightIdx, ', dingToRightIdx)
                            print('leftDing ************')
                            print(leftDing)
                            print('ding *****************')
                            print(ding)
                            print('rightDing ***********')
                            print(rightDing)
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


                        if self.verbose:
                            """
                            dingsPoss = [0]
                            there is exactly one idx
                            and there is nothing to the left of dingPos in newDings.
                            and there is nothing to the right of dingPos in newDings
                            """
                            print('******building subtrees, leftDingPos:', dingToLeftIdx, ', dingPos', dingPos, ' dingToRightIdx, ', dingToRightIdx)
                            print('leftDing ************')
                            print(leftDing)
                            print('ding *****************')
                            print(ding)
                            print('rightDing ***********')
                            print(rightDing)
                            print('**********************')
                            # import pdb;pdb.set_trace()

                        #TODO set parents, so that we can figure out equals children later.....
                        processed.remove(dingPos) # the infix needs to be available again, to be a child
                        processed.add(dingToLeftIdx) # args used may not be reused again
                        processed.add(dingToRightIdx) # args used may not be reused again
            #the last ding from the last-for-loop is the root of dings
            rootsAndGanzeWidth.append({'root':ding, 'ganzStartPos':treeifiedDingsGanzStartPos, 'ganzEndPos':treeifiedDingsGanzEndPos})
            #clear the treeifiedDingsGanzStartPos, treeifiedDingsGanzEndPos
            treeifiedDingsGanzStartPos = len(self._eqs) + 1
            treeifiedDingsGanzEndPos = -1
            newConsecutiveGroups[grenzeRange] = newDings
        #we have to deal with the backslash_function/backslash_variable, whom have no children... since their children might be infixs, for example: \sin(2*x_0), the child2 of \sin is *
        #but child/ren of backslash_function/variable, will not be on the same dings as the backslash_function/variable.... and we can only do this after we build parent/child relationship with all the infixes...
        #preferably we can identify some parent/relationship-leveling between dings, if not, all i can think of is all-dings-each-dings-compare-each-argumentPos-v-ganzDingStartEnd
        exponentialId = 0 # for id-ing new exponentials TODO all the implicitly added, should have 1 big id to draw from... TODO but if multiprocess--> livedeadlock
        self.alleDing = []
        #################
        if self.verbose:
            print('*****************************************build parent/child relationship amongst subtree')
            #check existing parent child relationship
            # import pdb;pdb.set_trace()
            print('*****************************************build parent/child relationship amongst subtree')
        #################
        for grenzeRange, dings in newConsecutiveGroups.items():
            for ding in dings:
                if (ding['type'] == 'backslash_function' and (ding['child'][1] is None or ding['child'][2] is None)) or \
                (ding['type'] == 'backslash_variable' and ding['child'][1] is None): #only come here if there is some None child
                    #find the root of dings
                    if ding['type'] == 'backslash_function':
                        if ding['child'][1] is None and ding['child'][2] is None:
                            def rootIsContained(tGSPos, tGEPos):
                                if ding['argument1StartPosition'] <= tGSPos and  tGEPos <= ding['argument1EndPosition']:
                                    return 1
                                if ding['argument2StartPosition'] <= tGSPos and tGEPos <= ding['argument2EndPosition']:
                                    return 2
                                return False
                        elif ding['child'][1] is None:
                            def rootIsContained(tGSPos, tGEPos):
                                # import pdb;pdb.set_trace()
                                if ding['argument1StartPosition'] <= tGSPos and  tGEPos <= ding['argument1EndPosition']:
                                    return 1
                                return False
                        elif ding['child'][2] is None:
                            def rootIsContained(tGSPos, tGEPos):
                                if ding['argument2StartPosition'] <= tGSPos and tGEPos <= ding['argument2EndPosition']:
                                    return 2
                                return False
                    elif ding['type'] == 'backslash_variable':
                        if ding['child'][1] is None:
                            def rootIsContained(tGSPos, tGEPos):
                                if ding['argument1StartPosition'] <= tGSPos and  tGEPos <= ding['argument1EndPosition']:
                                    return 1
                                return False
                    #we need to find the widest ganzeWidth, but still contained
                    theRoot1 = None
                    theGanzStartPos1 = len(self._eqs) + 1#largest num
                    theGanzEndPos1 = -1#smallest num
                    theRoot2 = None
                    theGanzStartPos2 = len(self._eqs) + 1#largest num
                    theGanzEndPos2 = -1#smallest num
                    for rootInfoDict in rootsAndGanzeWidth:
                        ####
                        if self.verbose:
                            print('checking ding', ding['name'], ' contains rootInfoDict of rootsAndGanzeWidth ', rootInfoDict['root']['name'])
                            # import pdb;pdb.set_trace()
                        ####
                        containedArgument = rootIsContained(rootInfoDict['ganzStartPos'], rootInfoDict['ganzEndPos'])
                        if containedArgument:
                            ####
                            if self.verbose:
                                print('ding', ding['name'], ' contains  rootInfoDict of rootsAndGanzeWidth ', rootInfoDict['root']['name'], ' containedment child:', containedArgument)
                                # import pdb;pdb.set_trace()
                            ####
                            if containedArgument == 1 and ( rootInfoDict['ganzStartPos'] <= theGanzStartPos1 and theGanzEndPos1 <= rootInfoDict['ganzEndPos'] ):
                                theRoot1 = rootInfoDict['root']
                                theGanzStartPos1 = rootInfoDict['ganzStartPos']
                                theGanzEndPos1 = rootInfoDict['ganzEndPos']
                            if containedArgument == 2 and ( rootInfoDict['ganzStartPos'] <= theGanzStartPos2 and theGanzEndPos2 <= rootInfoDict['ganzEndPos'] ):
                                theRoot2 = rootInfoDict['root']
                                theGanzStartPos2 = rootInfoDict['ganzStartPos']
                                theGanzEndPos2 = rootInfoDict['ganzEndPos']
                    #There are trigo function with no power(arg1), if there is nothing fitting here for trigo function in arg1, then we take from argument1
                    #Put the child into the right place
                    ################
                    if self.verbose:
                        print('**************************check what theRoot1 or theRoot2 we found...')
                        # import pdb;pdb.set_trace()
                        print('**************************check what theRoot1 or theRoot2 we found...')
                    ################
                    if ding['type'] == 'backslash_variable':
                        ding['child'][1] = {
                            'name':theRoot1['name'],
                            'startPos':theRoot1['startPos'],
                            'endPos':theRoot1['endPos'],
                            'type':theRoot1['type'],
                            'ganzStartPos':theRoot1['startPos'],
                            'ganzEndPos':theRoot1['endPos']
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
                    # if ding['type'] == 'backslash_function' and ding['child'][1] is None and ding['argument1StartPosition'] <= theGanzStartPos1 and  theGanzEndPos1 <= ding['argument1EndPosition']:
                    if theRoot1:
                        # if theRoot1 is None and ding['name'] in self.TRIGOFUNCTION and ding['child'][1] is None:
                        #     # ding['child'][1] = {
                        #     #     'name':1,
                        #     #     'startPos':None,
                        #     #     'endPos':None,
                        #     #     'type':'number',
                        #     #     'ganzStartPos':None,
                        #     #     'ganzEndPos':None
                        #     # }
                        #     ding['child'][1] = None # leave it as None, then it will not appear in AST...
                        # else:
                        ding['child'][1] = {
                            'name':theRoot1['name'],
                            'startPos':theRoot1['startPos'],
                            'endPos':theRoot1['endPos'],
                            'type':theRoot1['type'],
                            'ganzStartPos':theRoot1['startPos'],
                            'ganzEndPos':theRoot1['endPos']
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


                    # if ding['type'] == 'backslash_function' and ding['child'][2] is None and ding['argument2StartPosition'] <= theGanzStartPos2 and  theGanzEndPos2 <= ding['argument2EndPosition']:
                    if theRoot2:
                        ding['child'][2] = {
                            'name':theRoot2['name'],
                            'startPos':theRoot2['startPos'],
                            'endPos':theRoot2['endPos'],
                            'type':theRoot2['type'],
                            'ganzStartPos':theRoot2['startPos'],
                            'ganzEndPos':theRoot2['endPos']
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
                    #we have to do this no matter if children of trig is None or not. but, after we got children of trig (if trig was None in the first place)

                if ding['name'] == 'sqrt' and ding['child'][1] is None: # arg1 is empty so, by default, arg1=2 (SQUARE root)
                    ding['child'][1] = {
                        'name':2,
                        'startPos':exponentialId,
                        'endPos':exponentialId,
                        'type':'number',
                        'ganzStartPos':exponentialId,
                        'ganzEndPos':exponentialId
                    }
                    self.alleDing.append({
                        'name':2,
                        'startPos':exponentialId,
                        'endPos':exponentialId,
                        'type':'number',
                        'ganzStartPos':exponentialId,
                        'ganzEndPos':exponentialId,
                        'parent':{
                            'name':ding['name'],
                            'startPos':ding['startPos'],
                            'endPos':ding['endPos'],
                            'type':ding['type'],
                            'childIdx':1,
                            'ganzStartPos':ding['ganzStartPos'],
                            'ganzEndPos':ding['ganzEndPos']
                        }
                    })
                    exponentialId += 1 #TODO rename exponentialId to general AlleDing

                if ding['name'] == 'log' and ding['child'][1] is None:
                    ding['child'][1] = {
                        'name':10, # natural logarithms...
                        'startPos':exponentialId,
                        'endPos':exponentialId,
                        'type':'number',
                        'ganzStartPos':exponentialId,
                        'ganzEndPos':exponentialId
                    }
                    self.alleDing.append({
                        'name':10,
                        'startPos':exponentialId,
                        'endPos':exponentialId,
                        'type':'number',
                        'ganzStartPos':exponentialId,
                        'ganzEndPos':exponentialId,
                        'parent':{
                            'name':ding['name'],
                            'startPos':ding['startPos'],
                            'endPos':ding['endPos'],
                            'type':ding['type'],
                            'childIdx':1,
                            'ganzStartPos':ding['ganzStartPos'],
                            'ganzEndPos':ding['ganzEndPos']
                        }
                    })
                    exponentialId += 1 #TODO rename exponentialId to general AlleDing


                if ding['name'] == 'ln':
                    ding['name'] = 'log'
                    ding['child'][1] = {
                        'name':'e', # natural logarithms...
                        'startPos':exponentialId,
                        'endPos':exponentialId,
                        'type':'number',
                        'ganzStartPos':exponentialId,
                        'ganzEndPos':exponentialId
                    }
                    self.alleDing.append({
                        'name':'e',
                        'startPos':exponentialId,
                        'endPos':exponentialId,
                        'type':'number',
                        'ganzStartPos':exponentialId,
                        'ganzEndPos':exponentialId,
                        'parent':{
                            'name':ding['name'],
                            'startPos':ding['startPos'],
                            'endPos':ding['endPos'],
                            'type':ding['type'],
                            'childIdx':1,
                            'ganzStartPos':ding['ganzStartPos'],
                            'ganzEndPos':ding['ganzEndPos']
                        }
                    })
                    exponentialId += 1 #TODO rename exponentialId to general AlleDing


                # import pdb;pdb.set_trace()#TODO debug, it seems that below code block is repeated too many times
                #special case for TRIG, but we still want to process the second child, after process the first child of trig (since power of trig may not be a number)
                if ding['name'] in self.TRIGOFUNCTION and ding['child'][1] is not None:
                    #NO widest-arg1-on-ding and arg1(child)=None
                    # if theRoot1 is None and ding['child'][1] is None: #no exponential on ding trig
                    #     ding['child'][1] = None # leave it as None, then it will not appear in AST...
                    #what about theRoot1 is not None ding['child'][1] is None,THEN hopefully, theRoot1==ding['child'][1]
                    # else: #trig has power   ding['child'][1] is not None
                        #add exponent, set as parent of [trig, power]
                    expoDing = {
                        'name':'^',
                        'startPos':exponentialId, # not real, 
                        'endPos':exponentialId,
                        'ganzStartPos':exponentialId,
                        'ganzEndPos':exponentialId,
                        'type':'infix',
                        'child':{
                            1:{
                            'name':ding['name'],
                            'startPos':ding['startPos'],
                            'endPos':ding['endPos'],
                            'type':ding['type'],
                            'ganzStartPos':ding['ganzStartPos'],
                            'ganzEndPos':ding['ganzEndPos']
                            },
                            2:{#power is the arg1 of ding
                            'name':ding['child'][1]['name'],
                            'startPos':ding['child'][1]['startPos'],
                            'endPos':ding['child'][1]['endPos'],
                            'type':ding['child'][1]['type'],
                            'ganzStartPos':ding['child'][1]['ganzStartPos'],
                            'ganzEndPos':ding['child'][1]['ganzEndPos']
                            }
                        },
                        'parent':ding['parent']
                    }
                    #need actual ding's parent and update its child to expoDing
                    actualParent = None
                    for grenzeRange0, dings0 in newConsecutiveGroups.items():
                        for ding0 in dings0:
                            if ding0['name'] == ding['parent']['name'] and ding0['startPos'] == ding['parent']['startPos'] and ding0['endPos'] == ding['parent']['endPos']:
                                actualParent = ding0
                    actualParent['child'][ding['parent']['childIdx']] = {
                        'name':expoDing['name'],
                        'startPos':expoDing['startPos'],
                        'endPos':expoDing['endPos'],
                        'type':expoDing['type'],
                        'ganzStartPos':expoDing['ganzStartPos'],
                        'ganzEndPos':expoDing['ganzEndPos']

                    }
                    exponentialId += 1
                    self.alleDing.append(expoDing)
                    #set ding parent as expoDing's child1
                    ding['parent'] = {
                        'name':expoDing['name'],
                        'startPos':expoDing['startPos'],
                        'endPos':expoDing['endPos'],
                        'type':expoDing['type'],
                        'childIdx':1,
                        'ganzStartPos':expoDing['ganzStartPos'],
                        'ganzEndPos':expoDing['ganzEndPos']
                    }
                    #remove ding arg1 (power)
                    ding['child'][1] = None
                    #############
                    # import pdb;pdb.set_trace()
                    #############

                self.alleDing.append(ding)# just dump everything together
        #add the = (with children) in alleDing, YAY!
        #first find ding with no parent
        dingsNoParents = []
        for ding in self.alleDing:
            if ding['parent'] is None: # 'parent' not in ding (this is not acceptable, if this happens, fix the code apriori)
                dingsNoParents.append(ding)
        if len(dingsNoParents) != 2:
            import pdb;pdb.set_trace()
            raise Exception('Equals only have 2 sides')
        #build the AST here...
        self.nameStartEndToNodeId = {}
        nodeId = 1
        for s in self.alleDing:
            self.nameStartEndToNodeId[(s['name'], s['startPos'], s['endPos'])] = nodeId
            nodeId += 1
        self.ast = {}
        child0Id = self.nameStartEndToNodeId[(dingsNoParents[0]['name'], dingsNoParents[0]['startPos'], dingsNoParents[0]['endPos'])]
        child1Id = self.nameStartEndToNodeId[(dingsNoParents[1]['name'], dingsNoParents[1]['startPos'], dingsNoParents[1]['endPos'])]
        # import pdb;pdb.set_trace()
        if dingsNoParents[0]['position'] < dingsNoParents[1]['position']:
            self.ast[('=', 0)] = [(dingsNoParents[0]['name'], child0Id), (dingsNoParents[1]['name'], child1Id)]
        else:
            self.ast[('=', 0)] = [(dingsNoParents[1]['name'], child1Id), (dingsNoParents[0]['name'], child0Id)]


        for parent in self.alleDing:
            parentId = self.nameStartEndToNodeId[(parent['name'], parent['startPos'], parent['endPos'])]

            if 'child' in parent:
                if len(parent['child']) == 1:
                    childKey = self.nameStartEndToNodeId[(parent['child'][1]['name'], parent['child'][1]['startPos'], parent['child'][1]['endPos'])]
                    self.ast[(parent['name'], parentId)] = [(parent['child'][1]['name'], childKey)]
                elif len(parent['child']) == 2: #current this is the only other possibility
                    if parent['child'][1] is not None:
                        child1Name = parent['child'][1]['name']
                        child1Key = self.nameStartEndToNodeId[(child1Name, parent['child'][1]['startPos'], parent['child'][1]['endPos'])]
                        self.ast[(parent['name'], parentId)] = [(child1Name, child1Key)]

                    if parent['child'][2] is not None:
                        child2Name = parent['child'][2]['name']
                        child2Key = self.nameStartEndToNodeId[(child2Name, parent['child'][2]['startPos'], parent['child'][2]['endPos'])]
                        existingChildren = self.ast.get((parent['name'], parentId), [])
                        existingChildren.append((child2Name, child2Key))
                        self.ast[(parent['name'], parentId)] = existingChildren


        

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


        10. convert backslash variables to internal variables mapping
        11. convert backslash function name to standard function name IN automat.arithmetic.function.py
        """
        self._findVariablesFunctionsPositions()
        self._findInfixAndEnclosingBrackets()
        self._removeCaretThatIsNotExponent()
        self._varFindVarChildren() # remove
        self._funcFindFuncChildren() # remove
        self._infixFindInfixChildren() # remove
        self._findLeftOverPosition()
        self._contiguousLeftOvers()
        self._infixFuncVarLeftoversCrossFindChildren() # remove
        self._addChildOnMinusInfixWithNoLeftArg()
        self._addImplicitMultipy()
        #TODO Pool multiprocessing with method priorities (Chodai!)





    def _unparse(self): # TODO from AST to LaTeX string... 
        raise Exception('Unimplemented')

