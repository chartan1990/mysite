
class Node:
	"""
	holds the value and children in memory. 
	intermediate class for converting from in memory to pythonic array
	helps common.pythonicarray to convert from ctypearrays to pythonic arrays.
	"""
	def __init__(self, value, children=[]): # note to self, children=[] will give the same []...
		self.value = value
		self.children = children
	def get(self):
		return self.value
	def set(self, value):
		self.value = value
	def addChild(self, child):
		self.children.append(child)
	def getChildren(self):
		return self.children
	def iterable(self):
		return hasattr(self.value, '__getitem__') and hasattr(self.value, '__len__')