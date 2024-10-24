from foundation.nDisplay.helper.node import Node

class PythonicArray:
	"""
	Sometimes arrays are ctypes arrays, like:
	OpenGL.raw.GL._types.c_double_Array_4

	we need the to be in PythonicArray to be readable.
	"""

	@classmethod
	def convertToPyArray(cls, car):
	    """
	    put all the memory address into the stack, then modify the value accordingly
	    https://stackoverflow.com/questions/3106689/pointers-in-python

	    :param car: Ctype-ARray 
	    :type car:
	    :return:
	    :rtype:
	    """

	    root = Node(car)
	    stack = [root]
	    while len(stack) != 0:
	        current = stack.pop()
	        if current.iterable():
	            for idx in range(0, current.get().__len__()):
	                node = Node(current.get().__getitem__(idx), [])
	                current.addChild(node)
	                stack.append(node)
	    return cls.treeToList(root)#re-pass to pythonic

	@classmethod
	def treeToList(cls, node):
		"""
		recursive function that converts InMemory-Node (restricted to LIST) to Pythonic List (not just generator nor iterable)

		:param node:
		:type node:
		:return:
		:rtype:
		"""
		if len(node.getChildren()) == 0:
			return node.get()
		return [cls.treeToList(child) for child in node.getChildren()]