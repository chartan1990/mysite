from jinja2 import Environment, FileSystemLoader
from json import loads
import os
import re

from foundation.automat import AUTOMAT_MODULE_DIR, info
from foundation.automat.common import getMatchesOrNone, recursiveNaiveTraverseAndEdit

class StandardFunctionClassGenerator:

    def __init__(self):
        #read the configuration file for standard functions
        self.standardConfigFileFolder = os.path.join(AUTOMAT_MODULE_DIR, 'arithmetic', 'configuration','standard')
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        self.pformat = pp.pformat

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
        environment = Environment(loader=FileSystemLoader(os.path.join(AUTOMAT_MODULE_DIR, 'arithmetic', 'generator', 'template', 'standard', 'function')))# put in the full directory
        for filename in os.listdir(self.standardConfigFileFolder):
            if filename.endswith('.json'): # then its good! sei vorsichtung um nicht zu non-configuration-files zu beitragen
                if verbose:
                    info(f'processing {filename}')
                JSONfile = open(os.path.join(self.standardConfigFileFolder, filename), 'r')

                config = loads(JSONfile.read())
                JSONfile.close()
                #get all keys starting with init
                keysStartingWithInit = list(filter(lambda key: key.startswith('init_'), config.keys()))
                initSubstitutionDict = {}
                initSubstitutionDictStr = {}
                for initKey in keysStartingWithInit:
                    if 'string' in initKey:
                        initSubstitutionDictStr[config[initKey]['code']] = config[initKey]['full']
                    else:
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
                                keyId = getMatchesOrNone('idk_(\\d+)', keyword)[0]
                                substituteStr = f'key{keyId}[1]'
                            elif keyword.startswith('id_'):
                                keyIdx, argumentIdx = getMatchesOrNone('id_(\\d+)_(\\d+)', keyword)
                                substituteStr = f'{replacementDictVN}[key{keyIdx}][{argumentIdx}][1]'
                            elif keyword.startswith('item_'):
                                keyIdx, argumentIdx = getMatchesOrNone('item_(\\d+)_(\\d+)', keyword)
                                substituteStr = f'{replacementDictVN}[key{keyIdx}][{argumentIdx}]'
                            elif keyword.startswith('fN_'):
                                funcName = getMatchesOrNone('fN_(.+)', keyword)[0]
                                substituteStr = funcName
                            elif keyword.startswith('cN_'):
                                funcName = getMatchesOrNone('cN_(.+)', keyword)[0]
                                substituteStr = funcName
                            else:
                                if f'@{keyword}@' in initSubstitutionDict:
                                    substituteStr = initSubstitutionDict[f'@{keyword}@']
                                elif f'@{keyword}@' in initSubstitutionDictStr:
                                    substituteStr = initSubstitutionDictStr[f'@{keyword}@']
                                    substituteStr = f'"{substituteStr}"'
                                else:
                                    substituteStr = keyword # get vk0, leave it there
                            resultStr += substituteStr
                            keyword = ""
                        elif inKeywordStart:
                            keyword += c
                        else:
                            resultStr += c
                    return resultStr
                returnReversesCode = []
                for idx, reverseReturn in enumerate(config['return_reverse']["reversedAst"]):
                    functionReturns = recursiveNaiveTraverseAndEdit(reverseReturn, subShortHandWithActualCode)
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
                        #pretty Format makes bad indentation => unrunnable TODO
                        'reversedDict':str(functionReturns).replace("'", ""),#self.pformat(functionReturns).replace("'", ""), # we are assuming that pformat string always have use '"' to quote strings
                        'functionCountAdded':str(functionCountAdded).replace("'", ""),#self.pformat(functionCountAdded).replace("'", ""), # we are assuming that pformat string always have use '"' to quote strings
                        'primitivesCountAdded':primitiveCountAdded,
                        'totalNodeCountAdded':totalNodeCountAdded,
                        'imports':config['return_reverse']['imports'] if 'imports' in config['return_reverse'] else [],
                    })
                    returnReversesCode.append(renderedReverseFTemplate)

                #fill template for calculate function
                calculateFTemplate = environment.get_template("function_calculate.py.jinja2")
                importings = config['return_calculation'][0]['imports']
                renderedCalculateFTemplate = calculateFTemplate.render({
                    'num_of_variables':config['return_calculation'][0]['variableCount'],
                    'import_as_str':importings[0] if len(importings) > 0 else "", # TODO for now we just take the first one
                    'code_as_str':config['return_calculation'][0]['code'][0] # TODO for now we just take the first one
                })

                #main template for this class
                mainFTemplate = environment.get_template("function.py.jinja2")
                renderedMainFTemplate = mainFTemplate.render({
                    'type':initSubstitutionDict['@te@'] if '@te@' in initSubstitutionDict else 'other',
                    'className':initSubstitutionDict['@cN@'],
                    'funcName':initSubstitutionDict['@fN@'],
                    'num_of_variables':config['return_calculation'][0]['variableCount'],
                    'reverseFunctionStrs':returnReversesCode,
                    'calculateFunctionStr':renderedCalculateFTemplate,
                    'imports':config['imports']
                })
                fileName = f"{initSubstitutionDict['@cN@'].lower()}.py"
                self.writeToFile(fileName, renderedMainFTemplate, verbose=verbose)


    def writeToFile(self, filename, content, verbose=False):
        #we fix the filepath here:
        directory = os.path.join(AUTOMAT_MODULE_DIR, 'arithmetic', 'standard')#
        with open(os.path.join(directory, filename), mode='w', encoding='utf-8') as file:
            file.write(content)
            if verbose:
                info(f"written {filename}")


if __name__=='__main__':
    print('generating standard function class files START')
    StandardFunctionClassGenerator().generateClass(verbose=True)
    print('generating standard function class files END')