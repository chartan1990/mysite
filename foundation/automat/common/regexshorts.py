import re

class Regexshorts:

	@classmethod
	def getMatchesOrNone(cls, pattern, searchText):
		"""
		Just a simple wrapper to simplify the syntax of re.search
		Only first the FIRST OCCURENCE of each capturing group!

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

	@classmethod
	def findAllMatches(cls, pattern, searchText):
		"""
		Just a simple wrapper to simplify the syntex of re.finditer
		Finds all the occurences of each capturing group
		Ex :- if we are looking for x in 'xyxyxy', 3 matches will be returned.

		:param pattern: regex
		:type pattern: str
		:param searchText: text to search in for `pattern`
		:type pattern: str
		:return: list containing every re.Match that fits the pattern
		:rtype: list[re.Match]
		"""
		return list(re.finditer(pattern, searchText))