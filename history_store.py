# -*- coding:utf-8 -*-

from collections import deque

class HistoryStore:
    def __init__(self, history_size):
        self.history_size = history_size
        self.store = deque()

    def push(self, element):
        """
        Stores the new |element|.

        The oldest element is popped from the store if |self.history_size| is exceeded.
        In this case, the popped element is returned.
        """

        self.store.append(element)

        popped = None

        if ( len(self.store) > self.history_size ):
            popped = self.store.popleft()

        return popped


    def flush(self):
        """
        Return all stored elements. (This removes the elements from the store.)
        """

        ret = self.store
        self.store = deque()

        return ret


    def size(self):
        return len( self.store )
    