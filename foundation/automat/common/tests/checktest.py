import inspect
import pprint

from foundation.automat.common.checker import Booler


def test__isNum__decimal(verbose=False):
    print(Booler.isNum('0.5'))
    print(Booler.isNum('3.14'))
    print(Booler.isNum('1.618'))




if __name__=='__main__':
    test__isNum__decimal()