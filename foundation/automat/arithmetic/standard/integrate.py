class Integrate(Function):
	"""

	"""
	FUNC_NAME = 'dif'

	def __init__(self, equation):
		"""

		"""
		super(Integrate, self).__init__(equation)
		self.reverses = {

			1: self._reverse1
			#2: self._reverse2 # needs differentiate to be done, then make x the subject....
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
		Definite integral?
		"""
		pass #TODO