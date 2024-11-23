import inspect
import pprint

from foundation.automat.common.enclosuretree import EnclosureTree
# from foundation.automat.common.enclosuretree import EnclosureTreeLevel

pp = pprint.PrettyPrinter(indent=4)

def test__latexParser__makeEnclosureTreeOfConsecutiveGroupGrenze(verbose=False):
    consecutiveGroups = {   
    (0, 24): [('frac', 0, 24)],
    (6, 9): [('x', 6, 7), ('^', 7, 8), ('2', 8, 9)],
    (12, 15): [('x', 12, 13), ('-', 13, 14), ('2', 14, 15)],
    (17, 20): [('x', 17, 18), ('-', 18, 19), ('3', 19, 20)],
    (21, 23): [('^', 21, 22), ('2', 22, 23)],
    (25, 71): [   ('frac', 25, 38),
                  ('+', 38, 39),
                  ('frac', 39, 53),
                  ('+', 53, 54),
                  ('frac', 54, 71)],
    (31, 32): [('4', 31, 32)],
    (34, 37): [('x', 34, 35), ('-', 35, 36), ('2', 36, 37)],
    (45, 47): [('-', 45, 46), ('3', 46, 47)],
    (49, 52): [('x', 49, 50), ('-', 50, 51), ('3', 51, 52)],
    (60, 61): [('9', 60, 61)],
    (64, 67): [('x', 64, 65), ('-', 65, 66), ('3', 66, 67)],
    (68, 70): [('^', 68, 69), ('2', 69, 70)]
    }
    listPoss = list(consecutiveGroups.keys())
    def firstContainsSecond(p0, p1):
        return p0[0] <= p1[0] and p1[1] <= p0[1]
    def getId(p0):
        return p0

    roots, leaves, enclosureTree, levelToIDs, idToLevel = EnclosureTree.makeEnclosureTreeWithLevelRootLeaves(listPoss, firstContainsSecond, getId)
    #need to change everything to instancemethod instead of class method
    # rootId, enclosureTree, levelToIDs, idToLevel, leaves = EnclosureTreeLevel().growLevelTree(listPoss, firstContainsSecond, getId)
    # leaves = EnclosureTreeLevel.leaves
    if verbose:
        print('**************enclosureTree:')
        pp.pprint(enclosureTree)
        print('**************leaves:')
        pp.pprint(leaves)
        print('**************levelToIDs:')
        pp.pprint(levelToIDs)
        print('**************idToLevel:')
        pp.pprint(idToLevel)
    expected__enclosureTree = {   (0, 24): [(6, 9), (12, 15), (17, 20), (21, 23)],
    (6, 9): [],
    (12, 15): [],
    (17, 20): [],
    (21, 23): [],
    (25, 71): [   (31, 32),
                  (34, 37),
                  (45, 47),
                  (49, 52),
                  (60, 61),
                  (64, 67),
                  (68, 70)],
    (31, 32): [],
    (34, 37): [],
    (45, 47): [],
    (49, 52): [],
    (60, 61): [],
    (64, 67): [],
    (68, 70): []}
    expected__leaves = [   (6, 9),
    (12, 15),
    (17, 20),
    (21, 23),
    (31, 32),
    (34, 37),
    (45, 47),
    (49, 52),
    (60, 61),
    (64, 67),
    (68, 70)]
    expected__levelToIDs = {   0: [(0, 24), (25, 71)],
    1: [   (21, 23),
           (17, 20),
           (12, 15),
           (6, 9),
           (68, 70),
           (64, 67),
           (60, 61),
           (49, 52),
           (45, 47),
           (34, 37),
           (31, 32)]}
    expected__idToLevel = {   (0, 24): 0,
    (6, 9): 1,
    (12, 15): 1,
    (17, 20): 1,
    (21, 23): 1,
    (25, 71): 0,
    (31, 32): 1,
    (34, 37): 1,
    (45, 47): 1,
    (49, 52): 1,
    (60, 61): 1,
    (64, 67): 1,
    (68, 70): 1}
    print(
        inspect.currentframe().f_code.co_name, 
        ' PASSED? ', 
        expected__enclosureTree==enclosureTree and expected__leaves==leaves and expected__levelToIDs==levelToIDs and expected__idToLevel==idToLevel
    )




