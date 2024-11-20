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

    enclosureTree, levelToIDs, idToLevel, leaves = EnclosureTree.makeEnclosureTreeWithLevelRootLeaves(listPoss, firstContainsSecond, getId)
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
    expected__levelToIDs = {   0: [   (6, 9),
           (12, 15),
           (17, 20),
           (21, 23),
           (31, 32),
           (34, 37),
           (45, 47),
           (49, 52),
           (60, 61),
           (64, 67),
           (68, 70)],
    1: [(0, 24), (25, 71)]}
    expected__idToLevel = {   (0, 24): 1,
    (6, 9): 0,
    (12, 15): 0,
    (17, 20): 0,
    (21, 23): 0,
    (25, 71): 1,
    (31, 32): 0,
    (34, 37): 0,
    (45, 47): 0,
    (49, 52): 0,
    (60, 61): 0,
    (64, 67): 0,
    (68, 70): 0}
    print(
        inspect.currentframe().f_code.co_name, 
        ' PASSED? ', 
        expected__enclosureTree==enclosureTree and expected__leaves==leaves and expected__levelToIDs==levelToIDs and expected__idToLevel==idToLevel
    )



if __name__=='__main__':
    test__latexParser__makeEnclosureTreeOfConsecutiveGroupGrenze(False)