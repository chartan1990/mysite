if __name__=='__main__':
    from foundation.automat.common import getMatchesOrNone, findAllMatches
    # print('testing latexparsertest.py')
    # equationStr = '\\sin(2x)=2\\sin(x)\\cos(x)'
    # matches = findAllMatches('(\\\\[a-zA-Z]+)', equationStr) # '\\\\[a-zA-Z]+'
    # for reMatch in matches:
    #   posTuple = reMatch.span()
    #   print(equationStr[posTuple[0]:posTuple[1]], '***', reMatch.group())
    # import pdb;pdb.set_trace()
    #
    VARIABLENAMESTAKEANARG = ['overline', 'underline', 'widehat', 'widetilde', 'overrightarrow', 'overleftarrow', 'overbrace', 'underbrace'
    #Math mode accents
    'acute', 'breve', 'ddot', 'grave', 'tilde', 'bar', 'check', 'dot', 'hat', 'vec'
    ] # these 'functions' must be preceded by {
    _eqs = 'e^{i\\theta}\\sin(\\theta)+\\underline{\\alpha}+1234*{7435}*\\beta' # nonsense formula
    for reMatch in findAllMatches('\\\\([a-zA-Z]+)', _eqs): #capturing group omit the backslash
        #import pdb;pdb.set_trace()
        positionTuple = reMatch.span()
        labelName = reMatch.groups()[0]
        print(labelName, positionTuple)
        if labelName in VARIABLENAMESTAKEANARG: # it is actually a special kind of variable
            print(labelName , '<<<<<<<<<<<<IS', _eqs[positionTuple[0]+len(reMatch.group())])