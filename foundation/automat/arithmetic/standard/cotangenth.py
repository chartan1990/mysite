
from foundation.automat.arithmetic.function import Function


class Cotangenth(Function):
    """

    """
    TYPE = 'trigonometric'
    FUNC_NAME = 'coth'

    def __init_subclass__(cls, **kwargs):
        kwargs['type'] = 'trigonometric'
        kwargs['funcName'] = 'coth'
        super().__init_subclass__(**kwargs)

    def __init__(self, equation):
        """

        """
        super().__init__(equation)
        self.reverses = {
            
                1: self._reverse1
            
        }

    
    def _reverse1(self, replacementDictionary, totalNodeCount):
        """
        replacementDictionary are the rows in the AST mapping that needs to be replaced.
        Aim of this function is to make #1 input, the subject
        replacementDictionary will always have exactly 2 rows, because of the nature of equality.
        One of the list have this tuple ('coth', nodeId) on the #2 argument. Since this is
        the function that will operate on it.

        :param replacementDictionary: 
        :type replacementDictionary: dict[tuple[str, int], list[tuple[str, int]]]
        :param totalNodeCount:
        :type totalNodeCount: int
        :return: tuple
         - input that was reversed
         - mapping from FuncName to how many of FuncName was added by this reversal, if its a negative, then its removal
         - total number of primitives that was added. If its negative, then primitives was removed
         - total number of nodes that was added. If its negative, the nodes were removed
        :rtype: tuple [
            dict[str, dict[str, Any]],
            dict[str, int],
            int,
            int
        ]
        """
        #error checking 
        if len(replacementDictionary) != 2: # always be 2 due to nature of equality
            raise Exception('replacementDictionary incorrect length')
        key0 = None
        key1 = None
        for key, value in replacementDictionary.items():
            if value[1][0] == self.FUNC_NAME:
                key0 = key
            else:
                key1 = key
        if key0 is None or key1 is None:
            raise Exception("replacementDictionary not according to format")
        
        from foundation.automat.arithmetic.standard.arccotangenth import Arccotangenth
        
        return {key0: {"newKey": key0, "newValue": [replacementDictionary[key1][0], [Arccotangenth.FUNC_NAME, replacementDictionary[key0][1][1]]]}, key1: {"newKey": [Arccotangenth.FUNC_NAME, key1[1]], "newValue": [replacementDictionary[key0][0]]}}, {Arccotangenth.FUNC_NAME: 1, FUNC_NAME: -1}, 0, 0

    

    def __calculate(self, v0):
        """
        Used to get the numerical value of this function, when all the inputs applied are numerical.
        Also used in substitution method of parent :class:`Function`

        
        :param v0: 0-th input of this function
        :type v0: float
        
        :return: calculated numerical result
        :rtype: float
        """
        from math import tanh
        num=1.0/tanh(v0)
        return num