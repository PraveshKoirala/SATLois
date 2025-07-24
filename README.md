This repository contains code for the paper _An Application of SAT Solvers in Integer Programming Games_ which has been accepted into the 
The 28th International Conference on Theory and Applications of Satisfiability Testing (SAT 2025) conference.

> Integer programming games (IPGs) are a popular game-theoretic tool to model an array of games
where each player has a discrete strategy set. These games arise in important domains such as
economics, transportation, cybersecurity, etc., but solving them is non-trivial as it is known that
checking for the existence of pure Nash equilibria in an IPG is Sigma_p^2 -complete. Recent works have
proposed a class of relaxed solution concepts for IPGs called locally optimal integer solutions (LOIS)
and shown it to be an efficient alternative for pure Nash equilibria. While LOIS are significantly
simpler to compute, they still do not scale when solved using traditional mathematical solvers,
especially when high-quality solutions are desired. In this paper, we apply commercially available
SAT solvers to find LOIS in IPGs. We investigate efficient encodings for a cybersecurity game
and compare solution times when using SAT solvers vs mathematical program solvers. We also
investigate the application of SAT solvers in graph games using a graph interdiction example and
compare against the obtained LOI solutions against existing heuristics-based solutions. Our results
indicate that with appropriate encodings, large-scale IPGs can be solved much more efficiently
using SAT solvers. We also show that SAT solvers can be applied to graph games in conjunction
with LOIS for obtaining high-quality solutions. Our results emphasize the potential of SAT solvers
combined with LOIS to solve significant game theory problems.

_The code is in the process of cleanup/refactor and will be shortly updated._
