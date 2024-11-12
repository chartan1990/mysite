import importlib
import os

FUNCTOR_NAMES_TO_CLASS = []

#gather all the FUNC_NAME from folder sfunctor into FUNCTOR_NAMES_TO_CLASS
module_dir = os.path.dirname(__file__)
for module in os.listdir(module_dir):
	if module.endswith('.py') and module != '__init__.py':
		module_name = module[:-3] # remove .py
		module_obj = importlib.import_module(f'.{module_name}', package=__name__)
		for name, cls in inspect.getmembers(module_obj, predicate=inspect.isclass):
			FUNCTOR_NAMES_TO_CLASS[cls.FUNC_NAME] = cls