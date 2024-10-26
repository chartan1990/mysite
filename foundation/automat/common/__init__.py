import os
import importlib
import inspect


#Automatically import all Python files in the package directory
module_dir = os.path.dirname(__file__)
for module in os.listdir(module_dir):
	if module.endswith('.py') and module != '__init__.py':
		module_name = module[:-3] # remove .py
		module_obj = importlib.import_module(f'.{module_name}', package=__name__)
		for name, cls in inspect.getmembers(module_obj, predicate=inspect.isclass):
			globals()[name] = cls # export the class as well
			for method_name, method in inspect.getmembers(cls, predicate=inspect.ismethod):
				if (isinstance(inspect.getattr_static(cls, method_name), staticmethod)) or \
				   (isinstance(inspect.getattr_static(cls, method_name), classmethod)):
				   #is a static or class method
				   globals()[method_name] = method