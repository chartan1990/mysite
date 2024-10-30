class EnclosureTree:

    @classmethod
    def makeEnclosureTree(cls, listOfPoss, firstContainsSecond, getId):
        """
        
        :param listOfPoss: list of objects
        :type: list[Any]
        :param firstContainsSecond: a method that takes obj0 from listOfPoss (as first object), and obj1 from listOfPoss (as second object)
        and returns if obj0 CONTAINS obj1 ? Bool
        :type getPosMethod: Callable[Any, Bool]
        :param getId: a method that takes an object from listOfPoss, and returns its ID
        :return: tuple[
            rootId,
            dictionary where key is ID and value is a list of ID, whom are connected to the key (its children)
        ]
        :rtype: tuple[
            int,
            dict[]
        ]
        """
        if len(listOfPoss) == 0:
            return {}
        enclosureTree = {}
        for obj0 in listOfPoss:
            obj0ID = getId(obj0)
            for obj1 in listOfPoss:
                obj1ID = getId(obj1)
                if firstContainsSecond(obj0, obj1):
                    existingChildren = enclosureTree.get(obj0ID, [])
                    existingChildren.append(obj1ID)
                    enclosureTree[obj0ID] = existingChildren
                elif firstContainsSecond(obj1, obj0):
                    existingChildren = enclosureTree.get(obj1ID, [])
                    existingChildren.append(obj0ID)
                    enclosureTree[obj1ID] = existingChildren
        #all roads lead to rome (find root of tree) TODO might need to add cycle detection
        rootId = getId(listOfPoss[0])
        checkAgain = True
        while checkAgain: # keep going up
            checkAgain = False
            for pos, childenPos in enclosureTree.items():
                if rootId in childenPos:
                    rootId = pos #pos is parent of rootId
                    checkAgain = True # might still have parent, so we check again.
        return rootId, enclosureTree

    @classmethod
    def makeEnclosureTreeWithLevel(cls, listOfPoss, firstContainsSecond, getId):
        """
        
        :param listOfPoss: list of objects
        :type: list[Any]
        :param firstContainsSecond: a method that takes obj0 from listOfPoss (as first object), and obj1 from listOfPoss (as second object)
        and returns if obj0 CONTAINS obj1 ? Bool
        :type getPosMethod: Callable[Any, Bool]
        :param getId: a method that takes an object from listOfPoss, and returns its ID
        :return: tuple[
            rootId,
            dictionary where key is ID and value is a list of ID, whom are connected to the key (its children),
            dictionary where key is level, and value is a list of ID, that are in the level
        ]
        :rtype: tuple[
            int,
            dict[],
            dict[]
        ]
        """
        rootId, enclosureTree = cls.makeEnclosureTree(listOfPoss, firstContainsSecond, getId)
        levelToIDs = {0:[rootId]}
        queue = [{'id':rootId, 'level':0}]
        while len(queue) > 0:
            current = queue.pop()
            for neighbourId in enclosureTree[current['id']]:
                neighbourLevel = current['level']+1
                queue.append({'id':neighbourId, 'level':neighbourLevel})
                #
                levelIDList = levelToIDs.get(neighbourLevel, [])
                levelIDList.append(neighbourId)
        return rootId, enclosureTree, levelIDList