def test__latexParser__makeEnclosureTreeOfConsecutiveGroupGrenze0(verbose=False):
    consecutiveGroups = {   
    (0, 11): [('log', 0, 11)],
    (6, 7): [('b', 6, 7)],
    (9, 10): [('a', 9, 10)],
    (12, 43): [('frac', 12, 43)],
    (18, 29): [('log', 18, 29)],
    (24, 25): [('c', 24, 25)],
    (27, 28): [('a', 27, 28)],
    (31, 42): [('log', 31, 42)],
    (37, 38): [('c', 37, 38)],
    (40, 41): [('b', 40, 41)]}

    listPoss = list(consecutiveGroups.keys())
    def firstContainsSecond(p0, p1):
        return p0[0] <= p1[0] and p1[1] <= p0[1]
    def getId(p0):
        return p0

    roots, leaves, enclosureTree, levelToIDs, idToLevel = EnclosureTree.makeEnclosureTreeWithLevelRootLeaves(listPoss, firstContainsSecond, getId)
    #need to change everything to instancemethod instead of class method
    # rootId, enclosureTree, levelToIDs, idToLevel, leaves = EnclosureTreeLevel().growLevelTree(listPoss, firstContainsSecond, getId)
    # leaves = EnclosureTreeLevel.leaves
    if verbose:
        print('**************enclosureTree:')
        pp.pprint(enclosureTree)
        print('**************leaves:')
        pp.pprint(leaves)
        print('**************levelToIDs:')
        pp.pprint(levelToIDs) #<<<<<<<<<<<<<<WRONG
        print('**************idToLevel:')
        pp.pprint(idToLevel)
    expected__enclosureTree = {   (0, 11): [(6, 7), (9, 10)],
    (6, 7): [],
    (9, 10): [],
    (12, 43): [(18, 29), (24, 25), (27, 28), (31, 42), (37, 38), (40, 41)],
    (18, 29): [(24, 25), (27, 28)],
    (24, 25): [],
    (27, 28): [],
    (31, 42): [(37, 38), (40, 41)],
    (37, 38): [],
    (40, 41): []}
    expected__leaves = [(6, 7), (9, 10), (24, 25), (27, 28), (37, 38), (40, 41)]
    expected__levelToIDs = {   0: [(12, 43), (0, 11)],
    1: [   (40, 41),
           (37, 38),
           (31, 42),
           (27, 28),
           (24, 25),
           (18, 29),
           (9, 10),
           (6, 7)],
    2: [(40, 41), (37, 38), (27, 28), (24, 25)]}
    expected__idToLevel = {   (0, 11): 0,
    (6, 7): 1,
    (9, 10): 1,
    (12, 43): 0,
    (18, 29): 1,
    (24, 25): 2,
    (27, 28): 2,
    (31, 42): 1,
    (37, 38): 2,
    (40, 41): 2}
    print(
        inspect.currentframe().f_code.co_name, 
        ' PASSED? ', 
        expected__enclosureTree==enclosureTree and expected__leaves==leaves and expected__levelToIDs==levelToIDs and expected__idToLevel==idToLevel
    )



def test__latexParser__parentHavingChildrenOfTheirChildren(verbose=False):
    consecutiveGroups = {   (0, 11): [('log', 0, 11)],
    (6, 7): [('b', 6, 7)],
    (9, 10): [('a', 9, 10)],
    (12, 43): [('frac', 12, 43)],
    (18, 29): [('log', 18, 29)],
    (24, 25): [('c', 24, 25)],
    (27, 28): [('a', 27, 28)],
    (31, 42): [('log', 31, 42)],
    (37, 38): [('c', 37, 38)],
    (40, 41): [('b', 40, 41)]}


    listPoss = list(consecutiveGroups.keys())
    def firstContainsSecond(p0, p1):
        return p0[0] <= p1[0] and p1[1] <= p0[1]
    def getId(p0):
        return p0

    roots, leaves, enclosureTree, levelToIDs, idToLevel = EnclosureTree.makeEnclosureTreeWithLevelRootLeaves(listPoss, firstContainsSecond, getId)
    #need to change everything to instancemethod instead of class method
    # rootId, enclosureTree, levelToIDs, idToLevel, leaves = EnclosureTreeLevel().growLevelTree(listPoss, firstContainsSecond, getId)
    # leaves = EnclosureTreeLevel.leaves
    if verbose:
        print('**************enclosureTree:')
        pp.pprint(enclosureTree)
        print('**************leaves:')
        pp.pprint(leaves)
        print('**************levelToIDs:')
        pp.pprint(levelToIDs) #<<<<<<<<<<<<<<WRONG
        print('**************idToLevel:')
        pp.pprint(idToLevel)
    expected__enclosureTree = {   (0, 11): [(9, 10), (6, 7)],
    (6, 7): [],
    (9, 10): [],
    (12, 43): [(18, 29), (31, 42)],
    (18, 29): [(24, 25), (27, 28)],
    (24, 25): [],
    (27, 28): [],
    (31, 42): [(37, 38), (40, 41)],
    (37, 38): [],
    (40, 41): []}
    expected__leaves = [(6, 7), (9, 10), (24, 25), (27, 28), (37, 38), (40, 41)]
    expected__levelToIDs = {   0: [(12, 43), (0, 11)],
    1: [(31, 42), (18, 29), (6, 7), (9, 10)],
    2: [(40, 41), (37, 38), (27, 28), (24, 25)]}
    expected__idToLevel = {   (0, 11): 0,
    (6, 7): 1,
    (9, 10): 1,
    (12, 43): 0,
    (18, 29): 1,
    (24, 25): 2,
    (27, 28): 2,
    (31, 42): 1,
    (37, 38): 2,
    (40, 41): 2}


if __name__=='__main__':
    # test__latexParser__makeEnclosureTreeOfConsecutiveGroupGrenze()
    # test__latexParser__makeEnclosureTreeOfConsecutiveGroupGrenze0()
    test__latexParser__parentHavingChildrenOfTheirChildren()