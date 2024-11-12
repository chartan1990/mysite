class NoneSkipper:

	@classmethod
	def lenOrZero(cls, numOrNone):
		if numOrNone is None:
			return 0
		else:
			return len(numOrNone)