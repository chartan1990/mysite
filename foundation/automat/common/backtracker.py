class Backtracker:
    """
    Used in some tree traversal algorithms, allow selected path to be reconstructed.
    Holds the name of nodes, the neighbours of nodes, prev is the parent of this, id is this id in the whole tree
    Also used to hold the traversal itself in the memory of this process/thread, so that it can be re-made to a
    pythonic format (or not).

    TODO should it be a "container" class?

    :param label: name of this Node
    :type label: str
    :param neighbours: connections to this Backtracker
    :type neighbours: list[:class:`Backtracker`]
    :param argumentIdx: the position of this Node on its parent,which also denotes its position as an argument on
    its parent as a function
    :param prev: a BackTracker, denoting the previous link
    :type prev: :class: `BackTracer`
    :param id: id of this BackTracker, in the tree
    :type id: int
    """
    def __init__(self, label, neighbours, argumentIdx, prev, id):
        """
        Just getters and setter. Also the constructor.

        :param label: name of this Node
        :type label: str
        :param neighbours: connections to this Node, elements are tuples
            -item.0 : label
            -item.1 : id of the node in the tree
        :type neighbours: list[tuple[str, int]]
        :param argumentIdx: the position of this Node on its parent,which also denotes its position as an argument on
        its parent as a function
        :param prev: a BackTracker, denoting the previous link
        :type prev: :class: `BackTracer`
        :param id: id of this Node, in the tree
        :type id: int
        """
        self.label = label
        self.neighbours = neighbours
        self.argumentIdx = argumentIdx
        self.prev = prev
        self.id = id