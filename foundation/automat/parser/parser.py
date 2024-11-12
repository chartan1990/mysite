from abc import ABC
import copy


class Parser(ABC):
    """
    Abstract class for :class:`Equation` to parse an equation string

    :param parserName: the name of the parser
    :type parserName: str
    """
    PARSERNAME_PARSERCLASSSTR = {
        'scheme':'Schemeparser',
        'latex':'Latexparser',
        'html':'Htmlparser'
    }

    def __init__(self, parserName):
        """
        constructor, but initialise the correct parser child instead

        :param parserName: the name of the parser
        :type parserName: str
        """
        self.parserName = parserName
        self.PARSERNAME_PARSERCLASSSTR = Parser.PARSERNAME_PARSERCLASSSTR

    def parse(self, equationStr):
        """
        get the parser class lazily (because of circular import)
        and then initialises it

        :param equationStr: equation string to be parsed to ast
        :type equationStr: str
        :return: tuple of
            - ast (Abstract Syntax Tree), map, key:tuple(label, id), value:list[tuple[label, id]]
            - functions (map from function_label_str to number of such functions there are in the equation
            - variables (map from variable_label_str to number of such variables there are in the equation
            - primitives (amount of primitives there are in the equation
            - totalNodeCount (total number of nodes in the ast)
        :rtype: tuple[
            dict[tuple[str, int], list[tuple[str, int]]],
            dict[str, int],
            dict[str, int],
            int,
            int]
        """
        # will raise exception if parserName not in PARSERNAME_PARSERCLASSSTR
        # actual parsing is done in individual child class
        from foundation.automat.parser.sorte import Schemeparser, Latexparser, Htmlparser  #prevents circular import
        parser = globals()[self.PARSERNAME_PARSERCLASSSTR[self.parserName]](equationStr)
        ast, functions, variables, primitives, totalNodeCount = parser._parse()
        return ast, functions, variables, primitives, totalNodeCount



if __name__=='__main__':
    pass
    #import pprint
    #pp = pprint.PrettyPrinter(indent=4)
    #eqs = 'a+b=c'
    #latexParser = Latexparser(eqs, verbose=True)
    #ast = latexParser.ast
    #print('*********ast:')
    #pp.pprint(ast)
    """
    ast = {
    ('=', 0):[(('a', 1), ('+', 2)],
    ('+', 2):[('b', 3), ('c', 4)]
    }
    """
    #unparsedStr = latexParser._unparse()
    #print(f'***********unparsedStr: modorimashitaka: {eqs==unparsedStr}')
    #print(unparsedStr)

    #TODO