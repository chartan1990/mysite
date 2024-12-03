# class GrowTreeMixin: # TODO find out how to do MixIn properly


#     def growTree(self, listOfPoss, firstContainsSecond, getId):
#         """
        
#         :param listOfPoss: list of objects
#         :type: list[Any]
#         :param firstContainsSecond: a method that takes obj0 from listOfPoss (as first object), and obj1 from listOfPoss (as second object)
#         and returns if obj0 CONTAINS obj1 ? Bool
#         :type getPosMethod: Callable[Any, Bool]
#         :param getId: a method that takes an object from listOfPoss, and returns its ID
#         :return: tuple[
#             rootId,
#             dictionary where key is ID and value is a list of ID, whom are connected to the key (its children)
#         ]
#         :rtype: tuple[
#             int,
#             dict[]
#         ]
#         """
#         self.listOfPoss = listOfPoss
#         if len(listOfPoss) == 0:
#             return {}
#         self.enclosureTree = dict(map(lambda obj: (getId(obj), []),listOfPoss))
#         for obj0 in listOfPoss:
#             obj0ID = getId(obj0)
#             for obj1 in listOfPoss:
#                 obj1ID = getId(obj1)
#                 if obj0ID == obj1ID:
#                     continue 
#                 if firstContainsSecond(obj0, obj1):
#                     existingChildren = enclosureTree.get(obj0ID, [])
#                     if obj1ID not in existingChildren:
#                         existingChildren.append(obj1ID)
#                         enclosureTree[obj0ID] = existingChildren
#                 elif firstContainsSecond(obj1, obj0):
#                     existingChildren = enclosureTree.get(obj1ID, [])
#                     if obj0ID not in existingChildren:
#                         existingChildren.append(obj0ID)
#                         enclosureTree[obj1ID] = existingChildren
#         return self.enclosureTree

# class FindRootMixin:

#     def __init__(self, *args, **kwargs):
#         #TODO code can be a mixin too... CheckForPropertiesMixin lol
#         if not(hasattr(self, 'growTree') and callable(self.growTree)):# or not(hasattr(self, 'enclosureTree') and self.enclosureTree is not None and len(self.enclosureTree) > 0):
#             #should we import the mixin for the user?
#             setattr(self, 'growTree', GrowTreeMixin.growTree)

#     def findRoot(self, listOfPoss, firstContainsSecond, getId):
#         if not(hasattr(self, 'enclosureTree') and self.enclosureTree is not None and len(self.enclosureTree) > 0):
#             self.enclosureTree = self.growTree(listOfPoss, firstContainsSecond, getId)
#         #all roads lead to rome (find root of tree) TODO might need to add cycle detection
#         self.rootId = getId(self.listOfPoss[0])
#         checkAgain = True
#         while checkAgain: # keep going up
#             checkAgain = False
#             for pos, childenPos in self.enclosureTree.items():
#                 if self.rootId in childenPos:
#                     self.rootId = pos #pos is parent of rootId
#                     checkAgain = True # might still have parent, so we check again.
#         return self.enclosureTree, self.rootId


# class FindLeavesMixin:

#     def __init__(self, *args, **kwargs):
#         #TODO code can be a mixin too... CheckForPropertiesMixin lol
#         if not(hasattr(self, 'growTree') and callable(self.growTree)):# or not(hasattr(self, 'enclosureTree') and self.enclosureTree is not None and len(self.enclosureTree) > 0):
#             #should we import the mixin for the user?
#             setattr(self, 'growTree', GrowTreeMixin.growTree)

#     def findLeaves(self, listOfPoss, firstContainsSecond, getId):
#         if not(hasattr(self, 'enclosureTree') and self.enclosureTree is not None and len(self.enclosureTree) > 0):
#             self.enclosureTree = self.growTree(listOfPoss, firstContainsSecond, getId)
#         self.leaves = []
#         for ID, children in self.enclosureTree.items():
#             if len(children) == 0:
#                 self.leaves.append(ID)
#         return self.enclosureTree, self.leaves


# class LevelTreeMixing:

