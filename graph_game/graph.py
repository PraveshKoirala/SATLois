from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
import random

import networkx


class Graph:
    def __init__(self, vertices: int):
        self.V = vertices
        self.E = []
        self._neighbors = None
        self._nx_graph = None

    @property
    def nx_graph(self):
        if self._nx_graph is None:
            graph = networkx.Graph()
            graph.add_nodes_from(range(self.V))
            graph.add_edges_from(self.E)
            self._nx_graph = graph
        return self._nx_graph

    @property
    def neighbors(self):
        if self._neighbors is None:
            self._neighbors = {
                i: {j for j in range(self.V) if (i, j) in self.E or (j, i) in self.E}
                for i in range(self.V)
            }
        return self._neighbors

    @lru_cache
    def get_cover(self, radius: int):
        cover = defaultdict(set)
        for vertex in range(self.V):
            cover[vertex].add(vertex)
        for vertex in range(self.V):
            frontier = {vertex}
            for _ in range(radius):
                for current in cover[vertex]:
                    frontier |= self.neighbors[current]
                cover[vertex] |= frontier
        return cover


class MST(Graph):
    def __init__(self, vertices: int):
        super().__init__(vertices)
        remaining = set(range(vertices))
        for i in range(vertices):
            target = random.choice(list(remaining - {i}))
            self.E.append((i, target))

    def __repr__(self) -> str:
        return "MST"


class Line(Graph):
    def __init__(self, vertices: int):
        super().__init__(vertices)
        for i in range(vertices - 1):
            self.E.append((i, i + 1))

    def __repr__(self) -> str:
        return "Line"


class Ring(Graph):
    def __init__(self, vertices: int):
        super().__init__(vertices)
        for i in range(vertices - 1):
            self.E.append((i, i + 1))
        self.E.append((vertices - 1, 0))

    def __repr__(self) -> str:
        return "Ring"


class Sparse30(Graph):
    def __init__(self, vertices: int):
        super().__init__(vertices)
        while len(self.E) < 30:
            left, right = sorted(random.choices(range(vertices), k=2))
            if (left, right) not in self.E:
                self.E.append((left, right))

    def __repr__(self) -> str:
        return "Sparse30"
