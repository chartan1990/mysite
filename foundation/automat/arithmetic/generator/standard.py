from json import loads
import os
import re

from foundation.automat import AUTOMAT_MODULE_DIR
from foundation.automat.common import getMatchesOrNone, traverseAndEdit

class StandardFunctionClassGenerator:

    def __init__(self):
        #read the configuration file for standard functions
        self.standardConfigFileFolder = os.path.join(os.path.dirname(__file__), '..', 'configuration')
        self.standardConfigFileName = 'standard_function_config.json'
        self.standardConfigFilePath = os.path.join(self.standardConfigFileFolder, self.standardConfigFileName)

    def generateClass(self, verbose=False):
        """
        Generates all the standard function in Python and dumps them into arithmetic.configuration.standard

        TODO run standardconfigoneargument.py
        
        shorthands used in configurations --:
        '@fN@' -: funcName
        '@cN@' -: className
        '@vfN@' -: variableName of funcName
        '@vrD@' -: variableName of replacementDict
        '@vk0@' -: variableName of key0
        '@vk1@' -: variableName of key1
        '@vtN@' -: variableName of totalNodeCount
        '@vnK@' -: variableName of newKey
        '@vnV@' -: variableName of newValue
        ##CODE WITH INPUTS##
        '@id_<0>_<1>@' -: replacementDict[key<0>][<1>][1] {nodeId of <1> argument of operator key<0>}
        '@item_<0>_<1>@' -: replacementDict[key<0>][<1>] {<1> argument of operator key<0>}
        '@fN_<0>@' -: funcName <0>
        '@idk_<0>@' -: key<0>[1] {nodeId of key<0>}

        :param verbose: prints written file path to logger
        :type verbose: bool
        """

        #copied from https://realpython.com/primer-on-jinja-templating/
        environment = Environment(loader=FileSystemLoader(os.path.join(AUTOMAT_MODULE_DIR, 'arithmetic', 'generator', 'function')))# put in the full directory

        configJSON = loads(self.standardConfigFilePath)
        for config in configJSON:
            #get all keys starting with init
            keysStartingWithInit = list(filter(lambda key: key.startswith('init_'), config.keys()))
            initSubstitutionDict = {}
            for initKey in keysStartingWithInit:
                initSubstitutionDict[config[initKey]['code']] = config[initKey]['full']
            replacementDictVN = f"{initSubstitutionDict['@vrD@']}"
            def subShortHandWithActualCode(value):
                if not isinstance(value, str):
                    return value
                resultStr = ''
                keyword = ''
                inKeywordStart = False
                for c in value:
                    if c == '@' and not inKeywordStart:
                        inKeywordStart = True
                    elif c == '@' and inKeywordStart:
                        #here we have keyword
                        inKeywordStart = False
                        if keyword.startswith('idk_'):
                            keyId = getMatchesOrNone('idk_(\\d+)', keyword)
                            substituteStr = f'key{keyId}[1]'
                        elif keyword.startswith('id_'):
                            keyIdx, argumentIdx = getMatchesOrNone('id_(\\d+)_(\\d+)', keyword)
                            substituteStr = f'{replacementDictVN}[key{keyIdx}][{argumentIdx}][1]'
                        elif keyword.startswith('item_'):
                            keyIdx, argumentIdx = getMatchesOrNone('item_(\\d+)_(\\d+)', keyword)
                            substituteStr = f'{replacementDictVN}[key{keyIdx}][{argumentIdx}]'
                        elif keyword.startswith('fN_'):
                            funcName = getMatchesOrNone('fN_(\\.+)', keyword)
                            substituteStr = f'key{funcName}[1]'
                        else:
                            raise Exception("Undefined Keyword")
                        resultStr += substituteStr
                    elif inKeywordStart:
                        keyword += c
                    else:
                        resultStr += c
            returnReversesCode = []
            for idx, reverseReturn in enumerate(config['return_reverse']["reversedAst"]):
                functionReturns = traverseAndEdit(reverseReturn, subShortHandWithActualCode)
                functionCountAdded = functionReturns['functionCountAdded']
                del functionReturns['functionCountAdded']
                primitiveCountAdded = functionReturns['primitiveCountAdded']
                del functionReturns['primitiveCountAdded']
                totalNodeCountAdded = functionReturns['totalNodeCountAdded']
                del functionReturns['totalNodeCountAdded']
                #fill template for reverse function
                reverseFTemplate = environment.get_template("function_reverse.py.jinja2")
                renderedReverseFTemplate = reverseFTemplate.render({
                    'idx':idx,
                    'vReplacementDict':initSubstitutionDict['@vrD@'],
                    'vTotalNodeCount':initSubstitutionDict['@vtN@'],
                    'funcName':initSubstitutionDict['@fN@'],
                    'vKey0':initSubstitutionDict['@vk0@'],
                    'vKey1':initSubstitutionDict['@vk1@'],
                    'reversedDict':functionReturns,
                    'functionCountAdded':functionCountAdded,
                    'primitivesCountAdded':primitiveCountAdded,
                    'totalNodeCountAdded':totalNodeCountAdded
                })
                returnReversesCode.append(renderedReverseFTemplate)

            #fill template for calculate function
            calculateFTemplate = environment.get_template("function_calculate.py.jinja2")
            renderedCalculateFTemplate = calculateFTemplate.render({
                'num_of_variables':config['return_calculation'][0]['variableCount'],
                'import_as_str':config['return_calculation'][0]['imports'],
                'code_as_str':config['return_calculation'][0]['code']
            })

            #main template for this class
            mainFTemplate = environment.get_template("function.py.jinja2")
            renderedMainFTemplate = mainFTemplate.render({
                'className':initSubstitutionDict['@cN@'],
                'funcName':initSubstitutionDict['@fN@'],
                'num_of_variables':config['return_calculation'][0]['variableCount'],
                'reverseFunctionStrs':returnReversesCode,
                'calculateFunctionStr':renderedCalculateFTemplate
            })
            fileName = f"{initSubstitutionDict['@cN@'].lower()}.py"
            cls.writeToFile(fileName, renderedMainFTemplate, verbose=verbose)
        return 


    @classmethod
    def writeToFile(cls, filename, content, verbose=False):
        #we fix the filepath here:
        directory = AUTOMAT_MODULE_DIR#
        with open(os.path.join(directory, filename), mode='w', encoding='utf-8') as file:
            file.write(content)
            if verbose:
                info(f"written {filename}")


if __name__=='__main__':
    print('generating standard function class files START')
    Standardconfigoneargument.generateConfigurations(verbose=True)
    print('generating standard function class files END')