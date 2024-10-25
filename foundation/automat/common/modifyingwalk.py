import collections.abc
import decimal
from typing import Callable, TypeVar, Any
from copy import deepcopy

T = TypeVar('T') # Define a generic type variable

class Pythondatastructuretraversal:
	"""
	"""

	@classmethod
	def traverseAndEdit(cls, pyds:Any, procedure:Callable[[T], T]) -> Any:
		"""
		traverses the pyds in Depth-First fashion, calling the `procedure` on all primitives (str, float, int), and then replacing the primitive on the output of the `procedure`

		:param pyds: a python datastructure that can be any combination of list, tuple, and/or dictionary
		:type pyds: Any
		:param procedure: A callable that takes a string, and returns a string
		:type procedure: Callable[[T], T]
		:return: the original input data structure, with the primitives modified by `procedure` but structure untouched
		:rtype: Any
		"""
		stack = [{'node':pyds, 'key':None, 'idx':None, 'parent':None}] # root node
		while len(stack) != 0:
			current = stack.pop()
			node = current['node']
			if isinstance(node, collections.abc.Mapping): # For mappings (like dict)
				for idx, (k, v) in enumerate(node.items()):
					stack.append({'node':k, 'iskey':True, 'key':k, 'idx':idx, 'parent':current})
					stack.append({'node':v, 'iskey':False, 'key':k, 'idx':idx, 'parent':current})
			elif isinstance(node, collections.abc.Iterable): # For any iterable (like list, tuple, set)
				for idx, i in enumerate(node):
					stack.append({'node':i, 'iskey':None, 'idx':idx, 'parent':current})
			elif hasattr(node, '__next__'): # For regular generators
				while True:
					try:
						i = node.__next__()
						stack.append({'node':i, 'iskey':None, 'idx':idx, 'parent':current})
					except StopIteration:
						break
			elif hasattr(node, '__aiter__'): # For asynchronous iterators
				# Handles asynchronously with await and asyncio (async context needed)
				raise Exception("Cannot handle Async Iterator") # Example would require async handling logic here
			elif hasattr(node, '__anext__'): # For asynchronous generators
				# Handles asynchronously with await and asyncio (async context needed)
				raise Exception("Cannot handle Async Generator") # Example would require async handling logic here
			else:  # Primitive types or unsupported types (str, int, float, etc.)
				#TODO this is untested, and probably will not work because python is pass-by-value
				if isinstance(node, (str, float, int, decimal.Decimal, bool, type(None))):
					modifiedValue = procedure(node) 
					if current['key'] is None: # was from a mapping
						current['parent'][current['idx']] = modifiedValue # have to do it like this because python is pass by value.... sickening? or protective? depends on the situation
					else: # something with key, value BS
						if current['iskey']:
							current['parent'][modifiedValue] = current['parent'].pop(current['key'])
						else: # its value
							current['parent'][current['key']] = modifiedValue
				else:
					# Handle anything else that isn't a standard Python iterable or primitive
					pass
		return pyds


	@classmethod
	def recursiveNaiveTraverseAndEdit(cls, pyds:Any, procedure:Callable[[T], T]) -> Any:
		"""
		traverses the pyds recursively, but converts everything to either a dictionary or list
		raises Exception if we see Async

		:param pyds:
		:type pyds:
		:param procedure:
		:type procedure:
		"""
		if isinstance(pyds, collections.abc.Mapping): # For mapping (like dict), just convert to dictionary
			return dict([(cls.recursiveNaiveTraverseAndEdit(key, procedure), cls.recursiveNaiveTraverseAndEdit(value, procedure)) for key, value in pyds.items()])
		#<class 'str'> is iterable too...
		#elif isinstance(pyds, collections.abc.Iterable) or hasattr(pyds, '__next__'): # For any iterable (like list, tuple, set) AND generators
		elif isinstance(pyds, list): # convert to list
			return [cls.recursiveNaiveTraverseAndEdit(item, procedure) for item in pyds]
		elif isinstance(pyds, tuple): # convert to tuple
			return tuple([cls.recursiveNaiveTraverseAndEdit(item, procedure) for item in pyds])
		elif isinstance(pyds, set): #convert to set
			return set([cls.recursiveNaiveTraverseAndEdit(item, procedure) for item in pyds])
			# else:
			# 	raise Exception(f'unhandled type: {type(pyds)}')
		elif hasattr(pyds, '__anext__') or hasattr(pyds, '__aiter__'): # scream if you see async iterator and generator
			raise Exception(f'Async generator {hasattr(pyds, "__anext__")} or iterator {hasattr(pyds, "__aiter__")} Unhandled')
		else: # has to be a primitive type... right? Naive
			#print(type(pyds))
			#print(pyds)

			return procedure(pyds)


#DEV TEST
if __name__=='__main__':
	configuration = {
		"init_funcName": {"full": "arccos", "code": "@fN@"},
		"init_className": {"full": "Arccos", "code": "@cN@"},
		"init_variableName_funcName": {"full": "FUNC_NAME", "code": "@vfN@"},
		"init_variableName_key0": {"full": "key0", "code": "@vk0@"},
		"init_variableName_key1": {"full": "key1", "code": "@vk1@"},
		"init_variableName_replacementDictionary": {"full": "replacementDictionary", "code": "@vrD@"},
		"init_variableName_totalNodeCount": {"full": "totalNodeCount", "code": "@vtN@"},
		"init_variableName_newKey": {"full": "newKey", "code": "@vnK@"},
		"init_variableName_newValue": {"full": "newValue", "code": "@vnV@"},
		"return_reverse": {
		"reversedAst": [
		  {
			"@vk0@": {
				"@vnK@": "@vk0@",
				"@vnV@": ["@item_1_0@", ["@fN_cos@", "@id_0_1@"]]
			},
			"@vk1@": {
				"@vnK@": ["@fN_cos@", "@idk_1@"],
				"@vnV@": ["@item_0_0@"]
			},
			"functionCountAdded": {"@fN_cos": 1, "@fN@": -1},
			"primitiveCountAdded": 0,
			"totalNodeCountAdded": 0
			}
		]
		},
		"return_calculation": [{
		"imports": ["from math import acos"],
		"variableCount": 1,
		"code": ["acos(v0)"]
		}]
	}
	def decodeConfigurationSymbols(text):
		try:
			return text.replace('@', '') # just remove all the @....
		except:
			return text
	pyds = Pythondatastructuretraversal.recursiveNaiveTraverseAndEdit(configuration, decodeConfigurationSymbols)
	import pprint
	pp = pprint.PrettyPrinter(indent=4)
	pp.pprint(pyds)
