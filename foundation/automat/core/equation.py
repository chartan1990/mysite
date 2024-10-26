from copy import deepcopy
from importlib import import_module

from foundation.automat.common.backtracker import Backtracker
from foundation.automat.arithmetic.function import Function
from foundation.automat.parser import Parser

class Equation:
    """
    This is the entry point for automat, it is supposed to parse a string, that is the equation, into internal
    memory, which, for now, is a dictionary of list of nodes (node=tuple(label, id)). We call it Abstract
    Syntax Tree (ast for short).

    TODO ast should also be displayable in 2D/3D, and glow/shine and shift and rotate and all that
    TODO 2d/3d will help in debugging
    TODO PICKLE too? https://docs.python.org/3/library/pickle.html

    :param equationStr: the equation str to be parsed
    :type equationStr: str
    :param parserName: the name of the parser to be used
    :type parserName: str
    """
    def __init__(self, equationStr, parserName):
        """
        loads the parser with that name, throws a tantrum if parserName was not found. Also the constructor

        :param equationStr: the equation str to be parsed
        :type equationStr: str
        :param parserName: the name of the parser to be used
        :type parserName: str
        """
        self._eqs = equationStr
        self._parserName = parserName
        (self.ast, self.functions, self.variables, self.primitives,
         self.totalNodeCount) = Parser(parserName).parse(self._eqs)

    def makeSubject(self, variable):
        """
        make variable the subject of this equation

        :param variable:
        :type variable: str
        :return: a new AST that has variable as the subject of the formula
        :rtype: dict[tuple[str, int], list[tuple[str, int]]]
        """
        #error checking
        if variable not in self.variables:
            raise Exception("Variable Not Available")
        if self.variables[variable] > 1: #TODO, unable to further handle without more patterns like quadratic
            raise Exception("Cannot handle")

        #find path from subRoot to variable
        stack = [Backtracker(
            '=', #label
            None, #neighbours
            None, # argumentIdx
            None, #prev
            None, #id
        )]
        found = None
        while len(stack) != 0:
            current = stack.pop()
            if current.label == variable:
                found = current
                break
            for argumentIdx, (label, id) in enumerate(self.ast[current.label]):
                backtracker = Backtracker(
                    label, #label
                    None, #neighbours
                    argumentIdx, #argumentIdx
                    current, #prev
                    id
                )
                stack.append(backtracker)
            if found is None:
                raise Exception("No path to variable") # this shouldn't happen, most probably a parser error
            ops = [{
                'functionName':found.label,
                'argumentIdx':found.argumentIdx,
                'id':found.id,
                'lastId':found.prev.id if found.prev is not None else None
            }]
            while found.prev is not None:
                found = found.prev
                ops.append({
                    'functionName':found.label,
                    'argumentIdx':found.argumentIdx,
                    'id':found.id,
                    'lastId':found.prev.id if found.prev is not None else None
                })
            originalAst = deepcopy(self.ast)
            #apply the inverses
            while len(ops) != 0:
                op = ops.pop(0) # apply in reverse order (start with the one nearest to =)
                op_filename = Function.FUNCNAME_FILENAME[op['functionName']]
                op_foldername = "arithmetic.standard."+op_filename
                functionClass = getattr(import_module(op_foldername, op_filename))
                (invertedAst, functionCountChange,
                variableCountChange, primitiveCountChange, totalNodeCountChange) = functionClass(self).inverse(
                    op.argumentIdx, [op.id, op.lastId]
                )
                #update the `stat` of self
                self.ast = invertedAst
                for funcName, countChange in functionCountChange.items():
                    self.functions[funcName] += countChange
                for varStr, countChange in variableCountChange.items():
                    self.variables[varStr] += countChange
                self.primitives = primitiveCountChange
                self.totalNodeCount += totalNodeCountChange
            modifiedAst = deepcopy(self.ast)
            self.ast = originalAst# put back
            return modifiedAst


    def toString(self, format):
        """
        write the equation to string

        :param format: states the format to be used, to write to a string
        :type format: str
        """
        return Parser(format).unparse(self.ast)


if __name__=='__main__':
    eq0 = Equation('(= a (+ b c) )', 'scheme')