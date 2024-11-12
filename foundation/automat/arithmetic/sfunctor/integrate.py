class Integrate(Function):
	"""

	"""
	FUNC_NAME = 'int'

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


	def _recursiveCalculate(self, subAST):
		"""
		There is a need to add a constant term... But this should only be done at the end of the whole calculation...
		If partial integration is done... need to add a term that is a UNKNOWN FUNCTION in other variables that are not withrespecttovariable

@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@_partialIntegration
		#integrating withrespectto x, then IGNORE the other 'variables'
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@_powerRule <<<<< part of exponential FUNCTION
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@_termRule (also works on =)
		#meant for both +,-; but we use - as example

		(int, ?1):[(-, ?2), (x, ?3)]
		(-, ?2):[(A, ?4), (B, ?5)]

		===
		(-, ?2):[(int, ?6), (int, ?7)]
		(int, ?6):[(A, ?4), (x, ?3)]
		(int, ?7):[(B, ?5), (x, ?3)]
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@_chainRule (applyInt is implemented in each FUNCTION)
		#for single-valued functions, but we use sin as example

		(int, ?1):[(sin, ?2), (x, ?3)]
		(sin, ?2):[(A, ?4)]

		===
		(*, ?5):[(applyInt(sin), ?2), (diff, ?6)]
		(applyInt(sin), ?2):[(A, ?4)]
		(diff, ?6):[(A, ?4), (x, ?3)]

		#######TODO try a more complex example like sec(x), to get a feel of how to program.
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@_partialFractions <<<<<<<<<<< part of divide FUNCTION (simplifying...)
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@_integrationByParts
		(int, ?1):[(*, ?2), (x, ?3)]
		(*, ?2):[(A, ?4), (B, ?5)]

		===
		(-, ?6):[(*, ?7), (int, ?8)]
		(*, ?7):[(A, ?4), (int, ?9)]
		(int, ?9):[(B, ?5), (x, ?3)]
		(int, ?8):[(*, ?10), (int, ?11)]
		(*, ?10):[(diff, ?12), (int, ?13)]
		(int, ?11):[(B, ?5), (x, ?3)]
		(diff, ?12):[(A, ?4), (x, ?3)]
		(int, ?13):[(B, ?5), (x, ?3)]
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@_returningIntegrals
		#TODO integrals that become the 'same' as the left-hand side, so can be added back to itself, to terminate the program
		#'same' is hard, need simplication... and then searchTree for simplication...
		"""

		pass