#     def __init__(self, *args, **kwargs):
#         """
#         if we have self.rootId
#             then we levelTreeWithRoot
#         if we have self.leaves
#             then we levelTreeWithLeaves
#         else:
#             we alert user to inherit either:
#             1. GrowTreeMixin & FindRootMixin
#             2. GrowTreeMixin & FindLeavesMixin
#         """
#         #TODO code can be a mixin too... CheckForPropertiesMixin lol
#         if not(hasattr(self, 'leaves') and self.leaves is not None and len(self.leaves) > 0) and not(hasattr(self, 'rootId') and self.rootId is not None and len(self.rootId) > 0):
#             #we make the choice for the user, FindRootMixin
#             setattr(self, 'findRoot', GrowTreeMixin.findRoot)
#             self.levelingType = 'RF'
#         if hasattr(self, 'leaves'): # so if there are leaves, then we will have enclosureTree
#             self.levelingType = 'L'
#         elif hasattr(self, 'rootId'): # so if there are rootId, then we will have enclosureTree
#             self.levelingType = 'R'
#         import pdb;pdb.set_trace()

#     def growLevelTree(self, listOfPoss, firstContainsSecond, getId):
#         if self.levelingType == 'L':
#             return self._levelTreeWithLeaves(listOfPoss, firstContainsSecond, getId)
#         elif self.levelingType == 'RF':
#             self.findRoot(listOfPoss, firstContainsSecond, getId)
#         return self._levelTreeWithRoot(listOfPoss, firstContainsSecond, getId)

#     def _levelTreeWithRoot(self, listOfPoss, firstContainsSecond, getId):
#         self.levelToIDs = {0:[self.rootId]}
#         self.idToLevel = {self.rootId:0}
#         queue = [{'id':self.rootId, 'level':0}]
#         while len(queue) > 0:
#             current = queue.pop()
#             for neighbourId in self.enclosureTree[current['id']]:
#                 neighbourLevel = current['level']+1
#                 queue.append({'id':neighbourId, 'level':neighbourLevel})
#                 #
#                 levelIDList = levelToIDs.get(neighbourLevel, [])
#                 levelIDList.append(neighbourId)
#                 #
#                 self.idToLevel[neighbourId] = neighbourLevel
#         return self.enclosureTree, self.levelToIDs, self.idToLevel

#     def _levelTreeWithLeaves(self, listOfPoss, firstContainsSecond, getId):
        # levelToIDs = {0:leaves}#{0:[self.rootId]}
        # idToLevel = dict(map(lambda leaf: (leaf, 0), leaves))#{self.rootId:0}
        # def getParent(leaf):
        #     for parent, children in enclosureTree.items():
        #         if leaf in children:
        #             return parent
        # queue = list(map(lambda leaf: (leaf, 0), leaves)) # leaf start at level 0
        # while len(queue) > 0:
        #     childLevel = queue.pop()
        #     parent = getParent(childLevel[0])
        #     #find parent in queue (we need to update the parent level)
        #     parentInQueue = None
        #     for possibleParent in queue:
        #         if possibleParent[0] == parent:
        #             parentInQueue = possibleParent
        #             break
        #     if parentInQueue is None: # parent not in queue yet
        #         newParentLevel = childLevel[1]+1
        #         parentInQueue = (parent, newParentLevel)
        #         existingChildren = []
        #     else:
        #         newParentLevel = max(childLevel[1]+1, parentInQueue[1])
        #         parentInQueue = (parent, newParentLevel) # childLevel+1 or existingparentlevel
        #         existingChildren = levelToIDs[parentInQueue[1]]
        #     idToLevel[parent] = newParentId
        #     existingChildren.append(childLevel)
        #     levelToIDs[newParentLevel] = existingChildren
        #     #return parent to queue
        #     queue.append(parentInQueue)
#         return self.enclosureTree, self.levelToIDs, self.idToLevel


# class EnclosureTreeLevel(GrowTreeMixin, FindLeavesMixin, LevelTreeMixing):
#     pass


