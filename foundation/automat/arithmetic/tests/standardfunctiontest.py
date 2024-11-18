import inspect
import pprint

from foundation.automat.arithmetic.function import Function

def test__trigNameListNotEmpty__Function(verbose=False):
    pp = pprint.PrettyPrinter(indent=4)
    print(inspect.currentframe().f_code.co_name, ' PASSED? ', len(Function.TRIGONOMETRIC_NAMES)>0)


if __name__=='__main__':
    print(Function.TRIGONOMETRIC_NAMES)