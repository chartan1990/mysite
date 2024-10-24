import os

from jinja2 import Environment, FileSystemLoader

from foundation.automat import AUTOMAT_MODULE_DIR
from foundation.automat.log import info
from foundation.automat.arithmetic.configuration.oneargumentconfigurationconfiguration import FUNC_NAMES



class Standardconfigoneargument:


    @classmethod
    def generateConfigurations(cls):
        #copied from https://realpython.com/primer-on-jinja-templating/
        environment = Environment(loader=FileSystemLoader(''))#TODO put in the full relative directory
        template = environment.get_template("standardoneargument.json.jinja2")

        for function_name, mapping in FUNC_NAMES.items():
            vorfname = function_name
            hinfname = mapping['reverse_prefix']+function_name
            hincname = cls.upperFirstLetter(hinfname)
            vorcontent = template.render(
                function_name=vorfname,
                class_name=mapping['class_name'],
                reverse_function_name=hinfname,
                imports_as_str=str(mapping['import']),
                code_as_str=str(mapping['code']),
            )
            cls.writeToFile(f'{vorfname}.json', vorcontent)
            hincontent = template.render(
                function_name=hinfname,
                class_name=hincname,
                reverse_function_name=vorfname,
                imports_as_str=str(mapping['reverse_import']),
                code_as_str=str(mapping['reverse_code']),
            )
            cls.writeToFile(f'{hinfname}.json', vorcontent)

    @classmethod
    def upperFirstLetter(cls, word):
        word = str(word).lower()
        upperedWord = word[0].upper() + word[1:].lower()
        return upperedWord

    @classmethod
    def writeToFile(cls, filename, content, verbose=False):
        #we fix the filepath here:
        directory = AUTOMAT_MODULE_DIR#
        with open(os.path.join(directory, filename), mode='w', encoding='utf-8') as file:
            file.write(content)
            if verbose:
                info(f"written {filename}")