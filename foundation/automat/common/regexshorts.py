import re

class Regexshorts:

	@classmethod
	def getMatchesOrNone(cls, pattern, searchText):
		"""
		Just a simple wrapper to simplify the syntax of re.search

		:param pattern: regex
		:type pattern: str
		:param searchText: text to search in for `pattern`
		:type pattern: str
		:return: tuple containing all the matches, or empty tuple
		:rtype: tuple
		"""
		matches = re.search(pattern, searchText)
		if matches: #if matches not None
			return matches.groups()
		return ()