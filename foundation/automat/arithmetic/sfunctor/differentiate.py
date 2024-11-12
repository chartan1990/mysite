class Differentiate(Function):
	"""

	"""
	FUNC_NAME = 'dif'

	def __init__(self, equation):
		"""

		"""
		super(Differentiate, self).__init__(equation)
		self.reverses = {

			1: self._reverse1
			#2: self._reverse2 # needs integrate to be done, then make x the subject....
		}

	def _reverse1(self, replacementDictionary, totalNodeCount):
		"""
		"""
		pass # TODO


	def _reverse2(self, replacementDictionary, totalNodeCount):
		"""
		"""
		pass # TODO


	def _calculate(self, v0, v1):
		"""
		Do BST, and apply to each node
		1. _chainRule (all-single-valued-functions)
		2. _productRule (/quotientRule) (*, /)
		3. _termRule (+, -)

		"""
		pass #TODO


	def _recursiveCalculate(self, subAST):
		"""
		#differentiate number =0
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ _variableAsConstant
		#differentiate variableNumber =0
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ _partialDifferentiation
		#differentiate variable != withrespecttoARG (IGNORE...TODO?)
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ _implicitDifferentiation
		#differentiate variable != withrespecttoARG
		#using x as an example
		(diff, ?):[(x, ?1), (y, ?2)]

		===
		(*, ?3):[(diff, ?4), (applyDiff((x, ?1)))]
		(diff, ?4):[(y, ?2), (x, ?5)]
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
		#differentiate variable == withrespecttoARG =1
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ _powerRule <<<<<<<<<<<<<<< this is part of Exponential FUNCTION....
		(diff, ?):[(^, ?1), (?, ?)]
		(^, ?1):[(?2, ?3), ([REAL_NUMBER], ?4)]

		===
		(*, ?5):[([REAL_NUMBER], ?4), (^, ?1)]
		(^, ?1):[(?2, ?3), (-, ?6)]
		(-, ?6):[([REAL_NUMBER], ?4), 1]
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ _chainRule (applyDiff is implemented in each FUNCTION)
		#differentiate single-valued functions (using sin as example)
		(diff, ?):[(sin, ?), (x, ?)]
		(sin, ?):[(?1, ?2)]

		=== applyDiff should do written on each individual functions
		(*, ?3):[(applyDiff(sin), ?), (diff, ?4)]
		(applyDiff(sin), ?):[(?1, ?2)],
		(diff, ?4):[(?1, ?2), (x, ?)]

		#######TODO try a more complex example like sec(x), to get a feel of how to program.
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ _productRule
		##differentiate (*, /) (using / as example)
		(diff, ?):[(/, ?1), (x, ?2)]
		(/, ?1):[(?3, ?4), (?5, ?6)]

		===
		(+, ?):[(*, ?7), (*, ?8)]
		(*, ?7):[(?3, ?4), (diff, ?9)]
		(*, ?8):[(diff, ?10), (?5, ?6)]
		(diff, ?9):[(?5, ?6), (x, ?)]
		(diff, ?10):[(?3, ?4), (x, ?)]
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ _termRule (differentiating equals is the same)
		#differentiate (+, -) (using - as example)
		(diff, ?):[(-, ?1), (x, ?)]
		(-, ?1):[(?3, ?4), (?5, ?6)]

		===
		(-, ?1):[(diff, ?7), (diff, ?8)]
		(diff, ?7):[(?3, ?4)]
		(diff, ?8):[(?5, ?6)]

		"""
		pass