class EnclosureTree: # can be used to schedule processes by level too... TODO
    #

    @classmethod
    def makeEnclosureTree(cls, listOfPoss, firstContainsSecond, getId):
        if len(listOfPoss) == 0:
            return {}
        enclosureTree = dict(map(lambda obj: (getId(obj), []),listOfPoss))
        for obj0 in listOfPoss:
            obj0ID = getId(obj0)
            for obj1 in listOfPoss:
                obj1ID = getId(obj1)
                if obj0ID == obj1ID:
                    continue 
                if firstContainsSecond(obj0, obj1):
                    existingChildren = enclosureTree.get(obj0ID, [])
                    if obj1ID not in existingChildren:
                        existingChildren.append(obj1ID)
                        enclosureTree[obj0ID] = existingChildren
                elif firstContainsSecond(obj1, obj0):
                    existingChildren = enclosureTree.get(obj1ID, [])
                    if obj0ID not in existingChildren:
                        existingChildren.append(obj0ID)
                        enclosureTree[obj1ID] = existingChildren
        #here, some parents may have their children's children, in their children list. TODO
        import copy
        cleanEnclosureTree = {}
        for objID, children in enclosureTree.items():
            addableChildren = set(copy.deepcopy(children))
            childrenToBeRemovedFromObjID = set()
            for child in children: 
                childChildren = enclosureTree[child]
                commonChildren = set(children).intersection(set(childChildren))#remove commonchildren
                childrenToBeRemovedFromObjID = childrenToBeRemovedFromObjID.union(commonChildren)
            leftOverChildren = addableChildren - childrenToBeRemovedFromObjID
            cleanEnclosureTree[objID] = list(leftOverChildren)
        return cleanEnclosureTree

    @classmethod
    def makeEnclosureTreeWithLeaves(cls, listOfPoss, firstContainsSecond, getId):
        enclosureTree = cls.makeEnclosureTree(listOfPoss, firstContainsSecond, getId)
        leaves = []
        for ID, children in enclosureTree.items():
            if len(children) == 0:
                leaves.append(ID)
        return enclosureTree, leaves


    @classmethod
    def makeEnclosureTreeWithRoots(cls, listOfPoss, firstContainsSecond, getId):
        """TODO make into MIXIN? REFACTOR, this code is repeated, in Equation._findAllDistributivePaths
        1. Get all the leavesA.
        2. get to ROME1 from a leave in leavesA, record ROME1
        3. DFS from ROME1 to leaves1=(all the leaves from this DFS)
        4. leavesA = leavesA - leaves1
        5. if len(leavesA) >0, then go to Step2, else TERMINATE
        
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
        enclosureTree, leaves = cls.makeEnclosureTreeWithLeaves(listOfPoss, firstContainsSecond, getId)
        tLeaves = set(leaves)
        roots = []
        while len(tLeaves) > 0:
            #all roads lead to rome (find root of tree) TODO might need to add cycle detection
            rootId = list(tLeaves)[0]#getId(list(tLeaves)[0])
            checkAgain = True
            while checkAgain: # keep going up
                checkAgain = False
                for pos, childenPos in enclosureTree.items():
                    if rootId in childenPos:
                        rootId = pos #pos is parent of rootId
                        checkAgain = True # might still have parent, so we check again.
            roots.append(rootId)
            #find all the leaves attached to this rootId
            leavesOfSubTree = set()
            stack = [rootId]
            while len(stack) > 0:
                currentNode = stack.pop()
                children = enclosureTree[currentNode]
                if len(children) == 0: # currentNode is a leaf
                    leavesOfSubTree.add(currentNode)
                else:
                    stack += children # push all the children to the stack
            tLeaves = set(tLeaves) - leavesOfSubTree
            #########
            # print(rootId, leavesOfSubTree)
            # print(tLeaves)
            # import pdb;pdb.set_trace()
            #########
        return roots, leaves, enclosureTree

    @classmethod
    def makeEnclosureTreeWithLevelRootLeaves(cls, listOfPoss, firstContainsSecond, getId):
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
        roots, leaves, enclosureTree = cls.makeEnclosureTreeWithRoots(listOfPoss, firstContainsSecond, getId)
        levelToIDs = {}#{0:[rootId]}
        idToLevel = {}#{rootId:0}
        queue = list(map(lambda root: {'id':root, 'level':0}, roots))#[{'id':rootId, 'level':0}]
        while len(queue) > 0:
            current = queue.pop()
            # print('current:', current)
            #
            levelIDList = levelToIDs.get(current['level'], [])
            levelIDList.append(current['id'])
            levelToIDs[current['level']] = levelIDList
            #
            idToLevel[current['id']] = current['level']
            for neighbourId in enclosureTree[current['id']]:
                neighbourLevel = current['level']+1
                queue.append({'id':neighbourId, 'level':neighbourLevel})
        return roots, leaves, enclosureTree, levelToIDs, idToLevel
