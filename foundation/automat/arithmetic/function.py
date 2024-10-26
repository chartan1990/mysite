from abc import ABC
from copy import deepcopy

from foundation.automat.common.backtracker import Backtracker


class Function:
    """
    Should be able to take an AST (dictionary, key: node (tuple[label, id]), value: list of neighbours (list[tuple[label, id]])
    and do:
    (1) each of its inputs (one at a time) the 'root of the sub-AST' (sub-subject of the equation) through inverses primitive
    (2) substitute primitives in variables, evaluate the sub-AST and replace sub-AST with primitve node
    (3) form a bunch of displayable
        (a) "Scheme - styled_string" (with pretty option)
        (b) "Latex - styled_string"
        (c) MathML (html)


    """
    FUNC_NAMES = [] # TODO this need to filled in __init__, need to parse the folder automat.arithmetic.standard
    FUNCNAME_FILENAME = [] # TODO this need to be filled in __init__, need to parse the folder automat.arithmetic.standard

    def __init__(self, equation):
        self.eq = equation
        self.inverses = None

    def substitute(self, substitutionDictionary):
        """
        substituteDictionary is mapping from variable to primitives (numbers), this method finds self.FUNC_NAME sub-AST, in
        self.equation.ast, and then substitute each variable under each sub-AST using substituteDictionary

        :param substitutionDictionary: mapping from variable (str) to numbers
        :type substitutionDictionary: dict[str, float]
        """
        #error-checking
        if self.FUNC_NAME not in self.eq.functions: # FUNC_NAME only defined in child
            raise Exception("Function not in equation")
        if len(substitutionDictionary) == 0:
            raise Exception("Did not input substitution")
        for variableStr, value in substitutionDictionary.items():
            if variableStr not in self.eq.variables:
                raise Exception("Function not in equation")
        #look for all the self.FUNC_NAME, to make the substitutions
        ast = deepcopy(self.eq.ast)
        stack = [Backtracker(
            ast['='][0], # label
            None, # neighbours
            None, # argumentIdx
            None, # prev
            ast['='][1] # id
        )]
        while len(stack) != 0:
            current = stack.pop()
            neighbours = deepcopy(ast[current.label]) # cannot modify the data, that we are reading (race condition)
            hasFunction = False # does the sub-AST we are substituting, have a function as a input?
            for idx, neighbour in enumerate(neighbours):
                if current.label == self.FUNC_NAME: # FUNC_NAME only defined in child
                    if neighbour.label in self.eq.functions: # is a function
                        hasFunction = True # there is a function as input, so sub-AST cannot be removed
                        stack.append(Backtracker(
                            neighbour.label, # label
                            None, # neighbours
                            idx, # argumentIdx
                            current, # prev
                            neighbour.id # id
                        ))
                    elif neighbour.label in self.eq.variables: # is a variable
                        ast[(current.label, current.id)][idx] = substitutionDictionary[neighbour.label] # change variable to primitive (number)
                    else: # substituted value?
                        pass
                else: # plain old DFS
                    stack.append(Backtracker(
                        neighbour.label, # label
                        None, # neighbours
                        idx, # argumentIdx
                        current, # prev
                        neighbour.id # id
                    ))
            if (current.label == self.FUNC_NAME) and not hasFunction: # totally substitutable, no functions at all
                ast[(current.prev.label, current.prev.id)][current.prev.argumentIdx] = self._calculate(ast[(current.label, current.id)])
                del ast[(current.label, current.id)]
        return ast # substituted ast

    def inverse(self, argumentIdx, nodeIds):
        """
        make argumentIdx the subject of the subAST

        :param argumentIdx: the index of the argument of self(this function) to make into the subject of the formula
        :type argumentIdx: int
        :param nodeIds: node ids (of the AST) to do the inversion on
        :type nodeIds: list[int]
        :return: multiple returns
            - Modified Abstract Syntax Tree
            - mapping from FUNC_NAME to (number of increase in FUNC_NAME in new tree, will be negative if it decrease)
            - mapping from variable_str to (number of increase in variable_str in new tree, will be negative it decrease)
            - how many primitives were added?
            - how many total nodes were added to the AST?
        :rtype: tuple[
            dict[tuple[str, int], list[tuple[str, int]]],
            dict[str, int],
            dict[str, int],
            int,
            int]
        """
        ast = deepcopy(self.eq.ast)
        replacementDictionary = {}
        for key, value in ast.items():
            if key[1] in nodeIds:
                replacementDictionary[key] = value
        #will raise error if function of the node with `nodeId` is not equals to self.FUNC_NAME, handle in child.inverse
        (invertedResults, functionCountChange, variableCountChange,
         primitiveCountChange, totalNodeCountChange) = self.inverses[argumentIdx](
            replacementDictionary, self.eq.totalNodeCount)

        for oldKey, oldValue in invertedResults.items():
            if oldKey in ast: # due to addition of operations, `oldKey` might not exist in ast
                del ast[oldKey]
            ast[oldValue['newKey']] = oldValue['newValue']
        return ast, functionCountChange, variableCountChange, primitiveCountChange, totalNodeCountChange