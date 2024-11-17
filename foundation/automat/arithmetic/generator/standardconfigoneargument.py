import os

from jinja2 import Environment, FileSystemLoader

from foundation.automat import AUTOMAT_MODULE_DIR
from foundation.automat.log import info
from foundation.automat.arithmetic.configuration.oneargumentconfiguration import FUNC_NAMES



class Standardconfigoneargument:


    @classmethod
    def generateConfigurations(cls, verbose=False):
        #copied from https://realpython.com/primer-on-jinja-templating/
        environment = Environment(loader=FileSystemLoader(os.path.join(AUTOMAT_MODULE_DIR, 'arithmetic', 'generator', 'template', 'configuration')))
        template = environment.get_template("standardoneargument.json.jinja2")

        for function_name, mapping in FUNC_NAMES.items():
            vorfname = function_name
            vorcname = mapping['class_name']
            hinfname = mapping['reverse_prefix']+function_name
            hincname = cls.upperFirstLetter(mapping['reverse_prefix']+vorcname.lower())
            vorcontent = template.render(
                function_name=vorfname,
                class_name=vorcname,
                reverse_class_name=hincname,
                imports=str(["from foundation.automat.arithmetic.function import Function"]).replace("'", '"'),
                reverse_imports=str([f"from foundation.automat.arithmetic.standard.{hincname.lower()} import {hincname}"]).replace("'", '"'),
                imports_as_str=str(mapping['import']).replace("'", '"'),
                code_as_str=str(mapping['code']).replace("'", '"'),
            )
            cls.writeToFile(f'{vorfname}.json', vorcontent, verbose=verbose)
            hincontent = template.render(
                function_name=hinfname,
                class_name=hincname,
                reverse_class_name=vorcname,
                imports=str(["from foundation.automat.arithmetic.function import Function"]).replace("'", '"'),
                reverse_imports=str([f"from foundation.automat.arithmetic.standard.{vorcname.lower()} import {vorcname}"]).replace("'", '"'),
                imports_as_str=str(mapping['reverse_import']).replace("'", '"'),
                code_as_str=str(mapping['reverse_code']).replace("'", '"'),
            )
            cls.writeToFile(f'{hinfname}.json', hincontent, verbose=verbose)

    @classmethod
    def upperFirstLetter(cls, word):
        word = str(word).lower()
        upperedWord = word[0].upper() + word[1:].lower()
        return upperedWord

    @classmethod
    def writeToFile(cls, filename, content, verbose=False):
        #we fix the filepath here:
        directory = os.path.join(AUTOMAT_MODULE_DIR, 'arithmetic', 'configuration', 'standard')
        with open(os.path.join(directory, filename), mode='w', encoding='utf-8') as file:
            file.write(content)
            if verbose:
                info(f"written {content} {os.linesep} {filename} to {directory}")


if __name__=='__main__':
    print('standardconfigoneargument START')
    Standardconfigoneargument.generateConfigurations(verbose=True)
    print('standardconfigoneargument END')