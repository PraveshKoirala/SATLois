from __future__ import annotations

from collections import defaultdict
import queue

import networkx as nx

from z3_interdiction import Solver


class HeuristicSolver(Solver):
    def get_defense(self, scenario):
        raise NotImplementedError


class EigenCentrality(HeuristicSolver):
    def get_defense(self, scenario):
        scores = nx.eigenvector_centrality(scenario.g.nx_graph, tol=1e-3)
        return sorted(scores, key=scores.get, reverse=True)[: scenario.budget_D]


class ClosenessCentrality(HeuristicSolver):
    def get_defense(self, scenario):
        scores = nx.closeness_centrality(scenario.g.nx_graph)
        return sorted(scores, key=scores.get, reverse=True)[: scenario.budget_D]


class DegreeCentrality(HeuristicSolver):
    def get_defense(self, scenario):
        scores = nx.degree_centrality(scenario.g.nx_graph)
        return sorted(scores, key=scores.get, reverse=True)[: scenario.budget_D]


class BetweennessCentrality(HeuristicSolver):
    def get_defense(self, scenario):
        scores = nx.betweenness_centrality(scenario.g.nx_graph)
        return sorted(scores, key=scores.get, reverse=True)[: scenario.budget_D]


class ShapleyCentrality(HeuristicSolver):
    def get_defense(self, scenario):
        scores = self.shapley_betweenness(scenario.g.nx_graph)
        return sorted(range(scenario.g.V), key=lambda node: scores[node], reverse=True)[: scenario.budget_D]

    def shapley_betweenness(self, graph):
        vertices = list(graph.nodes())
        distance = defaultdict(int)
        path_count = defaultdict(int)
        delta = defaultdict(float)
        shapley = defaultdict(float)
        traversal = []
        bfs_queue = queue.Queue()
        infinity = 9999

        for source in vertices:
            predecessors = [[] for _ in vertices]
            for vertex in vertices:
                distance[(source, vertex)] = infinity
                path_count[(source, vertex)] = 0
            distance[(source, source)] = 1
            path_count[(source, source)] = 1
            bfs_queue.put(source)
            while not bfs_queue.empty():
                current = bfs_queue.get()
                traversal.append(current)
                for _, neighbor in list(graph.edges(current)):
                    if distance[(source, neighbor)] == infinity:
                        distance[(source, neighbor)] = distance[(source, current)] + 1
                        bfs_queue.put(neighbor)
                    if distance[(source, neighbor)] == distance[(source, current)] + 1:
                        path_count[(source, neighbor)] += path_count[(source, current)]
                        predecessors[neighbor].append(current)
            for vertex in vertices:
                delta[(source, vertex)] = 0.0
            while traversal:
                current = traversal.pop()
                for predecessor in predecessors[current]:
                    delta[(source, predecessor)] += (
                        path_count[(source, predecessor)] / path_count[(source, current)]
                    ) * (1 / distance[(source, current)] + delta[(source, current)])
                if current != source:
                    shapley[current] += delta[(source, current)] + (2 - delta[(source, current)]) / distance[(source, current)]

        for vertex in vertices:
            shapley[vertex] /= 2
        return {vertex: round(shapley[vertex], 5) for vertex in vertices}
