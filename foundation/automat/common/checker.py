import inspect

class Booler:
    """
    Methods in this class always return boolean
    """

    @classmethod
    def isFloat(cls, num):
        try:
            float(num)
            return True
        except:
            return False
