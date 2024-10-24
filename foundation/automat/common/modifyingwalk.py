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
			if isinstance(node, collection.abc.Mapping): # For mappings (like dict)
				for idx, (k, v) in enumerate(node.items()):
					stack.append({'node':k, 'iskey':True, 'key':k, 'idx':idx, 'parent':current})
					stack.append({'node':v, 'iskey':False, 'key':k, 'idx':idx, 'parent':current})
			elif isinstance(node, collection.abc.Iterable): # For any iterable (like list, tuple, set)
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
				pass # Example would require async handling logic here
			elif hasattr(node, '__anext__'): # For asynchronous generators
				# Handles asynchronously with await and asyncio (async context needed)
				pass # Example would require async handling logic here
			else:  # Primitive types or unsupported types (str, int, float, etc.)
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